import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR

def evaluate_saved_models():
    print("Loading data for evaluation...")
    df = pd.read_csv(FEATURES_PATH)
    essential_cols = FEATURES + ['btts', 'total_cards', 'total_goals', 'result_1x2', 'home_goals', 'away_goals']
    df = df.dropna(subset=[c for c in essential_cols if c in df.columns]).reset_index(drop=True)
    
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
    
    df['target_under_2_5_goals'] = (df['total_goals'] <= 2.5).astype(int)
    df['target_btts_no'] = (df['btts'] == 0).astype(int)
    df['target_under_4_5_cards'] = (df['total_cards'] <= 4.5).astype(int)
    df['target_under_22_5_fouls'] = (df['total_fouls'] <= 22.5).astype(int)
    df['target_home_clean_sheet'] = (df['away_goals'] == 0).astype(int)
    df['target_away_clean_sheet'] = (df['home_goals'] == 0).astype(int)
    df['target_home_win_to_nil'] = ((df['home_goals'] > df['away_goals']) & (df['away_goals'] == 0)).astype(int)
    
    X = df[FEATURES]
    scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
    X_scaled = scaler.transform(X)
    
    print("\n✅ RESULTADOS DEL TEST SOBRE DATOS 2024-2025 (20% más recientes):")
    print("-" * 55)
    print(f"{'MERCADO (APUESTA)':<35} | {'PRECISIÓN (ACCURACY)'}")
    print("-" * 55)
    
    for target_name, target_col in TARGETS.items():
        y = df[target_col]
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, shuffle=False)
        
        safe_name = target_name.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
        model_path = os.path.join(MODELS_DIR, f"model_{safe_name}.pkl")
        
        if not os.path.exists(model_path):
            print(f"{target_name:<35} | Model not found!")
            continue
            
        model = joblib.load(model_path)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        
        print(f"{target_name:<35} | {acc*100:.2f}%")
        
    print("-" * 55)

if __name__ == '__main__':
    evaluate_saved_models()
