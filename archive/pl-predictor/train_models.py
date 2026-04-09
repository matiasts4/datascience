import pandas as pd
import numpy as np
import os
import joblib
import warnings
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR

warnings.filterwarnings("ignore")

def prepare_targets(df):
    """Calcula los targets a partir de las columnas base para que los modelos sean ciegos al resultado original."""
    df_out = df.copy()
    # Las columnas base en el v5 son: home_goals, away_goals, total_goals, btts, result_1x2
    df_out['target_1x2'] = df_out['result_1x2'].astype(int)
    df_out['target_dc_1X'] = (df_out['result_1x2'] >= 1).astype(int)
    df_out['target_dc_X2'] = (df_out['result_1x2'] <= 1).astype(int)
    df_out['target_over_2_5_goals'] = (df_out['total_goals'] > 2.5).astype(int)
    df_out['target_under_2_5_goals'] = (df_out['total_goals'] <= 2.5).astype(int)
    df_out['target_btts'] = df_out['btts'].astype(int)
    df_out['target_btts_no'] = (df_out['btts'] == 0).astype(int)
    df_out['target_home_clean_sheet'] = (df_out['away_goals'] == 0).astype(int)
    return df_out

def evaluate_models_tscv(df, target_name, target_col):
    print(f"\n{'='*65}")
    print(f"EVALUANDO MODELOS CON TimeSeriesSplit PARA: {target_name}")
    print(f"{'='*65}")
    
    # Ordenar por fecha es CRUCIAL para TimeSeriesSplit en fútbol
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    X = df[FEATURES]
    y = df[target_col]
    
    if '1X2' in target_name:
        rf = RandomForestClassifier(n_estimators=500, max_depth=9, min_samples_split=10, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.0187, max_depth=3, l2_regularization=7.36, max_iter=150, random_state=42)
    elif target_name == 'Double Chance 1X (Home or Draw)':
        rf = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_split=8, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.03, max_iter=200, max_depth=5, random_state=42)
    elif target_name == 'Double Chance X2 (Away or Draw)':
        rf = RandomForestClassifier(n_estimators=200, max_depth=16, min_samples_split=10, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.041, max_depth=10, l2_regularization=4.82, max_iter=100, random_state=42)
    elif 'Over' in target_name:
        rf = RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=3, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.0102, max_depth=3, l2_regularization=0.05, max_iter=50, random_state=42)
    elif 'Under' in target_name:
        rf = RandomForestClassifier(n_estimators=500, max_depth=8, min_samples_split=2, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.01, max_depth=3, max_iter=50, random_state=42)
    elif target_name == 'BTTS (Both Teams To Score)':
        rf = RandomForestClassifier(n_estimators=200, max_depth=7, min_samples_split=7, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.0106, max_depth=4, l2_regularization=9.98, max_iter=50, random_state=42)
    elif target_name == 'BTTS - No':
        rf = RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=6, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.01, max_depth=3, max_iter=50, random_state=42)
    elif target_name == 'Home Clean Sheet':
        rf = RandomForestClassifier(n_estimators=300, max_depth=16, min_samples_split=5, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.014, max_depth=4, l2_regularization=2.27, max_iter=100, random_state=42)
    else:
        rf = RandomForestClassifier(n_estimators=150, max_depth=6, min_samples_split=10, random_state=42, n_jobs=-1)
        hgb = HistGradientBoostingClassifier(learning_rate=0.03, max_iter=200, max_depth=5, l2_regularization=5.0, random_state=42)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": rf,
        "HistGradientBoosting": hgb,
        "XGBoost": xgb.XGBClassifier(eval_metric='logloss', random_state=42, max_depth=4, learning_rate=0.05, n_estimators=150)
    }
    
    tscv = TimeSeriesSplit(n_splits=5)
    
    is_multiclass = len(np.unique(y)) > 2
    
    results = {name: {'acc': [], 'auc': [], 'f1': []} for name in models.keys()}
    
    for name, model in models.items():
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            
            results[name]['acc'].append(accuracy_score(y_test, preds))
            
            if not is_multiclass:
                results[name]['f1'].append(f1_score(y_test, preds, zero_division=0))
                try:
                    probs = model.predict_proba(X_test)[:, 1]
                    results[name]['auc'].append(roc_auc_score(y_test, probs))
                except:
                    results[name]['auc'].append(0)
            else:
                results[name]['f1'].append(f1_score(y_test, preds, average='weighted', zero_division=0))
                results[name]['auc'].append(0)
                
    
    print(f"{'Model':<25} | {'Accuracy':<10} | {'ROC-AUC':<10} | {'F1-Score':<10}")
    print("-" * 65)
    
    best_name = None
    best_acc = 0
    final_models = {}
    
    for name in models.keys():
        avg_acc = np.mean(results[name]['acc'])
        avg_auc = np.mean(results[name]['auc'])
        avg_f1 = np.mean(results[name]['f1'])
        
        print(f"{name:<25} | {avg_acc:.4f}     | {avg_auc:.4f}     | {avg_f1:.4f}")
        
        if avg_acc > best_acc:
            best_acc = avg_acc
            best_name = name
            
    print(f"👉 BEST MODEL: {best_name} (Acc: {best_acc:.4f})")
    
    # Entrenar el mejor modelo con TODA la data temporal para guardarlo listo para producción
    best_model = models[best_name]
    best_model.fit(X, y)
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    safe_name = target_name.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
    model_path = os.path.join(MODELS_DIR, f"model_{safe_name}.pkl")
    joblib.dump(best_model, model_path)

def main():
    print(f"Leyendo dataset maestro sanitizado: {FEATURES_PATH}")
    if not os.path.exists(FEATURES_PATH):
        print(f"❌ Error: No se encontró el dataset {FEATURES_PATH}")
        return
        
    df = pd.read_csv(FEATURES_PATH)
    
    # Validar integridad pura
    print(f"✅ Total de registros crudos: {len(df)}")
    
    # Remover fixtures futuros no jugados (2025/2026 adelantados en db con game_id=0)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    print(f"✅ Filtrados partidos no jugados. Registros reales para training: {len(df)}")
    
    # Armar Targets dinámicamente y de forma limpia
    df = prepare_targets(df)
    
    # Ejecutar evaluación cruzada temporal
    for target_name, target_col in TARGETS.items():
        if target_col in df.columns:
            evaluate_models_tscv(df, target_name, target_col)
        else:
            print(f"❌ Error: Target {target_col} no encontrado.")

if __name__ == "__main__":
    main()
