import pandas as pd
import numpy as np
import warnings
import optuna
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# ML Algorithms
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

def calculate_elo(home_elo, away_elo, outcome, home_advantage=50, k=30):
    """
    Elo rating calculation with Home Field Advantage weight.
    """
    R_home = 10 ** ((home_elo + home_advantage) / 400)
    R_away = 10 ** (away_elo / 400)
    
    E_home = R_home / (R_home + R_away)
    E_away = R_away / (R_home + R_away)
    
    S_home = 1 if outcome == 1 else (0.5 if outcome == 0 else 0)
    S_away = 1 if outcome == 2 else (0.5 if outcome == 0 else 0)
    
    new_home = home_elo + k * (S_home - E_home)
    new_away = away_elo + k * (S_away - E_away)
    
    return new_home, new_away

def parse_base_data(historical_paths):
    print("Parsing base matches from all available seasons...")
    df_list = []
    
    # Process all historical data (unified scraper/kaggle format)
    for path in historical_paths:
        try:
            df_hist = pd.read_csv(path)
            scores = df_hist['score'].str.split('–', expand=True)
            df_hist['home_goals'] = pd.to_numeric(scores[0], errors='coerce')
            df_hist['away_goals'] = pd.to_numeric(scores[1], errors='coerce')
            df_hist['date'] = pd.to_datetime(df_hist['date'])
            df_hist['season'] = df_hist['season'].apply(lambda x: f"20{str(x)[:2]}-20{str(x)[2:]}")
            df_hist_core = df_hist[['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'season']]
            df_list.append(df_hist_core)
        except Exception as e:
            print(f"Skipping {path}: {e}")
    
    # Combine everything
    df = pd.concat(df_list).sort_values(by='date').reset_index(drop=True)
    
    cond_h = df['home_goals'] > df['away_goals']
    cond_a = df['home_goals'] < df['away_goals']
    cond_d = df['home_goals'] == df['away_goals']
    df['outcome'] = np.select([cond_h, cond_d, cond_a], [1, 0, 2], default=np.nan)
    df = df.dropna(subset=['outcome', 'home_goals', 'away_goals'])
    
    return df

def build_advanced_features(df, windows=[3, 5, 10]):
    print(f"Building rolling forms ({windows}), Elo, GD, Streaks and Days of Rest...")
    elo_dict = {}
    history = {}
    last_played = {} # Track last match date for fatigue
    
    df['home_elo'] = 1500
    df['away_elo'] = 1500
    df['home_rest_days'] = 14 # Default 2 weeks if start of season
    df['away_rest_days'] = 14
    
    # Initialize metric columns
    metrics = ['gf', 'ga', 'pts', 'gd', 'win_streak']
    for pfx in ['home', 'away']:
        for w in windows:
            for m in metrics:
                df[f'{pfx}_roll_{w}_{m}'] = 0.0
            
    for i, row in df.iterrows():
        ht = row['home_team']
        at = row['away_team']
        current_date = row['date']
        
        # Init Tracking
        if ht not in elo_dict: elo_dict[ht] = 1500
        if at not in elo_dict: elo_dict[at] = 1500
        if ht not in history: history[ht] = []
        if at not in history: history[at] = []
            
        # Write Pre-Match Metrics
        df.at[i, 'home_elo'] = elo_dict[ht]
        df.at[i, 'away_elo'] = elo_dict[at]
        
        # Calculate Rest Days
        if ht in last_played:
            df.at[i, 'home_rest_days'] = (current_date - last_played[ht]).days
        if at in last_played:
            df.at[i, 'away_rest_days'] = (current_date - last_played[at]).days
            
        # Calculate Rolling for all windows
        for w in windows:
            h_rec = history[ht][-w:]
            a_rec = history[at][-w:]
            
            if len(h_rec) > 0:
                df.at[i, f'home_roll_{w}_gf'] = sum([x['gf'] for x in h_rec]) / len(h_rec)
                df.at[i, f'home_roll_{w}_ga'] = sum([x['ga'] for x in h_rec]) / len(h_rec)
                df.at[i, f'home_roll_{w}_pts'] = sum([x['pts'] for x in h_rec])
                df.at[i, f'home_roll_{w}_gd'] = sum([x['gd'] for x in h_rec])
                df.at[i, f'home_roll_{w}_win_streak'] = sum([1 for x in h_rec if x['pts'] == 3])
                
            if len(a_rec) > 0:
                df.at[i, f'away_roll_{w}_gf'] = sum([x['gf'] for x in a_rec]) / len(a_rec)
                df.at[i, f'away_roll_{w}_ga'] = sum([x['ga'] for x in a_rec]) / len(a_rec)
                df.at[i, f'away_roll_{w}_pts'] = sum([x['pts'] for x in a_rec])
                df.at[i, f'away_roll_{w}_gd'] = sum([x['gd'] for x in a_rec])
                df.at[i, f'away_roll_{w}_win_streak'] = sum([1 for x in a_rec if x['pts'] == 3])
                
        # Update Tracking post-match
        n_elo_h, n_elo_a = calculate_elo(elo_dict[ht], elo_dict[at], row['outcome'])
        elo_dict[ht] = n_elo_h
        elo_dict[at] = n_elo_a
        last_played[ht] = current_date
        last_played[at] = current_date
        
        h_pts = 3 if row['outcome'] == 1 else (1 if row['outcome'] == 0 else 0)
        a_pts = 3 if row['outcome'] == 2 else (1 if row['outcome'] == 0 else 0)
        h_gd = row['home_goals'] - row['away_goals']
        a_gd = row['away_goals'] - row['home_goals']
        
        history[ht].append({'gf': row['home_goals'], 'ga': row['away_goals'], 'pts': h_pts, 'gd': h_gd})
        history[at].append({'gf': row['away_goals'], 'ga': row['home_goals'], 'pts': a_pts, 'gd': a_gd})
        
    # Cap rest days to avoid early season outliers skewing
    df['home_rest_days'] = df['home_rest_days'].clip(upper=14)
    df['away_rest_days'] = df['away_rest_days'].clip(upper=14)
    df['rest_diff'] = df['home_rest_days'] - df['away_rest_days']
    
    return df

def integrate_static_team_stats(df, stats_paths):
    print("Integrating static metrics...")
    misc = pd.read_csv(stats_paths['misc']).rename(columns={'Squad':'home_team'})
    misc_features = ['Performance_CrdY', 'Performance_CrdR', 'Performance_Fls', 'Performance_Int']
    
    shooting = pd.read_csv(stats_paths['shooting']).rename(columns={'Squad':'home_team'})
    shooting_features = ['Standard_SoT/90', 'Standard_G/Sh']
    
    team_strengths = misc[['home_team'] + misc_features].copy()
    team_strengths = team_strengths.merge(shooting[['home_team'] + shooting_features], on='home_team', how='left')
    team_strengths = team_strengths.fillna(team_strengths.mean(numeric_only=True))
    
    df = df.merge(team_strengths, on='home_team', how='left').rename(columns={c: f"home_static_{c}" for c in team_strengths.columns if c != 'home_team'})
    team_strengths_away = team_strengths.rename(columns={'home_team':'away_team'})
    df = df.merge(team_strengths_away, on='away_team', how='left').rename(columns={c: f"away_static_{c}" for c in team_strengths_away.columns if c != 'away_team'})
    
    df = df.fillna(0)
    return df

def optimize_xgb(X_train, y_train):
    print("Running Optuna Bayesian Search for XGBoost...")
    def objective(trial):
        param = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 250),
            'max_depth': trial.suggest_int('max_depth', 2, 7),
            'learning_rate': trial.suggest_float('learning_rate', 1e-3, 0.1, log=True),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 5),
            'random_state': 42
        }
        model = xgb.XGBClassifier(**param)
        score = cross_val_score(model, X_train, y_train, cv=3, scoring='accuracy').mean()
        return score

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=50) # Increased search depth for 8-season run
    best_xgb = xgb.XGBClassifier(**study.best_params, random_state=42)
    return best_xgb

