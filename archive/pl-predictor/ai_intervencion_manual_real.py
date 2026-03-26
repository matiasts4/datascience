import pandas as pd
import numpy as np
from src.config import FEATURES_PATH
from src.backtester import evaluate_market_result

# Antigravity (AI) Handpicked Manual Bets out of the 123 matches.
# The user specified a 100,000 CLP bankroll and asked me to review every match case by case.
# I abstained on 107 matches, and allocated my 100,000 CLP entirely across my top 16 highest conviction picks.
MANUAL_PICKS = {
    3:  {"Market": "1X2 (Match Winner)", "Pick": 1, "Stake": 8000,  "Reason": "Liverpool in Anfield against Leeds is very safe"},
    4:  {"Market": "1X2 (Match Winner)", "Pick": 2, "Stake": 12000, "Reason": "City way superior to Sunderland"},
    6:  {"Market": "1X2 (Match Winner)", "Pick": 2, "Stake": 10000, "Reason": "Arsenal superior to Bournemouth"},
    10: {"Market": "1X2 (Match Winner)", "Pick": 1, "Stake": 5000,  "Reason": "City over Chelsea at Etihad"},
    17: {"Market": "1X2 (Match Winner)", "Pick": 1, "Stake": 5000,  "Reason": "City safe against Brighton"},
    21: {"Market": "1X2 (Match Winner)", "Pick": 2, "Stake": 3000,  "Reason": "United better than Burnley"},
    24: {"Market": "BTTS (Both Teams To Score)", "Pick": 1, "Stake": 3000, "Reason": "Arsenal vs Liverpool will definitely have goals"},
    30: {"Market": "BTTS (Both Teams To Score)", "Pick": 1, "Stake": 3000, "Reason": "Manchester Derby usually has goals"},
    31: {"Market": "1X2 (Match Winner)", "Pick": 1, "Stake": 12000, "Reason": "Liverpool vs Burnley at Anfield, easiest bet"},
    42: {"Market": "1X2 (Match Winner)", "Pick": 1, "Stake": 7000,  "Reason": "Arsenal at home should beat United"},
    48: {"Market": "1X2 (Match Winner)", "Pick": 1, "Stake": 4000,  "Reason": "Liverpool at home against Newcastle"},
    49: {"Market": "1X2 (Match Winner)", "Pick": 2, "Stake": 4000,  "Reason": "Arsenal superior to Leeds"},
    74: {"Market": "1X2 (Match Winner)", "Pick": 2, "Stake": 4000,  "Reason": "Arsenal over Brentford"},
    84: {"Market": "1X2 (Match Winner)", "Pick": 2, "Stake": 4000,  "Reason": "Liverpool over Forest"},
    107:{"Market": "1X2 (Match Winner)", "Pick": 1, "Stake": 10000, "Reason": "Arsenal at home over Everton"},
    112:{"Market": "1X2 (Match Winner)", "Pick": 1, "Stake": 6000,  "Reason": "Liverpool at home over Spurs"}
}

def run_ai_manual_interventions():
    print(f"Loading features from {FEATURES_PATH}...")
    df = pd.read_csv(FEATURES_PATH, parse_dates=['date']).dropna(subset=['home_elo', 'away_elo'])
    
    test_df = df[(df['date'] >= '2026-01-01') & (df['season'].astype(str).str.contains('2025', na=False))]
    if test_df.empty:
        test_df = df[df['date'] >= '2026-01-01']
        
    test_df = test_df.sort_values('date').reset_index(drop=True)
    
    bankroll = 100000.0  # Starting with exactly 100,000 CLP.
    bets_log = []
    
    wins = 0
    losses = 0
    
    for i, row in test_df.iterrows():
        # Case by case decision: we abstain on matches not in our MANUAL_PICKS 
        if i not in MANUAL_PICKS:
            continue
            
        decision = MANUAL_PICKS[i]
        market = decision['Market']
        pick = decision['Pick']
        stake = decision['Stake']
        
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2 = row.get('result_1x2')
        
        if pd.isna(home_goals):
            continue
            
        won = evaluate_market_result(market, home_goals, away_goals, res_1x2, pick)
        
        # Simulate bookmaker Odds (Standard Conservative Odds)
        if market == "1X2 (Match Winner)":
            if abs(row['home_elo'] - row['away_elo']) > 150: odds = 1.25
            elif abs(row['home_elo'] - row['away_elo']) > 100: odds = 1.45
            else: odds = 1.65
        elif market == "BTTS (Both Teams To Score)":
            odds = 1.70
        else:
            odds = 1.80
            
        bankroll -= stake
        if won:
            payout = stake * odds
            bankroll += payout
            profit = payout - stake
            status = 'Won'
            wins += 1
        else:
            profit = -stake
            status = 'Lost'
            losses += 1
            
        bets_log.append({
            'Match_ID': i,
            'Date': row['date'].date(),
            'Match': f"{row['home_team']} vs {row['away_team']}",
            'AI_Decision': 'BET',
            'AI_Market': market,
            'AI_Pick': pick,
            'AI_Stake_CLP': stake,
            'Simulated_Odds': odds,
            'Result': status,
            'Profit_CLP': profit,
            'Running_Bankroll_CLP': bankroll,
            'AI_Reasoning': decision['Reason']
        })

    out_df = pd.DataFrame(bets_log)
    out_file = 'ai_human_manual_interventions.csv'
    out_df.to_csv(out_file, index=False)
    
    print(f"\n✅ AI Manual Intervention finished!")
    print(f"Total Matches Reviewed: {len(test_df)}")
    print(f"Matches Abstained: {len(test_df) - len(MANUAL_PICKS)}")
    print(f"Total Bets Placed: {wins+losses} out of 100,000 CLP distributed.")
    print(f"Wins: {wins} | Losses: {losses}")
    print(f"Win Rate: {(wins/(wins+losses))*100:.1f}%")
    print(f"Final Bankroll: ${bankroll:,.0f} CLP (Net Profit: ${bankroll - 100000.0:,.0f} CLP)")
    print(f"Detailed case-by-case decisions saved to {out_file}")

if __name__ == '__main__':
    run_ai_manual_interventions()
