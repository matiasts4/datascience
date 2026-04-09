import os
import joblib
import pandas as pd
import numpy as np
import warnings
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.inspection import permutation_importance
from src.config import FEATURES_PATH, FEATURES, MODELS_DIR, TARGETS

warnings.filterwarnings("ignore")

def main():
    print("="*60)
    print("PILAR 1 & 2: REPORTE DE VERIFICACION DE MODELOS".center(60))
    print("="*60)
    
    # 1. CARGA DE DATOS
    df = pd.read_csv(FEATURES_PATH)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    
    # Definir targets al vuelo
    df['target_1x2'] = df['result_1x2'].astype(int)
    df['target_dc_1X'] = (df['result_1x2'] >= 1).astype(int)
    df['target_dc_X2'] = (df['result_1x2'] <= 1).astype(int)
    df['target_over_2_5_goals'] = (df['total_goals'] > 2.5).astype(int)
    df['target_under_2_5_goals'] = (df['total_goals'] <= 2.5).astype(int)
    df['target_btts'] = df['btts'].astype(int)
    df['target_btts_no'] = (df['btts'] == 0).astype(int)
    df['target_home_clean_sheet'] = (df['away_goals'] == 0).astype(int)

    # 2. DEFINIR SET DE PRUEBA ESTRITO (Últimos 600 partidos, ~1 año y medio)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    test_set = df.tail(600).copy()
    
    X_test = test_set[FEATURES]

    # Evaluaremos solo los 4 mercados principales de interés
    markets_to_eval = [
        "1X2 (Match Winner)",
        "Double Chance 1X (Home or Draw)",
        "Double Chance X2 (Away or Draw)",
        "Over 2.5 Goals",
        "Under 2.5 Goals",
        "BTTS (Both Teams To Score)",
        "BTTS - No",
        "Home Clean Sheet"
    ]
    
    for market in markets_to_eval:
        target_col = TARGETS[market]
        y_test = test_set[target_col]
        
        # ⚠️ CORRECCIÓN DE DATA LEAKAGE: Entrenamos el modelo estrictamente con los datos HASTA los últimos 600 partidos.
        # No usamos el .pkl "best_model" pre-entrenado porque ese .pkl fue entrenado con la base COMPLETA (incluyendo validación).
        train_X = df[FEATURES].iloc[:-600]
        train_y = df[target_col].iloc[:-600]
        
        # Para que el testing use exactamente los mismos hiperparámetros que Optuna seleccionó para ese target en la malla moderna
        if '1X2' in market:
            model = RandomForestClassifier(n_estimators=500, max_depth=9, min_samples_split=10, random_state=42, n_jobs=-1)
        elif market == 'Double Chance 1X':
            model = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_split=8, random_state=42, n_jobs=-1)
        elif market == 'Double Chance X2':
            model = HistGradientBoostingClassifier(learning_rate=0.041, max_depth=10, l2_regularization=4.82, max_iter=100, random_state=42)
        elif market == 'Over 2.5 Goals':
            model = RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=3, random_state=42, n_jobs=-1)
        elif market == 'Under 2.5 Goals':
            model = RandomForestClassifier(n_estimators=500, max_depth=8, min_samples_split=2, random_state=42, n_jobs=-1)
        elif market == 'BTTS':
            model = RandomForestClassifier(n_estimators=200, max_depth=7, min_samples_split=7, random_state=42, n_jobs=-1)
        elif market == 'BTTS - No':
            model = RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=6, random_state=42, n_jobs=-1)
        elif market == 'Home Clean Sheet':
            model = RandomForestClassifier(n_estimators=300, max_depth=16, min_samples_split=5, random_state=42, n_jobs=-1)
        else:
            model = RandomForestClassifier(n_estimators=150, max_depth=6, min_samples_split=10, random_state=42, n_jobs=-1)
            
        model.fit(train_X, train_y)
        y_pred = model.predict(X_test)
        
        print(f"\n[{market.upper()}] ANALISIS PROFUNDO")
        print("-" * 50)
        print(">> MATRIZ DE CONFUSION (Filas=Reales, Columnas=Predicciones)")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        print("\n>> REPORTE DE CLASIFICACION")
        # limit classification report lines
        report = classification_report(y_test, y_pred, zero_division=0, output_dict=False)
        print(report)
        
        # PILAR 1: FEATURE IMPORTANCES
        print(">> FEATURE IMPORTANCES (Top 5 Permutation)")
        result = permutation_importance(model, X_test, y_test, n_repeats=5, random_state=42, n_jobs=-1)
        importances = pd.Series(result.importances_mean, index=FEATURES)
        top5 = importances.sort_values(ascending=False).head(5)
        for feat, val in top5.items():
            print(f"   {feat:<25}: {val:.4f}")
            
if __name__ == '__main__':
    main()