def run_ultimate_suite(df):
    print("Preparing Data and Balancing Classes...")
    drop_cols = ['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'outcome', 'season']
    features = [c for c in df.columns if c not in drop_cols]
    
    # Combine all data and split chronologically (80% Train, 20% Test)
    # We still drop the first 50 games of the earliest season to let rolling averages build
    df_clean = df.iloc[50:].reset_index(drop=True)
    
    split_idx = int(len(df_clean) * 0.8)
    train = df_clean.iloc[:split_idx]
    test = df_clean.iloc[split_idx:]
    
    X_train = train[features]
    y_train = train['outcome']
    X_test = test[features]
    y_test = test['outcome']
    
    # Calculate Time Decay for Sample Weights (More recent = higher weight)
    # We use the index or date. Index is already chronological.
    max_idx = len(train)
    # Exponential decay: e^(rate * (normalized_time - 1))
    # We want oldest game to have ~0.3 weight, newest to have 1.0
    decay_rate = 1.2
    time_weights = np.exp(decay_rate * ((train.index / max_idx) - 1.0))
    
    input_shape = X_train.shape[1]
    
    # SMOTE to handle the Draw (0) scarcity
    # Warning: SMOTE doesn't natively return sample_weights for synthetic data.
    # We'll map weights to the original data, and give synthetic draws a standard high weight.
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    # Create matching sample_weights array for resampled data
    sample_weights_resampled = np.zeros(len(y_train_resampled))
    sample_weights_resampled[:len(train)] = time_weights # Original samples keep their time weight
    # Synthetic samples (drawn to balance classes) get the mean weight of the top 20% most recent games
    recent_mean_weight = np.mean(time_weights[-int(len(train)*0.2):])
    sample_weights_resampled[len(train):] = recent_mean_weight
    
    # Scaling for Linear models
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train_resampled)
    X_test_s = scaler.transform(X_test)
    
    # Bayesian Tuning for XGBoost
    best_xgb = optimize_xgb(X_train_resampled, y_train_resampled)
    
    models = {
        "Logistic Regression (Balanced Weights)": LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42),
        "Random Forest (SMOTE)": RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42),
        "XGBoost (Optuna Tuned + SMOTE)": best_xgb,
    }
    
    results = {}
    with open(r'c:\Users\PC\DataScience\archive\pl-predictor\output\ultimate_metrics.txt', 'w', encoding='utf-8') as f:
        f.write(f"Ultimate Optimization Benchmark - Test Size: {len(X_test)}\n\n")
        
        for name, clf in models.items():
            print(f"Training {name} with Time Decay Weights...")
            
            x_tr = X_train_s if "Logistic" in name else X_train_resampled
            x_te = X_test_s if "Logistic" in name else X_test
            y_tr = y_train if "Logistic" in name else y_train_resampled # LR uses internal balanced weights, trees use SMOTE
            w_tr = time_weights if "Logistic" in name else sample_weights_resampled
            
            if "Logistic" in name: x_tr = scaler.fit_transform(X_train) 
            
            # Fit with sample weights
            clf.fit(x_tr, y_tr, sample_weight=w_tr)
            preds = clf.predict(x_te)
            
            acc = accuracy_score(y_test, preds)
            f.write(f"[{name}]\n")
            f.write(f"Accuracy:  {acc:.4f}\n")
            f.write("Report:\n")
            f.write(classification_report(y_test, preds, target_names=['Draw (0)', 'Home (1)', 'Away (2)'], zero_division=0))
            f.write("\n" + "="*40 + "\n\n")
            
            # Feature Importance for Trees
            if "XGB" in name:
                f.write("Top 5 Feature Importances:\n")
                importances = clf.feature_importances_
                indices = np.argsort(importances)[::-1][:5]
                for i in indices:
                    f.write(f"{features[i]}: {importances[i]:.4f}\n")
                f.write("\n")

