import pandas as pd
import numpy as np
from src.config import FEATURES_PATH, FEATURES
from src.models.selector import MasterBetSelector
from src.backtester import evaluate_market_result
import warnings

warnings.filterwarnings('ignore')

def run_fast_test():
    print("Loading test data...")
    df = pd.read_csv(FEATURES_PATH).dropna()
    split_idx = int(len(df) * 0.8)
    test_df = df.iloc[split_idx:].copy().reset_index(drop=True)
    
    selector = MasterBetSelector()
    
    print(f"Testing on {len(test_df)} matches (Vectorized)...")
    
    X_scaled = selector.scaler.transform(test_df[FEATURES])
    
    # Store all probas
    all_preds = np.zeros((len(test_df), len(selector.models)))
    market_names = list(selector.models.keys())
    
    for i, (market, model) in enumerate(selector.models.items()):
        if len(model.classes_) == 2 and 1 in model.classes_:
            idx = list(model.classes_).index(1)
            all_preds[:, i] = model.predict_proba(X_scaled)[:, idx]
        else:
            all_preds[:, i] = np.max(model.predict_proba(X_scaled), axis=1)
            
    # For each match, find the index of the highest probability
    best_market_idx = np.argmax(all_preds, axis=1)
    
    hits = 0
    market_stats = {m: {'hits': 0, 'total': 0} for m in market_names}
    
    for i, row in test_df.iterrows():
        chosen_market = market_names[best_market_idx[i]]
        hg = row['home_goals']
        ag = row['away_goals']
        r1x2 = row.get('result_1x2')
        won = evaluate_market_result(chosen_market, hg, ag, r1x2)
        
        if chosen_market == '1X2':
            if row['home_elo'] >= row['away_elo']:
                won = (hg > ag)
            else:
                won = (ag > hg)
                
        if won:
            hits += 1
            market_stats[chosen_market]['hits'] += 1
        market_stats[chosen_market]['total'] += 1
        
    print(f"\n--- FAST RESULTS OF HIGHEST ABSOLUTE PROBABILITY STRATEGY ---")
    print(f"Total Matches: {len(test_df)}")
    print(f"Overall Accuracy: {hits / len(test_df) * 100:.2f}%\n")
    
    print("--- BREAKDOWN OF TOP PICKS CHOSEN BY THE SELECTOR ---")
    for m in sorted(market_names, key=lambda x: market_stats[x]['total'], reverse=True):
        stats = market_stats[m]
        if stats['total'] > 0:
            acc = stats['hits'] / stats['total'] * 100
            print(f"{m:<30} | Chosen: {stats['total']:<4} times | Accuracy: {acc:.1f}%")

if __name__ == '__main__':
    run_fast_test()
