import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, roc_auc_score

# Define paths
BASE_DIR = r"c:\Users\PC\DataScience\archive\pl-predictor"
FEATURES_PATH = os.path.join(BASE_DIR, "data", "historical", "all_match_features_v2.csv")

def evaluate_models(X_train, X_test, y_train, y_test, target_name):
    print(f"\n{'='*50}")
    print(f"EVALUATING MODELS FOR TARGET: {target_name}")
    print(f"{'='*50}")
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, solver='lbfgs', penalty='l2', C=0.01, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, min_samples_split=10, min_samples_leaf=1, max_depth=5, random_state=42),
        "HistGradientBoosting": HistGradientBoostingClassifier(learning_rate=0.01, max_iter=100, max_depth=10, l2_regularization=10.0, random_state=42),
        "AdaBoost": AdaBoostClassifier(random_state=42),
        "Neural Network (MLP)": MLPClassifier(max_iter=500, random_state=42),
        "Naive Bayes": GaussianNB()
    }
    
    best_model_name = None
    best_accuracy = 0
    results = []
    
    is_multiclass = len(pd.unique(y_train)) > 2
    
    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        preds = model.predict(X_test_scaled)
        acc = accuracy_score(y_test, preds)
        
        auc = 0.0
        if not is_multiclass:
            try:
                auc = roc_auc_score(y_test, model.predict_proba(X_test_scaled)[:, 1])
            except:
                pass
            
        results.append({"Model": name, "Accuracy": acc, "ROC_AUC": auc if not is_multiclass else "N/A"})
            
        if acc > best_accuracy:
            best_accuracy = acc
            best_model_name = name
            
    results_df = pd.DataFrame(results).sort_values(by="Accuracy", ascending=False).reset_index(drop=True)
    print(results_df.to_string(index=False))
    print(f"\n🏆 Best model for {target_name}: {best_model_name} (Accuracy: {best_accuracy:.4f})")
    
def train_and_test():
    print("Loading engineered features for ALL seasons (with DEEP features)...")
    if not os.path.exists(FEATURES_PATH):
        print(f"Error: Could not find {FEATURES_PATH}. Run build_deep_features.py first.")
        return
        
    df = pd.read_csv(FEATURES_PATH)
    df = df.dropna()
    print(f"Dataset shape after dropping NaNs: {df.shape[0]} matches")
    
    # Define Targets
    df['target_btts'] = df['btts'].astype(int)
    df['target_over_4_5_cards'] = (df['total_cards'] > 4.5).astype(int)
    df['target_over_2_5_goals'] = (df['total_goals'] > 2.5).astype(int)
    df['target_1x2'] = df['result_1x2'].astype(int)
    
    # New Targets
    df['total_fouls'] = df['home_match_fouls'] + df['away_match_fouls']
    df['target_over_22_5_fouls'] = (df['total_fouls'] > 22.5).astype(int)
    df['target_dc_1X'] = (df['result_1x2'] >= 1).astype(int)
    df['target_dc_X2'] = (df['result_1x2'] <= 1).astype(int)
    df['target_home_over_0_5'] = (df['home_goals'] > 0.5).astype(int)
    df['target_away_over_0_5'] = (df['away_goals'] > 0.5).astype(int)
    
    # Define Advanced Deep Features
    features = [
        'home_elo', 'away_elo',
        'h_l5_pts', 'h_l5_sh', 'h_l5_sot', 'h_l5_sot_c', 'h_l5_gf', 'h_l5_ga', 'h_l5_fls',
        'a_l5_pts', 'a_l5_sh', 'a_l5_sot', 'a_l5_sot_c', 'a_l5_gf', 'a_l5_ga', 'a_l5_fls',
        'referee_avg_cards_history'
    ]
    
    X = df[features]
    
    targets = {
        "1X2 (Match Winner)": 'target_1x2',
        "Double Chance 1X (Home or Draw)": 'target_dc_1X',
        "Double Chance X2 (Away or Draw)": 'target_dc_X2',
        "Over 2.5 Goals": 'target_over_2_5_goals',
        "BTTS (Both Teams To Score)": 'target_btts',
        "Home Team Over 0.5 Goals": 'target_home_over_0_5',
        "Away Team Over 0.5 Goals": 'target_away_over_0_5',
        "Over 4.5 Cards": 'target_over_4_5_cards',
        "Over 22.5 Fouls": 'target_over_22_5_fouls'
    }
    
    for target_name, target_col in targets.items():
        y = df[target_col]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
        evaluate_models(X_train, X_test, y_train, y_test, target_name)

if __name__ == "__main__":
    train_and_test()
