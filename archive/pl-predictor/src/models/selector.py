import os
import joblib
import pandas as pd
import numpy as np

from src.config import MODELS_DIR, TARGETS, FEATURES

class MasterBetSelector:
    def __init__(self):
        self.scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
        self.models = {}
        for target_name in TARGETS.keys():
            safe_name = target_name.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
            model_path = os.path.join(MODELS_DIR, f"model_{safe_name}.pkl")
            if os.path.exists(model_path):
                self.models[target_name] = joblib.load(model_path)
    
    def get_best_bet(self, match_features_dict):
        # match_features_dict should have keys matching FEATURES
        df = pd.DataFrame([match_features_dict])
        
        # Ensure correct order
        X = df[FEATURES]
        X_scaled = self.scaler.transform(X)
        
        predictions = []
        for target_name, model in self.models.items():
            try:
                # Get probability of class 1 (Target True)
                if len(model.classes_) == 2 and 1 in model.classes_:
                    idx = list(model.classes_).index(1)
                    prob = model.predict_proba(X_scaled)[0][idx]
                else:
                    # For 1X2 (multiclass) get max probability
                    prob = max(model.predict_proba(X_scaled)[0])
                    
                predictions.append({
                    "Market": target_name,
                    "Probability": prob,
                    "Confidence": f"{prob*100:.1f}%"
                })
            except Exception as e:
                pass
                
        # Sort by probability
        predictions.sort(key=lambda x: x['Probability'], reverse=True)
        return predictions
