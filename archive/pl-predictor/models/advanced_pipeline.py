import pandas as pd
import numpy as np
import warnings
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.preprocessing import StandardScaler

# ML Algorithms
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings('ignore')

def calculate_elo(home_elo, away_elo, outcome, k=25):
    """
    Basic Elo rating calculation.
    outcome: 1 for Home Win, 0 for Draw, 2 for Away Win
    Returns: new_home_elo, new_away_elo
    """
    R_home = 10 ** (home_elo / 400)
    R_away = 10 ** (away_elo / 400)
    
    E_home = R_home / (R_home + R_away)
    E_away = R_away / (R_home + R_away)
    
    # Points based on outcome
    S_home = 1 if outcome == 1 else (0.5 if outcome == 0 else 0)
    S_away = 1 if outcome == 2 else (0.5 if outcome == 0 else 0)
    
    # Update Elo, providing a slight Home Field Advantage (HFA) assumed inside expected if needed
    new_home = home_elo + k * (S_home - E_home)
    new_away = away_elo + k * (S_away - E_away)
    
    return new_home, new_away

def parse_base_data(matches_2324_path, matches_2425_path):
    print("Parsing base matches...")
    # 23-24 Data
    df_2324 = pd.read_csv(matches_2324_path)
    scores = df_2324['score'].str.split('–', expand=True)
    df_2324['home_goals'] = pd.to_numeric(scores[0], errors='coerce')
    df_2324['away_goals'] = pd.to_numeric(scores[1], errors='coerce')
    df_2324['date'] = pd.to_datetime(df_2324['date'])
    df_2324['season'] = '2023-2024'
    # Base columns
    df_2324 = df_2324[['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'season']]
    
    # 24-25 Data
    df_2425 = pd.read_csv(matches_2425_path)
    scores = df_2425['score'].str.split('–', expand=True)
    df_2425['home_goals'] = pd.to_numeric(scores[0], errors='coerce')
    df_2425['away_goals'] = pd.to_numeric(scores[1], errors='coerce')
    df_2425['date'] = pd.to_datetime(df_2425['date'])
    df_2425['home_team'] = df_2425['home_team'].str.replace('Utd', 'United').str.replace("Nott'ham", "Nottingham")
    df_2425['away_team'] = df_2425['away_team'].str.replace('Utd', 'United').str.replace("Nott'ham", "Nottingham")
    df_2425['season'] = '2024-2025'
    
    # Keep baseline and available xG for 24-25
    df_2425_core = df_2425[['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'season']]
    
    df = pd.concat([df_2324, df_2425_core]).sort_values(by='date').reset_index(drop=True)
    
    # Set Outcomes (Target)
    cond_h = df['home_goals'] > df['away_goals']
    cond_a = df['home_goals'] < df['away_goals']
    cond_d = df['home_goals'] == df['away_goals']
    df['outcome'] = np.select([cond_h, cond_d, cond_a], [1, 0, 2], default=np.nan)
    df = df.dropna(subset=['outcome', 'home_goals', 'away_goals'])
    
    return df

def integrate_static_team_stats(df, stats_paths):
    """
    Joins season-based static stats. 
    Warning: If stats are from the ENTIRE season 24-25, they leak into early matches. 
    However, using them as generic "Team Strength Priers" can be useful for baseline.
    """
    print("Integrating static metrics...")
    # Load Misc (Cards/Fouls)
    misc = pd.read_csv(stats_paths['misc']).rename(columns={'Squad':'home_team'})
    misc_features = ['Performance_CrdY', 'Performance_CrdR', 'Performance_Fls', 'Performance_Int']
    
    # Load Shooting
    shooting = pd.read_csv(stats_paths['shooting']).rename(columns={'Squad':'home_team'})
    shooting_features = ['Standard_SoT/90', 'Standard_G/Sh']
    
    # Load Keepers
    keeper = pd.read_csv(stats_paths['keeper']).rename(columns={'Squad':'home_team'})
    keeper_features = ['Performance_Save%']
    
    team_strengths = misc[['home_team'] + misc_features].copy()
    team_strengths = team_strengths.merge(shooting[['home_team'] + shooting_features], on='home_team', how='left')
    team_strengths = team_strengths.merge(keeper[['home_team'] + keeper_features], on='home_team', how='left')
    
    # Fill NAs
    team_strengths = team_strengths.fillna(team_strengths.mean(numeric_only=True))
    
    # Add Home Stats
    df = df.merge(team_strengths, on='home_team', how='left').rename(columns={c: f"home_static_{c}" for c in team_strengths.columns if c != 'home_team'})
    
    # Add Away Stats
    team_strengths_away = team_strengths.rename(columns={'home_team':'away_team'})
    df = df.merge(team_strengths_away, on='away_team', how='left').rename(columns={c: f"away_static_{c}" for c in team_strengths_away.columns if c != 'away_team'})
    
    # Impute for teams from lower divisions lacking stats
    df = df.fillna(0)
    
    return df

def build_rolling_features(df, window=5):
    print("Building dynamic rolling features and Elo...")
    # Elo init
    elo_dict = {}
    df['home_elo'] = 1500
    df['away_elo'] = 1500
    
    # Rolling forms
    history = {}
    
    df['home_roll_gf'] = 0.0
    df['home_roll_ga'] = 0.0
    df['home_roll_pts'] = 0.0
    df['away_roll_gf'] = 0.0
    df['away_roll_ga'] = 0.0
    df['away_roll_pts'] = 0.0
    
    for i, row in df.iterrows():
        ht = row['home_team']
        at = row['away_team']
        
        # Init Tracking
        if ht not in elo_dict: elo_dict[ht] = 1500
        if at not in elo_dict: elo_dict[at] = 1500
        if ht not in history: history[ht] = []
        if at not in history: history[at] = []
            
        # Write Pre-Match Metrics
        df.at[i, 'home_elo'] = elo_dict[ht]
        df.at[i, 'away_elo'] = elo_dict[at]
        
        h_rec = history[ht][-window:]
        a_rec = history[at][-window:]
        
        if len(h_rec) > 0:
            df.at[i, 'home_roll_gf'] = sum([x['gf'] for x in h_rec]) / len(h_rec)
            df.at[i, 'home_roll_ga'] = sum([x['ga'] for x in h_rec]) / len(h_rec)
            df.at[i, 'home_roll_pts'] = sum([x['pts'] for x in h_rec])
            
        if len(a_rec) > 0:
            df.at[i, 'away_roll_gf'] = sum([x['gf'] for x in a_rec]) / len(a_rec)
            df.at[i, 'away_roll_ga'] = sum([x['ga'] for x in a_rec]) / len(a_rec)
            df.at[i, 'away_roll_pts'] = sum([x['pts'] for x in a_rec])
            
        # Update Tracking post-match
        n_elo_h, n_elo_a = calculate_elo(elo_dict[ht], elo_dict[at], row['outcome'])
        elo_dict[ht] = n_elo_h
        elo_dict[at] = n_elo_a
        
        h_pts = 3 if row['outcome'] == 1 else (1 if row['outcome'] == 0 else 0)
        a_pts = 3 if row['outcome'] == 2 else (1 if row['outcome'] == 0 else 0)
        
        history[ht].append({'gf': row['home_goals'], 'ga': row['away_goals'], 'pts': h_pts})
        history[at].append({'gf': row['away_goals'], 'ga': row['home_goals'], 'pts': a_pts})
        
    return df

def train_and_eval_suite(df):
    print("Preparing 5 Advanced Algorithms...")
    
    # Feature Selection (Dropping leakage features like actual goals/outcome)
    drop_cols = ['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'outcome', 'season']
    features = [c for c in df.columns if c not in drop_cols]
    
    # We will split temporally: 23/24 is Train, 24/25 is Test
    # Drop first 5 weeks of 23/24 to let rolling averages build
    train = df[df['season'] == '2023-2024'].iloc[50:] 
    test = df[df['season'] == '2024-2025']
    
    X_train = train[features]
    y_train = train['outcome']
    X_test = test[features]
    y_test = test['outcome']
    
    # Scale Data (Required for NN and LR)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    
    # Advanced Tuning setup for top performers
    param_grid_lr = {
        'C': [0.01, 0.1, 1, 10, 100],
        'penalty': ['l2'],
        'solver': ['lbfgs', 'liblinear']
    }
    
    param_grid_xgb = {
        'max_depth': [3, 4, 5],
        'learning_rate': [0.01, 0.05, 0.1],
        'n_estimators': [100, 200]
    }
    
    print("Running GridSearch on Logistic Regression...")
    gs_lr = GridSearchCV(LogisticRegression(max_iter=1000, random_state=42), param_grid_lr, cv=5, scoring='accuracy')
    gs_lr.fit(X_train_s, y_train)
    best_lr = gs_lr.best_estimator_
    
    print("Running GridSearch on XGBoost...")
    gs_xgb = GridSearchCV(xgb.XGBClassifier(random_state=42), param_grid_xgb, cv=5, scoring='accuracy')
    gs_xgb.fit(X_train, y_train)
    best_xgb = gs_xgb.best_estimator_
    
    models = {
        "Logistic Regression (Tuned)": best_lr,
        "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_split=5, random_state=42),
        "XGBoost (Tuned)": best_xgb,
        "LightGBM": lgb.LGBMClassifier(n_estimators=200, learning_rate=0.03, max_depth=4, random_state=42, verbose=-1),
        "Neural Network (MLP)": MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=1000, random_state=42, early_stopping=True, learning_rate_init=0.001)
    }
    
    results = {}
    with open('advanced_metrics.txt', 'w', encoding='utf-8') as f:
        f.write(f"Advanced Models Benchmark - Test Set Size: {len(X_test)}\n\n")
        
        for name, clf in models.items():
            print(f"Training {name}...")
            
            x_tr = X_train_s if ("Logistic" in name or "Neural" in name) else X_train
            x_te = X_test_s if ("Logistic" in name or "Neural" in name) else X_test
            
            if "Tuned" not in name:
                clf.fit(x_tr, y_train)
            preds = clf.predict(x_te)
            
            acc = accuracy_score(y_test, preds)
            prec = precision_score(y_test, preds, average='macro', zero_division=0)
            rec = recall_score(y_test, preds, average='macro')
            
            results[name] = acc
            
            f.write(f"[{name}]\n")
            f.write(f"Accuracy:  {acc:.4f}\n")
            f.write(f"Precision (Macro): {prec:.4f}\n")
            f.write(f"Recall (Macro):    {rec:.4f}\n")
            f.write("Report:\n")
            f.write(classification_report(y_test, preds, target_names=['Draw (0)', 'Home (1)', 'Away (2)'], zero_division=0))
            f.write("\n" + "="*40 + "\n\n")

    return results

def main():
    paths = {
        'm_2324': r"c:\Users\PC\DataScience\archive\pl-scraper\data\processed\2023\matches.csv",
        'm_2425': r"c:\Users\PC\DataScience\archive\pl_24-25_matches_clean.csv",
        'misc': r"c:\Users\PC\DataScience\archive\overwiev__stats_squads_misc_for.csv",
        'shooting': r"c:\Users\PC\DataScience\archive\overwiev__stats_squads_shooting_for.csv",
        'keeper': r"c:\Users\PC\DataScience\archive\overwiev__stats_squads_keeper_for.csv"
    }
    
    df = parse_base_data(paths['m_2324'], paths['m_2425'])
    df = build_rolling_features(df, window=5)
    df = integrate_static_team_stats(df, paths)
    
    train_and_eval_suite(df)
    print("Advanced Pipeline complete. Results written to advanced_metrics.txt.")

if __name__ == '__main__':
    main()
