import os
import pandas as pd
import numpy as np
import optuna
import warnings
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
from src.config import FEATURES_PATH, TARGETS, FEATURES

warnings.filterwarnings('ignore')

def objective_rf(trial, X, y):
    n_estimators = trial.suggest_int('n_estimators', 50, 300, step=50)
    max_depth = trial.suggest_int('max_depth', 3, 12)
    min_samples_split = trial.suggest_int('min_samples_split', 2, 20)
    
    cv = TimeSeriesSplit(n_splits=5)
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=42,
        n_jobs=-1
    )
    
    accuracies = []
    for train_idx, test_idx in cv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        accuracies.append(accuracy_score(y_test, preds))
        
    return np.mean(accuracies)

def objective_hgb(trial, X, y):
    learning_rate = trial.suggest_float('learning_rate', 0.01, 0.2, log=True)
    max_depth = trial.suggest_int('max_depth', 3, 10)
    l2_regularization = trial.suggest_float('l2_regularization', 0.0, 10.0)
    max_iter = trial.suggest_int('max_iter', 50, 300, step=50)

    cv = TimeSeriesSplit(n_splits=5)
    model = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_depth=max_depth,
        l2_regularization=l2_regularization,
        max_iter=max_iter,
        random_state=42
    )

    accuracies = []
    for train_idx, test_idx in cv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        accuracies.append(accuracy_score(y_test, preds))

    return np.mean(accuracies)


def run_optuna_tuning():
    print("🔥 Iniciando Optuna Bayesian Search 🔥")
    df = pd.read_csv(FEATURES_PATH)
    
    # Preparar DF de targets básicos (mismo código que train_models)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    
    df['target_1x2'] = df['result_1x2'].astype(int)
    df['target_over_2_5_goals'] = (df['total_goals'] > 2.5).astype(int)
    df['target_btts'] = df['btts'].astype(int)
    
    # Escogeremos estos 3 mercados principales como proxy
    markets = {
        '1X2 (Match Winner)': df['target_1x2'],
        'Over 2.5 Goals': df['target_over_2_5_goals'],
        'BTTS (Both Teams To Score)': df['target_btts']
    }
    
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    X = df[FEATURES]
    
    for market_name, y in markets.items():
        print(f"\n==============================================")
        print(f"🎯 Optimizando Mercado: {market_name}")
        print(f"==============================================")
        
        # RF Tuning
        print("-> Tuning Random Forest...")
        study_rf = optuna.create_study(direction='maximize')
        study_rf.optimize(lambda trial: objective_rf(trial, X, y), n_trials=15)
        print(f"   Mejor Acc RF: {study_rf.best_value:.4f}")
        print(f"   Params RF: {study_rf.best_params}")
        
        # HGB Tuning
        print("-> Tuning HistGradientBoosting...")
        study_hgb = optuna.create_study(direction='maximize')
        study_hgb.optimize(lambda trial: objective_hgb(trial, X, y), n_trials=15)
        print(f"   Mejor Acc HGB: {study_hgb.best_value:.4f}")
        print(f"   Params HGB: {study_hgb.best_params}")

if __name__ == "__main__":
    run_optuna_tuning()
