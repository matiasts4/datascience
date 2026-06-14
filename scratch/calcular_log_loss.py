import pandas as pd
import numpy as np
import os
import sys
import json
import warnings
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, accuracy_score
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb

# Asegurar que el directorio del pl-predictor esté en el path para importar src y evaluar_modelos_optimos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive', 'pl-predictor')))
from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR
from src.models_neural import PyTorchMLPClassifier
from evaluar_modelos_optimos import prepare_targets, create_pipeline, instantiate_classifier

def main():
    json_path = os.path.join(MODELS_DIR, "optimized_hyperparams.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        optimized_data = json.load(f)
        
    df = pd.read_csv(FEATURES_PATH)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = prepare_targets(df)
    
    X = df[FEATURES]
    tscv = TimeSeriesSplit(n_splits=5)
    
    models_list = [
        "Logistic Regression (Elastic Net)",
        "Random Forest",
        "HistGradientBoosting (Early Stopping)",
        "XGBoost (L1/L2 Regularized)",
        "Neural Network (Dropout)"
    ]
    
    # Mapa de ganadores de modelos_finales_metricas.md
    winners = {
        "1X2 (Match Winner)": "Logistic Regression (Elastic Net)",
        "Double Chance 1X (Home or Draw)": "Logistic Regression (Elastic Net)",
        "Double Chance X2 (Away or Draw)": "Logistic Regression (Elastic Net)",
        "Over 2.5 Goals": "XGBoost (L1/L2 Regularized)",
        "Under 2.5 Goals": "XGBoost (L1/L2 Regularized)",
        "BTTS (Both Teams To Score)": "HistGradientBoosting (Early Stopping)",
        "BTTS - No": "Neural Network (Dropout)",
        "Home Clean Sheet": "Neural Network (Dropout)"
    }
    
    print("\n=======================================================")
    print("CALCULANDO METRICAS LOG LOSS (TimeSeriesSplit 5-splits)")
    print("=======================================================")
    
    results = []
    for target_name, target_col in TARGETS.items():
        y = df[target_col]
        is_multiclass = len(np.unique(y)) > 2
        use_tomek = target_name in ["1X2 (Match Winner)", "Home Clean Sheet"]
        winner_model = winners[target_name]
        
        print(f"\nMercado: {target_name}")
        
        for model_name in models_list:
            info = optimized_data[target_name][model_name]
            params = info["best_params"]
            
            clf = instantiate_classifier(model_name, params)
            pipe = create_pipeline(clf, use_tomek=use_tomek)
            
            losses = []
            accs = []
            
            for train_idx, test_idx in tscv.split(X):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                try:
                    pipe.fit(X_train, y_train)
                    probs = pipe.predict_proba(X_test)
                    preds = pipe.predict(X_test)
                    
                    losses.append(log_loss(y_test, probs))
                    accs.append(accuracy_score(y_test, preds))
                except Exception as e:
                    losses.append(np.nan)
                    accs.append(0.0)
            
            mean_loss = np.nanmean(losses)
            mean_acc = np.mean(accs)
            is_winner = " [GANADOR]" if model_name == winner_model else ""
            print(f"  - {model_name:<38} | Log Loss: {mean_loss:.5f} | Acc: {mean_acc:.4f}{is_winner}")
            
            results.append({
                "target": target_name,
                "model": model_name,
                "log_loss": mean_loss,
                "accuracy": mean_acc,
                "is_winner": model_name == winner_model
            })
            
    # Guardar resultados
    results_df = pd.DataFrame(results)
    
    # 1. Guardar como CSV
    csv_out = os.path.join(os.path.dirname(__file__), "optimized_models_log_loss.csv")
    results_df.to_csv(csv_out, index=False)
    print(f"\nResultados CSV guardados en: {csv_out}")
    
    # 2. Guardar como Markdown
    md_out = os.path.join(os.path.dirname(__file__), "optimized_models_log_loss.md")
    with open(md_out, "w", encoding="utf-8") as f:
        f.write("# Resultados de Log Loss y Accuracy de Validacion Cruzada Temporal (5 splits)\n\n")
        f.write("| Mercado | Modelo | Log Loss | Accuracy | Estado |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: |\n")
        for r in results:
            status = "**GANADOR**" if r["is_winner"] else ""
            f.write(f"| {r['target']} | {r['model']} | {r['log_loss']:.5f} | {r['accuracy']:.4f} | {status} |\n")
            
    print(f"Resultados Markdown guardados en: {md_out}")
    print("\nCalculo finalizado exitosamente.")

if __name__ == "__main__":
    main()
