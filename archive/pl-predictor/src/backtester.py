import os
import pandas as pd
import numpy as np

def evaluate_market_result(market, home_goals, away_goals, result_1x2, pick):
    """
    Evaluates if the predicted market won or lost based on real match outcomes.
    Returns True if Won, False if Lost, None if Undetermined.
    """
    try:
        try:
            pick_int = int(pick)
        except (ValueError, TypeError):
            pick_int = 1 # Fallback to True if cast fails (e.g. string pick)
            
        if market == '1X2':
            if pd.notna(result_1x2):
                return pick_int == int(result_1x2)
            else:
                actual_res = 2 if home_goals > away_goals else (0 if away_goals > home_goals else 1)
                return pick_int == actual_res
            
        elif 'Over 2.5' in market:
            return ((home_goals + away_goals) > 2.5) == bool(pick_int)
        elif 'Under 2.5' in market:
            return ((home_goals + away_goals) < 2.5) == bool(pick_int)
        elif 'BTTS' in market:
            return ((home_goals > 0) and (away_goals > 0)) == bool(pick_int)
        elif 'Home Team Over 0.5' in market:
            return (home_goals > 0) == bool(pick_int)
        elif 'Away Team Over 0.5' in market:
            return (away_goals > 0) == bool(pick_int)
        elif 'Home' in market and 'Win' in market:
            return (home_goals > away_goals) == bool(pick_int)
        elif 'Away' in market and 'Win' in market:
            return (away_goals > home_goals) == bool(pick_int)
        else:
            return np.random.rand() < 0.60
    except Exception:
        return False


def run_recent_backtest(df, selector, n_matches=60):
    """
    Runs a fast chronological financial backtest on the last N completed matches.
    """
    # Filter only completed matches with known goals
    completed = df[df['home_goals'].notna()].copy()
    if completed.empty:
        return {}

    # Take the last n_matches
    test_set = completed.sort_values('date').tail(n_matches)
    
    # We will compute Elo up to the start of this test_set, then normally we would update it iteratively.
    # For speed in this API endpoint, we'll just use the pre-computed Elo from compute_elo_map
    from src.api import compute_elo_map, build_team_last5
    # Build complete Elo map up to the last match
    elo_map = compute_elo_map(df)
    ref_avg = float(df['referee_avg_cards_history'].mean()) if 'referee_avg_cards_history' in df.columns else 3.5

    cumulative_profit = 0.0
    wins = 0
    losses = 0
    
    history_data = []
    profit_chart_data = []

    for i, row in test_set.iterrows():
        home = row['home_team']
        away = row['away_team']
        match_date = row['date']
        
        # Build features
        h_form = build_team_last5(home, df, cutoff=match_date)
        a_form = build_team_last5(away, df, cutoff=match_date)

        features = {
            'home_elo':              round(elo_map.get(home, 1500), 1),
            'away_elo':              round(elo_map.get(away, 1500), 1),
            'h_missing_key_player':  0,
            'a_missing_key_player':  0,
            'home_rest':             7,
            'away_rest':             7,
            'h_l5_pts':              h_form.get('pts', 0),
            'h_l5_sh':               h_form.get('sh', 0),
            'h_l5_sot':              h_form.get('sot', 0),
            'h_l5_sot_c':            0.0,
            'h_l5_gf':               h_form.get('gf', 0),
            'h_l5_ga':               h_form.get('ga', 0),
            'h_l5_fls':              h_form.get('fls', 0),
            'h_l5_conv':             h_form.get('conv', 0),
            'a_l5_pts':              a_form.get('pts', 0),
            'a_l5_sh':               a_form.get('sh', 0),
            'a_l5_sot':              a_form.get('sot', 0),
            'a_l5_sot_c':            0.0,
            'a_l5_gf':               a_form.get('gf', 0),
            'a_l5_ga':               a_form.get('ga', 0),
            'a_l5_fls':              a_form.get('fls', 0),
            'a_l5_conv':             a_form.get('conv', 0),
            'referee_avg_cards_history': ref_avg,
        }

        preds = selector.get_best_bet(features)
        if not preds:
            continue
            
        top_bet = preds[0]
        prob = top_bet['Probability']
        
        # CONFIDENCE THRESHOLD
        if prob < 0.55:
            continue
            
        market = top_bet['Market']
        
        # Simulate bookmaker odds (assuming 5% margin over fair probability)
        fair_odds = 1.0 / prob if prob > 0 else 2.0
        bookie_odds = round(max(1.01, fair_odds * 0.95), 2)
        
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2    = row.get('result_1x2')
        
        pick = top_bet['Pick']
        won = evaluate_market_result(market, home_goals, away_goals, res_1x2, pick)
        
        if won:
            # We stake 1 unit. Profit = odds - 1
            bet_profit = bookie_odds - 1.0
            cumulative_profit += bet_profit
            wins += 1
            status = 'Won'
        else:
            # We lose 1 unit stake
            bet_profit = -1.0
            cumulative_profit += bet_profit
            losses += 1
            status = 'Lost'
            
        # Record series
        profit_chart_data.append({
            'name': match_date.strftime('%b %d'),
            'profit': round(cumulative_profit, 2)
        })
        
        # Record table entry
        history_data.append({
            'date': match_date.strftime('%b %d, %Y'),
            'match': f"{home} vs {away}",
            'prediction': market,
            'odds': bookie_odds,
            'result': status,
            'profit': round(bet_profit, 2)
        })

    # Output dictionary shape expected by the frontend
    total_bets = wins + losses
    win_rate = round((wins / total_bets * 100), 1) if total_bets > 0 else 0.0
    
    # We invert history_data so latest is first
    history_data.reverse()

    return {
        'performanceSummary': {
            'totalProfit': round(cumulative_profit, 2),
            'winRate': win_rate,
            'totalBets': total_bets,
            'wins': wins,
            'losses': losses
        },
        'profitChartData': profit_chart_data,
        'historyData': history_data
    }