def main():
    base = r"c:\Users\PC\DataScience\archive\pl-predictor"
    historical_paths = [
        rf"{base}\data\historical\2017\matches.csv",
        rf"{base}\data\historical\2018\matches.csv",
        rf"{base}\data\historical\2019\matches.csv",
        rf"{base}\data\historical\2020\matches.csv",
        rf"{base}\data\historical\2021\matches.csv",
        rf"{base}\data\historical\2022\matches.csv",
        rf"{base}\data\historical\2023\matches.csv",
        rf"{base}\data\historical\2024\matches.csv",   # 2024-25 season (converted)
    ]
    
    paths = {
        'misc':     rf"{base}\data\stats\overwiev__stats_squads_misc_for.csv",
        'shooting': rf"{base}\data\stats\overwiev__stats_squads_shooting_for.csv",
        'keeper':   rf"{base}\data\stats\overwiev__stats_squads_keeper_for.csv"
    }
    
    df = parse_base_data(historical_paths)
    df = build_advanced_features(df, windows=[3, 5, 10])
    # df = integrate_static_team_stats(df, paths) # Disabled for multi-season historical run
    
    run_ultimate_suite(df)
    print("Ultimate Pipeline complete. Results written to output/ultimate_metrics.txt.")

if __name__ == '__main__':
    main()
