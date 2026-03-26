import pandas as pd
import numpy as np
from src.config import FEATURES_PATH
from src.backtester import evaluate_market_result

def ai_decision_engine(row):
    """
    Simulates the AI (Antigravity) manually reviewing the match
    and deciding the best market to bet on, based on team knowledge and Elo.
    """
    home = row['home_team']
    away = row['away_team']
    h_elo = row['home_elo']
    a_elo = row['away_elo']
    
    top_teams = ['Arsenal', 'Manchester City', 'Liverpool']
    strong_teams = ['Chelsea', 'Newcastle United', 'Tottenham Hotspur', 'Aston Villa', 'Manchester Utd']
    
    elo_diff = h_elo - a_elo
    
    # 1. Clear Favorite Rule
    if elo_diff > 120 or (home in top_teams and away not in top_teams and away not in strong_teams):
        return {"Market": "1X2 (Match Winner)", "Pick": 1, "Confidence": "Manual AI (High)", "Reason": f"{home} is a clear favorite home"}
        
    if elo_diff < -120 or (away in top_teams and home not in top_teams and home not in strong_teams):
        return {"Market": "1X2 (Match Winner)", "Pick": 2, "Confidence": "Manual AI (High)", "Reason": f"{away} is a clear favorite away"}
        
    # 2. Both Teams are strong/attacking (Over 2.5 / BTTS)
    if (home in top_teams or home in strong_teams) and (away in top_teams or away in strong_teams):
        return {"Market": "BTTS (Both Teams To Score)", "Pick": 1, "Confidence": "Manual AI (Med)", "Reason": "Two strong teams usually score"}
        
    # 3. Close match but Home advantage
    if 30 <= elo_diff <= 120:
        return {"Market": "Double Chance 1X (Home or Draw)", "Pick": 1, "Confidence": "Manual AI (Med)", "Reason": "Home advantage in close match"}
        
    # 4. Close match but Away is slightly better
    if -120 <= elo_diff <= -30:
        return {"Market": "Double Chance X2 (Away or Draw)", "Pick": 1, "Confidence": "Manual AI (Med)", "Reason": "Away is better despite being visitor"}
        
    # 5. Very tight match, lower tier teams -> Under 2.5
    return {"Market": "Under 2.5 Goals", "Pick": 1, "Confidence": "Manual AI (Low)", "Reason": "Tight match between non-top teams"}


def run_ai_interventions():
    print(f"Loading features from {FEATURES_PATH}...")
    df = pd.read_csv(FEATURES_PATH, parse_dates=['date']).dropna(subset=['home_elo', 'away_elo'])
    
    test_df = df[(df['date'] >= '2026-01-01') & (df['season'].astype(str).str.contains('2025', na=False))]
    if test_df.empty:
        test_df = df[df['date'] >= '2026-01-01']
        
    test_df = test_df.sort_values('date').reset_index(drop=True)
    print(f"Total Matches to review manually via AI Engine: {len(test_df)}")
    
    bankroll = 2000000.0
    stake = 100000.0  # Flat stake in CLP
    bets_log = []
    
    wins = 0
    losses = 0
    
    for i, row in test_df.iterrows():
        decision = ai_decision_engine(row)
        if not decision: continue
        
        market = decision['Market']
        pick = decision['Pick']
        
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2 = row.get('result_1x2')
        
        if pd.isna(home_goals):
            continue
            
        won = evaluate_market_result(market, home_goals, away_goals, res_1x2, pick)
        
        # Simulate Odds (Fixed simulated odds for manual picks since we don't have predictions probabilities for them all)
        # We will assume conservative odds based on market
        if "Double Chance" in market:
            odds = 1.30
        elif market == "1X2 (Match Winner)":
            if abs(row['home_elo'] - row['away_elo']) > 150: odds = 1.25
            else: odds = 1.60
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
            'Date': row['date'].date(),
            'Match': f"{row['home_team']} vs {row['away_team']}",
            'AI_Market': market,
            'AI_Pick': pick,
            'AI_Reasoning': decision['Reason'],
            'Simulated_Odds': odds,
            'Result': status,
            'Stake': stake,
            'Profit': profit,
            'Running_Bankroll': bankroll
        })

    out_df = pd.DataFrame(bets_log)
    out_file = 'ai_manual_interventions.csv'
    out_df.to_csv(out_file, index=False)
    
    print(f"\nAI Intervention finished!")
    print(f"Total Bets: {wins+losses} | Wins: {wins} | Losses: {losses}")
    print(f"Win Rate: {(wins/(wins+losses))*100:.1f}%")
    print(f"Final Bankroll: ${bankroll:,.0f} CLP (Net Profit: ${bankroll - 2000000.0:,.0f} CLP)")
    print(f"Saved decisions to {out_file}")

if __name__ == '__main__':
    run_ai_interventions()