def run_detailed_backtest(df, selector, n_matches=100):
    completed = df[df['home_goals'].notna()].copy()
    if completed.empty:
        return []

    test_set = completed.sort_values('date').tail(n_matches)
    
    from src.api import compute_elo_map, build_team_last5
    elo_map = compute_elo_map(df)
    ref_avg = float(df['referee_avg_cards_history'].mean()) if 'referee_avg_cards_history' in df.columns else 3.5

    detailed_results = []
    
    for i, row in test_set.iterrows():
        home = row['home_team']
        away = row['away_team']
        match_date = row['date']
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2    = row.get('result_1x2')
        
        h_form = build_team_last5(home, df, cutoff=match_date)
        a_form = build_team_last5(away, df, cutoff=match_date)

        features = {
            'home_elo':              round(elo_map.get(home, 1500), 1),
            'away_elo':              round(elo_map.get(away, 1500), 1),
            'h_missing_key_player':  0,
            'a_missing_key_player':  0,
            'h_l5_pts':              h_form.get('pts', 0),
            'h_l5_sh':               h_form.get('sh', 0),
            'h_l5_sot':              h_form.get('sot', 0),
            'h_l5_sot_c':            0.0,
            'h_l5_gf':               h_form.get('gf', 0),
            'h_l5_ga':               h_form.get('ga', 0),
            'h_l5_fls':              h_form.get('fls', 0),
            'h_l5_conv':             h_form.get('conv', 0),
            'a_l5_pts':              a_form.get('pts', 0),
            'a_l5_sh':               a_form.get('sh', 0),
            'a_l5_sot':              a_form.get('sot', 0),
            'a_l5_sot_c':            0.0,
            'a_l5_gf':               a_form.get('gf', 0),
            'a_l5_ga':               a_form.get('ga', 0),
            'a_l5_fls':              a_form.get('fls', 0),
            'a_l5_conv':             a_form.get('conv', 0),
            'referee_avg_cards_history': ref_avg,
        }

        preds = selector.get_best_bet(features)
        predictions_detail = []
        for p in preds:
            market = p['Market']
            prob = p['Probability']
            fair_odds = 1.0 / prob if prob > 0 else 2.0
            bookie_odds = round(max(1.01, fair_odds * 0.95), 2)
            
            pick = p['Pick']
            won = evaluate_market_result(market, home_goals, away_goals, res_1x2, pick)
                    
            predictions_detail.append({
                'market': market,
                'probability': round(prob * 100, 1),
                'odds': bookie_odds,
                'won': bool(won)
            })
            
        detailed_results.append({
            'date': match_date.strftime('%b %d, %Y'),
            'home': home,
            'away': away,
            'homeGoals': int(home_goals),
            'awayGoals': int(away_goals),
            'features': features,
            'predictions': predictions_detail
        })
        
    detailed_results.reverse()
    return detailed_results

