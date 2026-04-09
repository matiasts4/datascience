import os
import pandas as pd
import numpy as np
import optuna
import warnings
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score
from src.config import FEATURES_PATH, TARGETS, FEATURES

warnings.filterwarnings('ignore')

# Usar el set moderno (los últimos 600 partidos) para evaluar el tuning
# Esto fuerza a Optuna a especializarse en fútbol moderno en vez del promedio de hace 10 años
VALIDATION_SIZE = 600

def objective_rf(trial, X_train, y_train, X_val, y_val):
    # Damos más libertad de profundidad para capturar patrones modernos
    n_estimators = trial.suggest_int('n_estimators', 100, 500, step=50)
    max_depth = trial.suggest_int('max_depth', 5, 20)
    min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
    
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    preds = model.predict(X_val)
    return accuracy_score(y_val, preds)

def objective_hgb(trial, X_train, y_train, X_val, y_val):
    learning_rate = trial.suggest_float('learning_rate', 0.01, 0.2, log=True)
    max_depth = trial.suggest_int('max_depth', 4, 15)
    l2_regularization = trial.suggest_float('l2_regularization', 0.0, 5.0)
    max_iter = trial.suggest_int('max_iter', 100, 400, step=50)

    model = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_depth=max_depth,
        l2_regularization=l2_regularization,
        max_iter=max_iter,
        random_state=42
    )

    model.fit(X_train, y_train)
    preds = model.predict(X_val)
    return accuracy_score(y_val, preds)


def run_optuna_modern_tuning():
    print("🔥 Iniciando Optuna MODERN Search (Evaluación en Puros Últimos 600) 🔥")
    df = pd.read_csv(FEATURES_PATH)
    
    # Preparar DF de targets básicos
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    
    df['target_1x2'] = df['result_1x2'].astype(int)
    df['target_dc_1X'] = (df['result_1x2'] >= 1).astype(int)
    df['target_dc_X2'] = (df['result_1x2'] <= 1).astype(int)
    df['target_over_2_5_goals'] = (df['total_goals'] > 2.5).astype(int)
    df['target_under_2_5_goals'] = (df['total_goals'] <= 2.5).astype(int)
    df['target_btts'] = df['btts'].astype(int)
    df['target_btts_no'] = (df['btts'] == 0).astype(int)
    df['target_home_clean_sheet'] = (df['away_goals'] == 0).astype(int)
    
    markets = {
        '1X2 (Match Winner)': df['target_1x2'],
        'Double Chance 1X': df['target_dc_1X'],
        'Double Chance X2': df['target_dc_X2'],
        'Over 2.5 Goals': df['target_over_2_5_goals'],
        'Under 2.5 Goals': df['target_under_2_5_goals'],
        'BTTS': df['target_btts'],
        'BTTS - No': df['target_btts_no'],
        'Home Clean Sheet': df['target_home_clean_sheet']
    }
    
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    X = df[FEATURES]
    
    # Split Moderno Ciego
    X_train = X.iloc[:-VALIDATION_SIZE]
    X_val = X.iloc[-VALIDATION_SIZE:]
    
    for market_name, y in markets.items():
        print(f"\n==============================================")
        print(f"🎯 Optimizando Mercado: {market_name}")
        print(f"==============================================")
        
        y_train = y.iloc[:-VALIDATION_SIZE]
        y_val = y.iloc[-VALIDATION_SIZE:]
        
        # RF Tuning
        print("-> Tuning Random Forest (Profundidad Agresiva)...")
        study_rf = optuna.create_study(direction='maximize')
        study_rf.optimize(lambda trial: objective_rf(trial, X_train, y_train, X_val, y_val), n_trials=30)
        print(f"   Mejor Acc RF (Moderno): {study_rf.best_value:.4f}")
        print(f"   Params RF: {study_rf.best_params}")
        
        # HistGradientBoosting para mercados específicos que lo aprovechan mejor
        if market_name in ['Home Clean Sheet', 'Double Chance X2']:
            print("-> Tuning HistGradientBoosting...")
            study_hgb = optuna.create_study(direction='maximize')
            study_hgb.optimize(lambda trial: objective_hgb(trial, X_train, y_train, X_val, y_val), n_trials=20)
            print(f"   Mejor Acc HGB (Moderno): {study_hgb.best_value:.4f}")
            print(f"   Params HGB: {study_hgb.best_params}")
        
if __name__ == "__main__":
    run_optuna_modern_tuning()
