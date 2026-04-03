import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score
from sklearn.calibration import CalibratedClassifierCV

from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR

def train_best_model_for_target(X_train, y_train, target_name):
    print(f"  [{target_name}] Tuning Random Forest...")
    rf = RandomForestClassifier(random_state=42)
    rf_params = {'n_estimators': [50, 100], 'max_depth': [5, 10]}
    search_rf = RandomizedSearchCV(rf, rf_params, n_iter=2, cv=3, scoring='accuracy', random_state=42, n_jobs=-1)
    search_rf.fit(X_train, y_train)
    best_rf = search_rf.best_estimator_

    print(f"  [{target_name}] Best RF CV Acc: {search_rf.best_score_:.4f}")

    lr = LogisticRegression(max_iter=1000, random_state=42, C=0.5)

    ensemble = VotingClassifier(
        estimators=[('rf', best_rf), ('lr', lr)],
        voting='soft'
    )
    
    calibrated_model = CalibratedClassifierCV(ensemble, method='isotonic', cv=3)
    calibrated_model.fit(X_train, y_train)
    
    return calibrated_model

def train_all_models():
    print("Loading data for training...")
    df = pd.read_csv(FEATURES_PATH).dropna()
    
    df['target_btts'] = df['btts'].astype(int)
    df['target_over_4_5_cards'] = (df['total_cards'] > 4.5).astype(int)
    df['target_over_2_5_goals'] = (df['total_goals'] > 2.5).astype(int)
    df['target_1x2'] = df['result_1x2'].astype(int)
    df['total_fouls'] = df['home_match_fouls'] + df['away_match_fouls']
    df['target_over_22_5_fouls'] = (df['total_fouls'] > 22.5).astype(int)
    df['target_dc_1X'] = (df['result_1x2'] >= 1).astype(int)
    df['target_dc_X2'] = (df['result_1x2'] <= 1).astype(int)
    df['target_home_over_0_5'] = (df['home_goals'] > 0.5).astype(int)
    df['target_away_over_0_5'] = (df['away_goals'] > 0.5).astype(int)
    
    # New Extended Targets
    df['target_under_2_5_goals'] = (df['total_goals'] <= 2.5).astype(int)
    df['target_btts_no'] = (df['btts'] == 0).astype(int)
    df['target_under_4_5_cards'] = (df['total_cards'] <= 4.5).astype(int)
    df['target_under_22_5_fouls'] = (df['total_fouls'] <= 22.5).astype(int)
    df['target_home_clean_sheet'] = (df['away_goals'] == 0).astype(int)
    df['target_away_clean_sheet'] = (df['home_goals'] == 0).astype(int)
    df['target_home_win_to_nil'] = ((df['home_goals'] > df['away_goals']) & (df['away_goals'] == 0)).astype(int)
    
    X = df[FEATURES]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(scaler, os.path.join(MODELS_DIR, 'scaler.pkl'))
    
    for target_name, target_col in TARGETS.items():
        y = df[target_col]
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, shuffle=False)
        
        safe_name = target_name.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
        model_path = os.path.join(MODELS_DIR, f"model_{safe_name}.pkl")
        
        if os.path.exists(model_path):
            print(f"Skipping {target_name}, already trained.")
            continue
            
        print(f"\nTraining for: {target_name}")
        best_model = train_best_model_for_target(X_train, y_train, target_name)
        
        preds = best_model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        print(f"  [{target_name}] Test Accuracy: {acc:.4f}")
        
        safe_name = target_name.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
        model_path = os.path.join(MODELS_DIR, f"model_{safe_name}.pkl")
        joblib.dump(best_model, model_path)

if __name__ == '__main__':
    train_all_models()
