import os
import sys
import warnings
import joblib
import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# Configurar rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive', 'pl-predictor')))
from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR
from evaluar_modelos_optimos import prepare_targets

def main():
    df = pd.read_csv(FEATURES_PATH)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = prepare_targets(df)
    
    # Probar con un subconjunto
    X = df[FEATURES]
    
    # Modelos a probar
    test_files = [
        ("model_1X2_Match_Winner.pkl", "1X2 (Match Winner)"), # LogisticRegression (Multiclass)
        ("model_Home_Clean_Sheet.pkl", "Home Clean Sheet"),   # PyTorchMLPClassifier (Binary)
        ("model_BTTS_Both_Teams_To_Score.pkl", "BTTS (Both Teams To Score)") # HistGradientBoosting (Binary)
    ]
    
    for filename, market_name in test_files:
        model_path = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(model_path):
            print(f"❌ No existe {model_path}")
            continue
            
        print(f"\nProbando SHAP para {market_name} ({filename})...")
        pipe = joblib.load(model_path)
        preprocessor = pipe.named_steps['preprocessor']
        classifier = pipe.named_steps['classifier']
        
        # Transformar datos
        X_transformed = preprocessor.transform(X)
        skewed_features = ['away_xg', 'referee_avg_cards_history', 'B365H', 'B365D', 'B365A', 'h_l5_fls', 'a_l5_fls', 'h_l5_xg', 'a_l5_xg', 'h_l5_xga', 'a_l5_xga']
        skewed_in_features = [f for f in skewed_features if f in FEATURES]
        standard_in_features = [f for f in FEATURES if f not in skewed_in_features]
        feature_names = skewed_in_features + standard_in_features
        X_trans_df = pd.DataFrame(X_transformed, columns=feature_names)
        
        clf_type = type(classifier).__name__
        print(f"  Tipo: {clf_type}")
        
        # Probar explicador
        try:
            if "HistGradientBoostingClassifier" in clf_type:
                explainer = shap.TreeExplainer(classifier)
                shap_values = explainer(X_trans_df)
                print("  [OK] TreeExplainer completo para HistGradientBoosting")
            elif "LogisticRegression" in clf_type:
                # Si es multiclase (1X2 tiene 3 clases), predict_proba tiene shape (N, 3)
                # Probamos explainer lineal
                explainer = shap.LinearExplainer(classifier, X_trans_df)
                shap_values = explainer(X_trans_df)
                print("  [OK] LinearExplainer completo para LogisticRegression")
            elif "PyTorchMLPClassifier" in clf_type:
                # Muestrear background para velocidad
                X_bg = shap.sample(X_trans_df, 50)
                f_prob = lambda x: classifier.predict_proba(x)[:, 1]
                explainer = shap.Explainer(f_prob, X_bg)
                shap_values = explainer(shap.sample(X_trans_df, 100))
                print("  [OK] Explainer genérico completo para PyTorchMLPClassifier")
        except Exception as e:
            print(f"  ❌ Error con {clf_type}: {e}")

if __name__ == '__main__':
    main()