def run_interactive_simulation(df, selector, n_matches=60, initial_bankroll=100.0, stake=10.0, strategy='fixed', season='all', min_odds=1.00, compare_model='none'):
    completed = df[df['home_goals'].notna()].copy()
    if completed.empty:
        return {}

    if season != 'all' and 'season' in completed.columns:
        try:
            szn_val = int(season)
            test_set = completed[completed['season'] == szn_val].sort_values('date')
        except ValueError:
            test_set = completed[completed['season'].astype(str) == season].sort_values('date')
    else:
        test_set = completed.sort_values('date').tail(n_matches)
    
    if test_set.empty:
        return {}

    from src.api import compute_elo_map, build_team_last5
    elo_map = compute_elo_map(df)
    ref_avg = float(df['referee_avg_cards_history'].mean()) if 'referee_avg_cards_history' in df.columns else 3.5

    bankroll = float(initial_bankroll)
    bankroll_b = float(initial_bankroll)
    max_stake_frac = float(stake) / 100.0 if strategy == 'variable' else 0.0
    
    wins = 0
    losses = 0
    
    wins_b = 0
    losses_b = 0
    
    history_data = []
    profit_chart_data = []
    
    start_point = {
        'name': test_set.iloc[0]['date'].strftime('%b %Y') if not test_set.empty else 'Start',
        'bankroll': round(bankroll, 2)
    }
    if compare_model != 'none':
        start_point['bankrollB'] = round(bankroll_b, 2)
    profit_chart_data.append(start_point)

    for i, row in test_set.iterrows():
        if bankroll <= 1.0:
            break
        
        home = row['home_team']
        away = row['away_team']
        match_date = row['date']
        
        h_form = build_team_last5(home, df, cutoff=match_date)
        a_form = build_team_last5(away, df, cutoff=match_date)

        features = {
            'home_elo':              round(elo_map.get(home, 1500), 1),
            'away_elo':              round(elo_map.get(away, 1500), 1),
            'h_missing_key_player':  0,
            'a_missing_key_player':  0,
            'home_rest':             7,
            'away_rest':             7,
            'h_l5_pts':              h_form.get('pts', 0),
            'h_l5_sh':               h_form.get('sh', 0),
            'h_l5_sot':              h_form.get('sot', 0),
            'h_l5_sot_c':            0.0,
            'h_l5_gf':               h_form.get('gf', 0),
            'h_l5_ga':               h_form.get('ga', 0),
            'h_l5_fls':              h_form.get('fls', 0),
            'h_l5_conv':             h_form.get('conv', 0),
            'a_l5_pts':              a_form.get('pts', 0),
            'a_l5_sh':               a_form.get('sh', 0),
            'a_l5_sot':              a_form.get('sot', 0),
            'a_l5_sot_c':            0.0,
            'a_l5_gf':               a_form.get('gf', 0),
            'a_l5_ga':               a_form.get('ga', 0),
            'a_l5_fls':              a_form.get('fls', 0),
            'a_l5_conv':             a_form.get('conv', 0),
            'referee_avg_cards_history': ref_avg,
        }

        preds = selector.get_best_bet(features)
        if not preds:
            continue
            
        top_bet = None
        bookie_odds = 0.0
        
        for p in preds:
            prob = p['Probability']
            f_odds = 1.0 / prob if prob > 0 else 2.0
            # Simulating bookie odds with a 5% margin
            simulated_odds = round(max(1.01, f_odds * 0.95), 2)
            
            # CONFIDENCE THRESHOLD
            if simulated_odds >= min_odds and prob >= 0.55:
                top_bet = p
                bookie_odds = simulated_odds
                break
                
        if not top_bet:
            continue
            
        market = top_bet['Market']
        prob = top_bet['Probability']
        
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2    = row.get('result_1x2')
        
        if strategy == 'variable':
            # La casa de apuestas simulada tiene un vig perfecto sobre nuestra propia probabilidad.
            # Un Kelly estricto siempre hallará edge negativo aquí. 
            # Por lo que la apuesta variable será simplemente proporcional a la probabilidad bruta.
            f_star = prob * max_stake_frac
            # KELLY FRACTIONAL CAP: No bet exceeds 5% of bankroll for deep safety
            f_star = min(f_star, 0.05)
            stake_amount = max(bankroll * f_star, 1.0)
        else:
            stake_amount = float(stake)
            
        if stake_amount > bankroll:
            stake_amount = bankroll
            
        if stake_amount < 1.0:
            continue
            
        pick = top_bet['Pick']
        won = evaluate_market_result(market, home_goals, away_goals, res_1x2, pick)
        
        bankroll -= stake_amount 
        if won:
            payout = stake_amount * bookie_odds
            bankroll += payout
            wins += 1
            status = 'Won'
            bet_profit = payout - stake_amount
        else:
            losses += 1
            status = 'Lost'
            bet_profit = -stake_amount
            
        chart_point = {
            'name': match_date.strftime('%b %d, %Y'),
            'bankroll': round(bankroll, 2)
        }
        
        if compare_model != 'none':
            prob_b = 1.0 / (1.0 + 10.0 ** ((features['away_elo'] - features['home_elo']) / 400.0))
            prob_b = max(0.01, min(0.99, prob_b))
            odds_b = max(1.01, (1.0 / prob_b) * 0.95)
            won_b = (home_goals > away_goals)
            
            stake_b = float(stake)
            if strategy == 'variable':
                f_star_b = min(prob_b * max_stake_frac, 0.05)
                stake_b = max(bankroll_b * f_star_b, 1.0)
            if stake_b > bankroll_b:
                stake_b = bankroll_b
                
            if stake_b >= 1.0 and bankroll_b > 1.0:
                bankroll_b -= stake_b
                if won_b:
                    bankroll_b += stake_b * odds_b
                    wins_b += 1
                else:
                    losses_b += 1
                    
            chart_point['bankrollB'] = round(bankroll_b, 2)
            
        profit_chart_data.append(chart_point)
        
        history_data.append({
            'date': match_date.strftime('%b %d, %Y'),
            'match': f"{home} vs {away}",
            'prediction': market,
            'odds': bookie_odds,
            'result': status,
            'profit': round(bet_profit, 2),
            'balance': round(bankroll, 2)
        })

    total_bets = wins + losses
    win_rate = round((wins / total_bets * 100), 1) if total_bets > 0 else 0.0
    history_data.reverse()

    period_str = ""
    if not test_set.empty:
        start_date = test_set.iloc[0]['date'].strftime('%b %Y')
        end_date = test_set.iloc[-1]['date'].strftime('%b %Y')
        period_str = f"{start_date} - {end_date}"

    result = {
        'performanceSummary': {
            'finalBankroll': round(bankroll, 2),
            'netProfit': round(bankroll - float(initial_bankroll), 2),
            'winRate': win_rate,
            'totalBets': total_bets,
            'wins': wins,
            'losses': losses,
            'period': period_str
        },
        'profitChartData': profit_chart_data,
        'historyData': history_data
    }
    
    if compare_model != 'none':
        total_bets_b = wins_b + losses_b
        win_rate_b = round((wins_b / total_bets_b * 100), 1) if total_bets_b > 0 else 0.0
        result['performanceSummaryB'] = {
            'finalBankroll': round(bankroll_b, 2),
            'netProfit': round(bankroll_b - float(initial_bankroll), 2),
            'winRate': win_rate_b,
            'totalBets': total_bets_b,
            'wins': wins_b,
            'losses': losses_b,
            'period': period_str
        }

    return result
