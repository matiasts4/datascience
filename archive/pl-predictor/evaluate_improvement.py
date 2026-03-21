import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from src.config import FEATURES_PATH, TARGETS, FEATURES
from src.models.selector import MasterBetSelector
import warnings

warnings.filterwarnings('ignore')

def evaluate_models():
    print("Loading test data...")
    df = pd.read_csv(FEATURES_PATH).dropna()
    
    # Target calculations for test set (we just need to replicate what trainer.py did)
    df['target_btts'] = df['btts'].astype(int)
    df['target_over_4_5_cards'] = (df['total_cards'] > 4.5).astype(int)
    df['target_under_4_5_cards'] = (df['total_cards'] <= 4.5).astype(int)
    df['target_over_2_5_goals'] = (df['total_goals'] > 2.5).astype(int)
    df['target_under_2_5_goals'] = (df['total_goals'] <= 2.5).astype(int)
    df['target_1x2'] = df['result_1x2'].astype(int)
    df['total_fouls'] = df['home_match_fouls'] + df['away_match_fouls']
    df['target_over_22_5_fouls'] = (df['total_fouls'] > 22.5).astype(int)
    df['target_under_22_5_fouls'] = (df['total_fouls'] <= 22.5).astype(int)
    df['target_dc_1X'] = (df['result_1x2'] >= 1).astype(int)
    df['target_dc_X2'] = (df['result_1x2'] <= 1).astype(int)
    df['target_home_over_0_5'] = (df['home_goals'] > 0.5).astype(int)
    df['target_away_over_0_5'] = (df['away_goals'] > 0.5).astype(int)
    df['target_btts_no'] = (df['btts'] == 0).astype(int)
    df['target_home_clean_sheet'] = (df['away_goals'] == 0).astype(int)
    df['target_away_clean_sheet'] = (df['home_goals'] == 0).astype(int)
    df['target_home_win_to_nil'] = ((df['home_goals'] > df['away_goals']) & (df['away_goals'] == 0)).astype(int)

    # Use the last 20% of matches for testing (like we did in the split)
    split_idx = int(len(df) * 0.8)
    test_df = df.iloc[split_idx:].copy()
    
    print(f"Evaluating Calibration on {len(test_df)} hold-out matches...\n")
    
    selector = MasterBetSelector()
    
    print(f"{'Market':<35} | {'Accuracy':<10} | {'Brier (Calibration)':<15}")
    print("-" * 65)
    
    overall_acc = []
    
    for target_name, target_col in TARGETS.items():
        if target_name not in selector.models:
            continue
            
        model = selector.models[target_name]
        
        # In our selector, input is pre-scaled but let's apply scaler directly
        X_test = test_df[FEATURES]
        X_scaled = selector.scaler.transform(X_test)
        y_true = test_df[target_col]
        
        # Predict
        preds = model.predict(X_scaled)
        
        # Predict Proba
        if len(model.classes_) == 2 and 1 in model.classes_:
            idx = list(model.classes_).index(1)
            probs = model.predict_proba(X_scaled)[:, idx]
            brier = brier_score_loss(y_true, probs)
            brier_str = f"{brier:.4f}"
        else:
            # Multi-class Log Loss proxy for 1X2
            probs = model.predict_proba(X_scaled)
            brier_str = "N/A (Multi)"
            brier = 0
            
        acc = accuracy_score(y_true, preds)
        overall_acc.append(acc)
        
        print(f"{target_name:<35} | {acc:<10.3f} | {brier_str:<15}")
        
    print("-" * 65)
    print(f"Average Accuracy across all markets: {sum(overall_acc)/len(overall_acc):.3f}")

if __name__ == '__main__':
    evaluate_models()
