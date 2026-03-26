import os
import pandas as pd
import numpy as np
import joblib
from datetime import datetime

from src.config import FEATURES_PATH, TARGETS, FEATURES
from src.models.trainer import train_best_model_for_target
from src.backtester import evaluate_market_result

def run_simulation():
    print(f"Loading features from {FEATURES_PATH}...")
    df = pd.read_csv(FEATURES_PATH, parse_dates=['date']).dropna(subset=FEATURES)
    
    # We create the targets matching train_all_models
    df['target_btts'] = df['btts'].astype(int)
    df['target_over_4_5_cards'] = (df['total_cards'] > 4.5).astype(int)
    df['target_over_2_5_goals'] = (df['total_goals'] > 2.5).astype(int)
    df['target_1x2'] = df['result_1x2'].astype(int)
    total_fouls = df['home_match_fouls'] + df['away_match_fouls']
    df['target_over_22_5_fouls'] = (total_fouls > 22.5).astype(int)
    df['target_dc_1X'] = (df['result_1x2'] >= 1).astype(int)
    df['target_dc_X2'] = (df['result_1x2'] <= 1).astype(int)
    df['target_home_over_0_5'] = (df['home_goals'] > 0.5).astype(int)
    df['target_away_over_0_5'] = (df['away_goals'] > 0.5).astype(int)
    
    df['target_under_2_5_goals'] = (df['total_goals'] <= 2.5).astype(int)
    df['target_btts_no'] = (df['btts'] == 0).astype(int)
    df['target_under_4_5_cards'] = (df['total_cards'] <= 4.5).astype(int)
    df['target_under_22_5_fouls'] = (total_fouls <= 22.5).astype(int)
    df['target_home_clean_sheet'] = (df['away_goals'] == 0).astype(int)
    df['target_away_clean_sheet'] = (df['home_goals'] == 0).astype(int)
    df['target_home_win_to_nil'] = ((df['home_goals'] > df['away_goals']) & (df['away_goals'] == 0)).astype(int)
    
    # Splitting logic: mid-season 25/26 is around Jan 1, 2026.
    split_date = pd.Timestamp('2026-01-01')
    
    # Needs to be sorted chronologically
    df = df.sort_values('date').reset_index(drop=True)
    
    train_df = df[df['date'] < split_date]
    test_df = df[(df['date'] >= split_date) & (df['season'].astype(str).str.contains('2025'))]
    
    if test_df.empty:
        # Fallback if season representation strings are different
        test_df = df[df['date'] >= split_date]

    print(f"Training on {len(train_df)} matches (up to {split_date.date()})")
    print(f"Testing on {len(test_df)} matches (from {split_date.date()})")

    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(train_df[FEATURES])
    
    models = {}
    for target_name, target_col in TARGETS.items():
        if target_col not in train_df.columns:
            continue
        print(f"\nTraining for: {target_name}")
        y_train = train_df[target_col]
        
        # Train and Calibrate model
        calibrated_model = train_best_model_for_target(X_train_scaled, y_train, target_name)
        models[target_name] = calibrated_model
        print(f"  [OK] Model for {target_name} is ready.")
        
    print("\nStarting Simulator on Testing Set...")
    # Best Params from strategy_optimization_results.csv (Flat, $50, conf>=0.57, odds>=1.1)
    CONFIDENCE_THRESHOLD = 0.57
    STAKE = 50.0
    MIN_ODDS = 1.1
    bankroll = 1000.0  # arbitrary starting bankroll
    
    bets_log = []
    
    for i, row in test_df.iterrows():
        match_dt = row['date']
        home = row['home_team']
        away = row['away_team']
        
        X_test = pd.DataFrame([row[FEATURES]])
        X_test_scaled = scaler.transform(X_test)
        
        predictions = []
        for target_name, model in models.items():
            try:
                if len(model.classes_) == 2 and 1 in model.classes_:
                    idx = list(model.classes_).index(1)
                    prob = model.predict_proba(X_test_scaled)[0][idx]
                    pick = 1
                else:
                    probs = model.predict_proba(X_test_scaled)[0]
                    max_idx = np.argmax(probs)
                    prob = probs[max_idx]
                    pick = model.classes_[max_idx]
                
                predictions.append({
                    "Market": target_name,
                    "Probability": prob,
                    "Pick": pick
                })
            except Exception as e:
                pass
                
        # Sort predictions by probability descending
        predictions.sort(key=lambda x: x['Probability'], reverse=True)
        
        # Look for the best bet meeting criteria
        top_bet = None
        bookie_odds = 0.0
        
        for p in predictions:
            prob = p['Probability']
            f_odds = 1.0 / prob if prob > 0 else 2.0
            simulated_odds = round(max(1.01, f_odds * 0.95), 2)
            
            if simulated_odds >= MIN_ODDS and prob >= CONFIDENCE_THRESHOLD:
                top_bet = p
                bookie_odds = simulated_odds
                break
                
        if top_bet is None:
            continue  # No bets met criteria for this match
            
        market = top_bet['Market']
        prob = top_bet['Probability']
        pick = top_bet['Pick']
        
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2 = row.get('result_1x2')
        
        if pd.isna(home_goals):
            continue # match not played
            
        won = evaluate_market_result(market, home_goals, away_goals, res_1x2, pick)
        
        stake = STAKE
        bankroll -= stake
        
        if won:
            payout = stake * bookie_odds
            bankroll += payout
            profit = payout - stake
            status = 'Won'
        else:
            profit = -stake
            status = 'Lost'
            
        bets_log.append({
            'Date': match_dt.date(),
            'Match': f"{home} vs {away}",
            'Market': market,
            'Confidence': f"{prob*100:.1f}%",
            'Pick': pick,
            'Simulated_Odds': bookie_odds,
            'Result': status,
            'Stake': stake,
            'Profit': profit,
            'Running_Bankroll': bankroll
        })

    print(f"\nSimulation Finished. Total bets placed: {len(bets_log)}")
    print(f"Final Bankroll: ${bankroll:.2f} (Net Profit: ${bankroll - 1000.0:.2f})")
    
    out_df = pd.DataFrame(bets_log)
    out_file = 'bets_2526_second_half.csv'
    out_df.to_csv(out_file, index=False)
    print(f"Bet log saved to {out_file}")

if __name__ == '__main__':
    run_simulation()
