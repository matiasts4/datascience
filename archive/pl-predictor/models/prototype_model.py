import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

def load_and_prep_2324(filepath):
    print(f"Loading 2023-2024 data from {filepath}")
    df = pd.read_csv(filepath)
    # Parse scores
    scores = df['score'].str.split('–', expand=True)
    df['home_goals'] = pd.to_numeric(scores[0], errors='coerce')
    df['away_goals'] = pd.to_numeric(scores[1], errors='coerce')
    
    # Standardize dates
    df['date'] = pd.to_datetime(df['date'])
    
    # Outcome: 1 for Home Win, 0 for Draw, 2 for Away Win
    conditions = [
        (df['home_goals'] > df['away_goals']),
        (df['home_goals'] == df['away_goals']),
        (df['home_goals'] < df['away_goals'])
    ]
    choices = [1, 0, 2]
    df['outcome'] = np.select(conditions, choices, default=np.nan)
    
    # Keep only necessary columns
    df = df[['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'outcome']]
    df['season'] = '2023-2024'
    return df.dropna(subset=['outcome'])

def load_and_prep_2425(filepath):
    print(f"Loading 2024-2025 data from {filepath}")
    df = pd.read_csv(filepath)
    # Parse scores
    scores = df['score'].str.split('–', expand=True)
    df['home_goals'] = pd.to_numeric(scores[0], errors='coerce')
    df['away_goals'] = pd.to_numeric(scores[1], errors='coerce')
    
    # Standardize dates
    df['date'] = pd.to_datetime(df['date'])
    
    # Outcome: 1 for Home Win, 0 for Draw, 2 for Away Win
    conditions = [
        (df['home_goals'] > df['away_goals']),
        (df['home_goals'] == df['away_goals']),
        (df['home_goals'] < df['away_goals'])
    ]
    choices = [1, 0, 2]
    df['outcome'] = np.select(conditions, choices, default=np.nan)
    
    # Standardize team names slightly better
    df['home_team'] = df['home_team'].str.replace('Utd', 'United')
    df['away_team'] = df['away_team'].str.replace('Utd', 'United')
    df['home_team'] = df['home_team'].str.replace("Nott'ham", "Nottingham")
    df['away_team'] = df['away_team'].str.replace("Nott'ham", "Nottingham")
    
    # Keep only necessary columns
    df = df[['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'outcome']]
    df['season'] = '2024-2025'
    return df.dropna(subset=['outcome'])

def calculate_recent_stats(df, matches_window=5):
    """
    Calculate recent form features based on a rolling window.
    """
    print("Calculating rolling features...")
    df = df.sort_values(by='date')
    
    # Initialize new columns
    df['home_recent_goals_scored'] = 0.0
    df['home_recent_goals_conceded'] = 0.0
    df['away_recent_goals_scored'] = 0.0
    df['away_recent_goals_conceded'] = 0.0
    
    # Simple form tracking dictionary per team
    team_history = {}
    
    for i, row in df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        
        # Initialize team history if not exists
        if home_team not in team_history:
            team_history[home_team] = []
        if away_team not in team_history:
            team_history[away_team] = []
            
        # Get recent matches
        home_recent = team_history[home_team][-matches_window:]
        away_recent = team_history[away_team][-matches_window:]
        
        # Calculate sums
        if len(home_recent) > 0:
            df.at[i, 'home_recent_goals_scored'] = sum([m['scored'] for m in home_recent]) / len(home_recent)
            df.at[i, 'home_recent_goals_conceded'] = sum([m['conceded'] for m in home_recent]) / len(home_recent)
            
        if len(away_recent) > 0:
            df.at[i, 'away_recent_goals_scored'] = sum([m['scored'] for m in away_recent]) / len(away_recent)
            df.at[i, 'away_recent_goals_conceded'] = sum([m['conceded'] for m in away_recent]) / len(away_recent)
            
        # Update histories
        team_history[home_team].append({'scored': row['home_goals'], 'conceded': row['away_goals']})
        team_history[away_team].append({'scored': row['away_goals'], 'conceded': row['home_goals']})
    
    return df

def main():
    path_2324 = r"c:\Users\PC\DataScience\archive\pl-scraper\data\processed\2023\matches.csv"
    path_2425 = r"c:\Users\PC\DataScience\archive\pl_24-25_matches_clean.csv"
    
    df_2324 = load_and_prep_2324(path_2324)
    df_2425 = load_and_prep_2425(path_2425)
    
    print(f"Loaded {len(df_2324)} matches from 23/24 season")
    print(f"Loaded {len(df_2425)} matches from 24/25 season")
    
    # Combine datasets for temporal sorting and feature generation
    all_data = pd.concat([df_2324, df_2425]).reset_index(drop=True)
    
    # Remove future games missing scores (if they somehow sneaked through dropna but generally good to check)
    all_data = all_data.dropna(subset=['outcome'])
    
    # Feature Engineering
    all_data = calculate_recent_stats(all_data)
    
    # Categorical encoding
    all_teams = set(all_data['home_team'].unique()) | set(all_data['away_team'].unique())
    team_mapping = {team: idx for idx, team in enumerate(all_teams)}
    
    all_data['home_team_encoded'] = all_data['home_team'].map(team_mapping)
    all_data['away_team_encoded'] = all_data['away_team'].map(team_mapping)
    
    # Define features and target
    features = [
        'home_team_encoded', 'away_team_encoded',
        'home_recent_goals_scored', 'home_recent_goals_conceded',
        'away_recent_goals_scored', 'away_recent_goals_conceded'
    ]
    target = 'outcome'
    
    # Split back into seasons for train/test
    train_data = all_data[all_data['season'] == '2023-2024']
    # Removing first few games of the season from training where moving average is zero
    train_data = train_data.dropna()
    
    test_data = all_data[all_data['season'] == '2024-2025']
    
    X_train = train_data[features]
    y_train = train_data[target]
    
    X_test = test_data[features]
    y_test = test_data[target]
    
    with open('model_metrics.txt', 'w', encoding='utf-8') as f:
        f.write("--- Training Models ---\n\n")
        
        # Baseline 1: Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)
        rf_preds = rf_model.predict(X_test)
        
        f.write("[Random Forest Classifier]\n")
        f.write(f"Accuracy: {accuracy_score(y_test, rf_preds):.4f}\n")
        f.write("Classification Report:\n")
        f.write(classification_report(y_test, rf_preds, target_names=['Draw (0)', 'Home Win (1)', 'Away Win (2)']))
        
        # Baseline 2: Logistic Regression
        lr_model = LogisticRegression(max_iter=1000, random_state=42)
        lr_model.fit(X_train, y_train)
        lr_preds = lr_model.predict(X_test)
        
        f.write("\n\n[Logistic Regression]\n")
        f.write(f"Accuracy: {accuracy_score(y_test, lr_preds):.4f}\n")
        f.write("Classification Report:\n")
        f.write(classification_report(y_test, lr_preds, target_names=['Draw (0)', 'Home Win (1)', 'Away Win (2)']))
        
        # Baseline 3: Always predict Home Win
        baseline_preds = np.ones_like(y_test)
        f.write("\n\n[Naive Baseline (Always Home Win)]\n")
        f.write(f"Accuracy: {accuracy_score(y_test, baseline_preds):.4f}\n")
        
    print("\nPrototype complete. Data has been successfully joined and tested.")

if __name__ == '__main__':
    main()
