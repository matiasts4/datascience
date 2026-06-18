import pandas as pd
import numpy as np
import os
import sys
import warnings
import json
import joblib

# Reconfigurar codificación para evitar errores en Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb

warnings.filterwarnings("ignore")

# Configurar rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive', 'pl-predictor')))
from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR
from src.models_neural import PyTorchMLPClassifier
from evaluar_modelos_optimos import prepare_targets, create_pipeline, instantiate_classifier

def evaluate_config(X, y, clf, use_tomek, is_multiclass, calibrate=False):
    tscv = TimeSeriesSplit(n_splits=5)
    losses = []
    
    # Crear pipeline
    if calibrate:
        cal_clf = CalibratedClassifierCV(estimator=clf, method='isotonic', cv=3)
        pipe = create_pipeline(cal_clf, use_tomek=use_tomek)
    else:
        pipe = create_pipeline(clf, use_tomek=use_tomek)
        
    labels = [0, 1, 2] if is_multiclass else [0, 1]
    
    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        if len(np.unique(y_train)) < len(labels):
            continue
            
        try:
            pipe.fit(X_train, y_train)
            probs = pipe.predict_proba(X_test)
            loss = log_loss(y_test, probs, labels=labels)
            losses.append(loss)
        except Exception as e:
            continue
            
    return np.mean(losses) if len(losses) > 0 else 999.0

def main():
    json_path = os.path.join(MODELS_DIR, "optimized_hyperparams.json")
    if not os.path.exists(json_path):
        print(f"[Error] No se encontro el archivo de hiperparametros {json_path}")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        optimized_data = json.load(f)
        
    if not os.path.exists(FEATURES_PATH):
        print(f"[Error] No se encontro el dataset en {FEATURES_PATH}")
        return
        
    df = pd.read_csv(FEATURES_PATH)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = prepare_targets(df)
    
    X = df[FEATURES]
    
    models_list = [
        "Logistic Regression (Elastic Net)",
        "Random Forest",
        "HistGradientBoosting (Early Stopping)",
        "XGBoost (L1/L2 Regularized)",
        "Neural Network (Dropout)"
    ]
    
    print("==================================================")
    print("SISTEMA DE OPTIMIZACION Y CALIBRACION DE CAPA 1")
    print("==================================================")
    
    for target_name, target_col in TARGETS.items():
        if target_col not in df.columns:
            continue
            
        y = df[target_col]
        is_multiclass = len(np.unique(y)) > 2
        use_tomek = target_name in ["1X2 (Match Winner)", "Home Clean Sheet", "Double Chance 1X (Home or Draw)", "Double Chance X2 (Away or Draw)"]
        
        print(f"\nMercado: {target_name}")
        print("-" * 50)
        
        best_loss = 999.0
        best_model_name = None
        best_params = None
        best_calibrated = False
        
        for model_name in models_list:
            if model_name not in optimized_data[target_name]:
                continue
                
            info = optimized_data[target_name][model_name]
            params = info["best_params"]
            
            # Evaluar original (sin calibrar)
            clf_raw = instantiate_classifier(model_name, params)
            loss_raw = evaluate_config(X, y, clf_raw, use_tomek, is_multiclass, calibrate=False)
            print(f"  {model_name:<38} | Log Loss Raw: {loss_raw:.4f}")
            
            if loss_raw < best_loss:
                best_loss = loss_raw
                best_model_name = model_name
                best_params = params
                best_calibrated = False
                
            # Evaluar calibrado (excepto para regresión logística que ya está calibrada)
            if "Logistic Regression" not in model_name:
                clf_cal = instantiate_classifier(model_name, params)
                loss_cal = evaluate_config(X, y, clf_cal, use_tomek, is_multiclass, calibrate=True)
                print(f"  {model_name + ' (Calibrated)':<38} | Log Loss Cal: {loss_cal:.4f}")
                
                if loss_cal < best_loss:
                    best_loss = loss_cal
                    best_model_name = model_name
                    best_params = params
                    best_calibrated = True
                    
        print(f"\n[Mejor Configuracion] PARA {target_name}:")
        print(f"   * Modelo: {best_model_name}")
        print(f"   * Calibrado: {best_calibrated}")
        print(f"   * Log Loss CV: {best_loss:.4f}")
        
        # Entrenar modelo final con toda la data
        print("   -> Entrenando modelo de produccion final...")
        clf_final = instantiate_classifier(best_model_name, best_params)
        
        if best_calibrated:
            cal_clf_final = CalibratedClassifierCV(estimator=clf_final, method='isotonic', cv=5)
            pipe_final = create_pipeline(cal_clf_final, use_tomek=use_tomek)
        else:
            pipe_final = create_pipeline(clf_final, use_tomek=use_tomek)
            
        pipe_final.fit(X, y)
        
        # Guardar en pickle
        safe_name = target_name.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
        model_path = os.path.join(MODELS_DIR, f"model_{safe_name}.pkl")
        joblib.dump(pipe_final, model_path)
        print(f"   [OK] Guardado en: {model_path}")
        
    print("\n==================================================")
    print("[Exito] MEJORA Y CALIBRACION DE TODOS LOS MODELOS FINALIZADA!")
    print("==================================================")

if __name__ == '__main__':
    main()
