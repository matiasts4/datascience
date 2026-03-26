import pandas as pd
import numpy as np
import os
from sklearn.model_selection import RandomizedSearchCV, train_test_split, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

# Paths
BASE_DIR = r"c:\Users\PC\DataScience\archive\pl-predictor"
FEATURES_PATH = os.path.join(BASE_DIR, "data", "historical", "all_match_features_v2.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models", "optimized")

os.makedirs(MODELS_DIR, exist_ok=True)

# Define Hyperparameter grids
PARAM_GRIDS = {
    "Logistic Regression": {
        "model": LogisticRegression(max_iter=2000, random_state=42),
        "params": {
            "C": [0.001, 0.01, 0.1, 1, 10, 100],
            "penalty": ["l2"],
            "solver": ["lbfgs", "liblinear"]
        }
    },
    "Random Forest": {
        "model": RandomForestClassifier(random_state=42),
        "params": {
            "n_estimators": [100, 200, 300, 500],
            "max_depth": [None, 5, 10, 20, 30],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4]
        }
    },
    "HistGradientBoosting": {
        "model": HistGradientBoostingClassifier(random_state=42),
        "params": {
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "max_iter": [100, 200, 300],
            "max_depth": [None, 3, 5, 10],
            "l2_regularization": [0.0, 0.1, 1.0, 10.0]
        }
    }
}

def load_data():
    df = pd.read_csv(FEATURES_PATH)
    df = df.dropna()
    
    df['target_1x2'] = df['result_1x2'].astype(int)
    df['target_over_2_5_goals'] = (df['total_goals'] > 2.5).astype(int)
    df['target_btts'] = df['btts'].astype(int)
    
    features = [
        'home_elo', 'away_elo',
        'h_l5_pts', 'h_l5_sh', 'h_l5_sot', 'h_l5_sot_c', 'h_l5_gf', 'h_l5_ga', 'h_l5_fls',
        'a_l5_pts', 'a_l5_sh', 'a_l5_sot', 'a_l5_sot_c', 'a_l5_gf', 'a_l5_ga', 'a_l5_fls',
        'referee_avg_cards_history'
    ]
    return df, features

def run_optimization():
    print("Loading data for optimization...")
    df, feature_cols = load_data()
    X = df[feature_cols]
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    targets = {
        "1X2 (Match Winner)": "target_1x2",
        "Over 2.5 Goals": "target_over_2_5_goals",
        "BTTS (Both Teams To Score)": "target_btts"
    }

    # TimeSeriesSplit is better for chronological sports data
    cv = TimeSeriesSplit(n_splits=5)

    results_md = "# Resultados de Optimización de Hiperparámetros\n\n"

    for target_name, target_col in targets.items():
        print(f"\n{'='*50}")
        print(f"OPTIMIZING MODELS FOR: {target_name}")
        print(f"{'='*50}")
        
        y = df[target_col]
        # Train-Test Split (Chronological)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, shuffle=False)
        
        best_overall_acc = 0
        best_overall_model = None
        best_overall_name = ""
        best_params_str = ""

        results_md += f"## {target_name}\n"

        for model_name, config in PARAM_GRIDS.items():
            print(f"Tuning {model_name}...")
            search = RandomizedSearchCV(
                config["model"],
                param_distributions=config["params"],
                n_iter=15,
                cv=cv,
                scoring="accuracy",
                n_jobs=-1,
                random_state=42,
                verbose=1
            )
            
            search.fit(X_train, y_train)
            
            # Predict on test set
            best_model = search.best_estimator_
            preds = best_model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            
            print(f"[{model_name}] Best Params: {search.best_params_}")
            print(f"[{model_name}] Test Accuracy: {acc:.4f}\n")
            
            results_md += f"- **{model_name}** - Test Accuracy: `{acc:.4f}`\n"
            results_md += f"  - Mejores Parámetros: `{search.best_params_}`\n"

            if acc > best_overall_acc:
                best_overall_acc = acc
                best_overall_model = best_model
                best_overall_name = model_name
                best_params_str = search.best_params_
                
        print(f"🏆 Best optimized model for {target_name}: {best_overall_name} (Acc: {best_overall_acc:.4f})")
        results_md += f"\n🏆 **GANADOR PARA {target_name}**: {best_overall_name} (Acc: `{best_overall_acc:.4f}`)\n\n---\n"
        
        # Save model
        target_slug = target_name.replace(' ', '_').replace('(', '').replace(')', '').lower()
        model_path = os.path.join(MODELS_DIR, f"best_{target_slug}.pkl")
        joblib.dump(best_overall_model, model_path)
    
    # Save the results to artifact
    with open(os.path.join(BASE_DIR, "experiment_results.md"), "w", encoding="utf-8") as f:
        f.write(results_md)
        
    # Save the scaler (Critical for inference)
    scaler_path = os.path.join(BASE_DIR, "models", "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    print(f"Scaler saved in: {scaler_path}")
        
    print(f"\nOptimización finalizada. Resultados guardados en experiment_results.md")
    print(f"Modelos guardados en: {MODELS_DIR}")

if __name__ == "__main__":
    run_optimization()
