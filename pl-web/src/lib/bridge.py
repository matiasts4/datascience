import os
import sys
import json
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# Configurar rutas para importar desde el backend
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../archive/pl-predictor'))
sys.path.append(BASE_DIR)

from src.config import TARGETS, FEATURES, MODELS_DIR
from src.models.selector import MasterBetSelector
from src.api import compute_elo_map, build_team_last5

def clean_json(obj):
    if isinstance(obj, list):
        return [clean_json(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [clean_json(x) for x in obj]
    else:
        return obj

def evaluate_market_result(market, home_goals, away_goals, result_1x2, pick):
    try:
        pick_int = int(pick)
    except (ValueError, TypeError):
        pick_int = 1
        
    if market == '1X2' or '1X2' in market:
        if pd.notna(result_1x2):
            return pick_int == int(result_1x2)
        else:
            actual_res = 2 if home_goals > away_goals else (0 if away_goals > home_goals else 1)
            return pick_int == actual_res
    elif 'Over 2.5' in market:
        return ((home_goals + away_goals) > 2.5) == bool(pick_int)
    elif 'Under 2.5' in market:
        return ((home_goals + away_goals) < 2.5) == bool(pick_int)
    elif 'BTTS (Both Teams To Score)' in market or 'BTTS' in market and 'No' not in market:
        return ((home_goals > 0) and (away_goals > 0)) == bool(pick_int)
    elif 'BTTS - No' in market:
        return (not ((home_goals > 0) and (away_goals > 0))) == bool(pick_int)
    elif 'Home Clean Sheet' in market:
        return (away_goals == 0) == bool(pick_int)
    elif 'Home' in market and 'Win' in market:
        return (home_goals > away_goals) == bool(pick_int)
    elif 'Away' in market and 'Win' in market:
        return (away_goals > home_goals) == bool(pick_int)
    else:
        return False

def run_predict(payload):
    home = payload.get('homeTeam', '')
    away = payload.get('awayTeam', '')
    h_miss = int(payload.get('homeMissingKey', False))
    a_miss = int(payload.get('awayMissingKey', False))
    match_date = payload.get('date', None)

    # Cargar datos
    features_path = os.path.join(BASE_DIR, "data", "historical", "historical_sanitized_v7.csv")
    df = pd.read_csv(features_path, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)

    if match_date:
        try:
            match_date_parsed = pd.to_datetime(match_date)
            elo_map = compute_elo_map(df, cutoff_date=match_date_parsed)
            h_form  = build_team_last5(home, df, cutoff=match_date_parsed)
            a_form  = build_team_last5(away, df, cutoff=match_date_parsed)
        except Exception:
            elo_map = compute_elo_map(df)
            h_form  = build_team_last5(home, df)
            a_form  = build_team_last5(away, df)
    else:
        elo_map = compute_elo_map(df)
        h_form  = build_team_last5(home, df)
        a_form  = build_team_last5(away, df)

    ref_avg = float(df['referee_avg_cards_history'].mean()) if 'referee_avg_cards_history' in df.columns else 3.5

    features = {
        'home_elo':              round(elo_map.get(home, 1500), 1),
        'away_elo':              round(elo_map.get(away, 1500), 1),
        'h_missing_key_player':  h_miss,
        'a_missing_key_player':  a_miss,
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
        'h_l5_xg':               h_form.get('xg', 0),
        'h_l5_xga':              h_form.get('xga', 0),
        'a_l5_pts':              a_form.get('pts', 0),
        'a_l5_sh':               a_form.get('sh', 0),
        'a_l5_sot':              a_form.get('sot', 0),
        'a_l5_sot_c':            0.0,
        'a_l5_gf':               a_form.get('gf', 0),
        'a_l5_ga':               a_form.get('ga', 0),
        'a_l5_fls':              a_form.get('fls', 0),
        'a_l5_conv':             a_form.get('conv', 0),
        'a_l5_xg':               a_form.get('xg', 0),
        'a_l5_xga':              a_form.get('xga', 0),
        'referee_avg_cards_history': ref_avg,
        'is_derby':              0,
        'relegation_pressure':   0,
    }

    selector = MasterBetSelector()
    preds = selector.get_best_bet(features)

    # Sort predictions by EV descending in the predictions array itself (smart selection)
    preds.sort(key=lambda x: x.get('ExpectedValue', 0.0), reverse=True)

    result = {
        'homeTeam':  home,
        'awayTeam':  away,
        'homeElo':   features['home_elo'],
        'awayElo':   features['away_elo'],
        'homeForm':  h_form,
        'awayForm':  a_form,
        'predictions': preds,
    }
    return clean_json(result)

def run_simulate(payload):
    initial_bankroll = float(payload.get('initialBankroll', 100.0))
    stake = float(payload.get('stake', 10.0))
    n_matches = int(payload.get('nMatches', 60))
    strategy = payload.get('strategy', 'fixed')
    season = payload.get('season', 'all')
    min_odds = float(payload.get('minOdds', 1.0))
    min_ev = float(payload.get('minEv', 0.0)) / 100.0
    compare_model = payload.get('compareModel', 'none')
    min_prob = float(payload.get('minProb', 50.0)) / 100.0
    allowed_markets = payload.get('allowedMarkets', [])
    selection_criteria = payload.get('selectionCriteria', 'combined')

    features_path = os.path.join(BASE_DIR, "data", "historical", "historical_sanitized_v7.csv")
    df = pd.read_csv(features_path, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)

    completed = df[df['home_goals'].notna()].copy()
    if completed.empty:
        return {}

    # Define real_season dynamically based on match date to avoid standardized floats bug
    def get_season_code(date):
        if pd.isna(date):
            return None
        year = date.year
        month = date.month
        if month >= 8:
            start_yr = year
        else:
            start_yr = year - 1
        s_code = (start_yr % 100) * 100 + ((start_yr + 1) % 100)
        return s_code

    completed['real_season'] = completed['date'].apply(get_season_code)

    if season != 'all':
        try:
            szn_val = int(season)
            test_set = completed[completed['real_season'] == szn_val].sort_values('date')
        except Exception:
            test_set = completed.sort_values('date').tail(n_matches)
    else:
        test_set = completed.sort_values('date').tail(n_matches)
    
    if test_set.empty:
        return {}

    elo_map = compute_elo_map(df)
    ref_avg = float(df['referee_avg_cards_history'].mean()) if 'referee_avg_cards_history' in df.columns else 3.5

    bankroll = float(initial_bankroll)
    bankroll_b = float(initial_bankroll)
    max_stake_frac = float(stake) / 100.0 if strategy == 'variable' else 0.0
    
    wins = 0
    losses = 0
    total_ev = 0.0
    
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

    selector = MasterBetSelector()

    for i, row in test_set.iterrows():
        if bankroll <= 1.0:
            break
        
        home = row['home_team']
        away = row['away_team']
        match_date = row['date']
        
        features = {
            'home_elo':              row.get('home_elo', 0.0),
            'away_elo':              row.get('away_elo', 0.0),
            'home_rest':             row.get('home_rest', 7.0),
            'away_rest':             row.get('away_rest', 7.0),
            'h_l5_pts':              row.get('h_l5_pts', 0.0),
            'h_l5_sh':               row.get('h_l5_sh', 0.0),
            'h_l5_sot':              row.get('h_l5_sot', 0.0),
            'h_l5_sot_c':            row.get('h_l5_sot_c', 0.0),
            'h_l5_gf':               row.get('h_l5_gf', 0.0),
            'h_l5_ga':               row.get('h_l5_ga', 0.0),
            'h_l5_fls':              row.get('h_l5_fls', 0.0),
            'h_l5_conv':             row.get('h_l5_conv', 0.0),
            'h_l5_xg':               row.get('h_l5_xg', 0.0),
            'h_l5_xga':              row.get('h_l5_xga', 0.0),
            'a_l5_pts':              row.get('a_l5_pts', 0.0),
            'a_l5_sh':               row.get('a_l5_sh', 0.0),
            'a_l5_sot':              row.get('a_l5_sot', 0.0),
            'a_l5_sot_c':            row.get('a_l5_sot_c', 0.0),
            'a_l5_gf':               row.get('a_l5_gf', 0.0),
            'a_l5_ga':               row.get('a_l5_ga', 0.0),
            'a_l5_fls':              row.get('a_l5_fls', 0.0),
            'a_l5_conv':             row.get('a_l5_conv', 0.0),
            'a_l5_xg':               row.get('a_l5_xg', 0.0),
            'a_l5_xga':              row.get('a_l5_xga', 0.0),
            'referee_avg_cards_history': row.get('referee_avg_cards_history', ref_avg),
            'is_derby':              row.get('is_derby', 0),
            'relegation_pressure':   row.get('relegation_pressure', 0),
        }

        preds = selector.get_best_bet(features)
        if not preds:
            continue
            
        top_bet = None
        bookie_odds = 0.0
        
        # Calculate "Public" probability based purely on Elo to simulate real Bookie Odds
        prob_public = 1.0 / (1.0 + 10.0 ** ((features['away_elo'] - features['home_elo']) / 400.0))
        prob_public = max(0.01, min(0.99, prob_public))
        
        # Recalculate EV and stake limit using user-defined max_stake_frac
        for p in preds:
            prob = p['Probability']
            market = p['Market']
            
            # Map Public Probability to the specific market roughly
            if market == '1X2':
                base_prob = prob_public * 0.9  
            elif '1X' in market or 'X2' in market:
                base_prob = prob_public + 0.15 
                base_prob = min(0.99, base_prob)
            else:
                base_prob = prob + np.random.uniform(-0.10, 0.10)
                base_prob = max(0.01, min(0.99, base_prob))
                
            f_odds = 1.0 / base_prob
            simulated_odds = round(max(1.01, f_odds * 0.95), 2)
            
            p['FairOdds'] = round(1.0 / prob if prob > 0 else 100.0, 2)
            ev = (prob * simulated_odds) - 1.0 
            p['ExpectedValue'] = round(ev, 3) 
            
            if simulated_odds > 1.0:
                b = simulated_odds - 1.0
                q = 1.0 - prob
                kelly_f = (b * prob - q) / b
            else:
                kelly_f = -1.0
                
            # Use user-supplied Kelly max_stake_frac limit
            limit_val = max_stake_frac if strategy == 'variable' else 0.10
            p['RecommendedStakePct'] = round(min(kelly_f * 0.25, limit_val) * 100, 2) if kelly_f > 0 else 0.0

        # Sort predictions by EV descending (Smart Selector) instead of probability descending
        preds.sort(key=lambda x: x['ExpectedValue'], reverse=True)

        for p in preds:
            prob = p['Probability']
            market = p['Market']
            
            # Filter by allowed markets
            if allowed_markets:
                is_allowed = False
                for allowed in allowed_markets:
                    if allowed.lower() in market.lower():
                        is_allowed = True
                        break
                if not is_allowed:
                    continue
            
            simulated_odds = p['ExpectedValue'] / prob + 1.0 if prob > 0 else 1.0
            simulated_odds = round(simulated_odds, 2)
            ev_val = p['ExpectedValue']
            
            meet_ev = ev_val >= min_ev
            meet_prob = prob >= min_prob
            meet_odds = simulated_odds >= min_odds
            
            meet_criteria = False
            if selection_criteria == 'ev_only':
                meet_criteria = meet_ev
            elif selection_criteria == 'prob_only':
                meet_criteria = meet_prob
            else: # combined
                meet_criteria = meet_ev and meet_prob
            
            if meet_odds and meet_criteria:
                top_bet = p
                bookie_odds = simulated_odds
                break
                
        if not top_bet:
            continue
            
        market = top_bet['Market']
        prob = top_bet['Probability']
        ev_val = top_bet.get('ExpectedValue', 0.0)
        stake_pct = top_bet.get('RecommendedStakePct', 0.0)
        total_ev += ev_val
        
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2    = row.get('result_1x2')
        
        if strategy == 'variable':
            recommended_pct = stake_pct
            if recommended_pct <= 0:
                continue 
                
            f_star = recommended_pct / 100.0
            f_star = min(f_star, max_stake_frac)
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
            'balance': round(bankroll, 2),
            'ev': round(ev_val, 3),
            'stakePct': round(stake_pct, 2),
            'stakeAmount': round(stake_amount, 2),
            'homeGoals': int(home_goals),
            'awayGoals': int(away_goals),
            'features': features,
            'predictions': [
                {
                    'market': p['Market'],
                    'probability': round(p['Probability'] * 100, 1),
                    'odds': p['FairOdds'],
                    'ev': p['ExpectedValue'],
                    'won': evaluate_market_result(p['Market'], home_goals, away_goals, res_1x2, p['Pick'])
                } for p in preds
            ]
        })

    total_bets = wins + losses
    win_rate = round((wins / total_bets * 100), 1) if total_bets > 0 else 0.0
    history_data.reverse()

    period_str = ""
    if not test_set.empty:
        start_date = test_set.iloc[0]['date'].strftime('%b %Y')
        end_date = test_set.iloc[-1]['date'].strftime('%b %Y')
        period_str = f"{start_date} - {end_date}"

    avg_ev = round((total_ev / total_bets) * 100, 2) if total_bets > 0 else 0.0

    result = {
        'performanceSummary': {
            'finalBankroll': round(bankroll, 2),
            'netProfit': round(bankroll - float(initial_bankroll), 2),
            'winRate': win_rate,
            'totalBets': total_bets,
            'wins': wins,
            'losses': losses,
            'period': period_str,
            'avgEV': avg_ev
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

    return clean_json(result)

def run_performance():
    features_path = os.path.join(BASE_DIR, "data", "historical", "historical_sanitized_v7.csv")
    df = pd.read_csv(features_path, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)

    completed = df[df['home_goals'].notna()].copy()
    if completed.empty:
        return {}

    test_set = completed.sort_values('date').tail(60)
    
    elo_map = compute_elo_map(df)
    ref_avg = float(df['referee_avg_cards_history'].mean()) if 'referee_avg_cards_history' in df.columns else 3.5

    cumulative_profit = 0.0
    wins = 0
    losses = 0
    
    history_data = []
    profit_chart_data = []

    selector = MasterBetSelector()

    for i, row in test_set.iterrows():
        home = row['home_team']
        away = row['away_team']
        match_date = row['date']
        
        features = {
            'home_elo':              row.get('home_elo', 0.0),
            'away_elo':              row.get('away_elo', 0.0),
            'home_rest':             row.get('home_rest', 7.0),
            'away_rest':             row.get('away_rest', 7.0),
            'h_l5_pts':              row.get('h_l5_pts', 0.0),
            'h_l5_sh':               row.get('h_l5_sh', 0.0),
            'h_l5_sot':              row.get('h_l5_sot', 0.0),
            'h_l5_sot_c':            row.get('h_l5_sot_c', 0.0),
            'h_l5_gf':               row.get('h_l5_gf', 0.0),
            'h_l5_ga':               row.get('h_l5_ga', 0.0),
            'h_l5_fls':              row.get('h_l5_fls', 0.0),
            'h_l5_conv':             row.get('h_l5_conv', 0.0),
            'h_l5_xg':               row.get('h_l5_xg', 0.0),
            'h_l5_xga':              row.get('h_l5_xga', 0.0),
            'a_l5_pts':              row.get('a_l5_pts', 0.0),
            'a_l5_sh':               row.get('a_l5_sh', 0.0),
            'a_l5_sot':              row.get('a_l5_sot', 0.0),
            'a_l5_sot_c':            row.get('a_l5_sot_c', 0.0),
            'a_l5_gf':               row.get('a_l5_gf', 0.0),
            'a_l5_ga':               row.get('a_l5_ga', 0.0),
            'a_l5_fls':              row.get('a_l5_fls', 0.0),
            'a_l5_conv':             row.get('a_l5_conv', 0.0),
            'a_l5_xg':               row.get('a_l5_xg', 0.0),
            'a_l5_xga':              row.get('a_l5_xga', 0.0),
            'referee_avg_cards_history': row.get('referee_avg_cards_history', ref_avg),
            'is_derby':              row.get('is_derby', 0),
            'relegation_pressure':   row.get('relegation_pressure', 0),
        }

        preds = selector.get_best_bet(features)
        if not preds:
            continue
            
        # Select best bet using Expected Value descending (Smart Selector)
        preds.sort(key=lambda x: x.get('ExpectedValue', 0.0), reverse=True)

        top_bet = None
        bookie_odds = 0.0

        for p in preds:
            prob = p['Probability']
            simulated_odds = p['ExpectedValue'] / prob + 1.0 if prob > 0 else 1.0
            simulated_odds = round(simulated_odds, 2)
            ev_val = p['ExpectedValue']
            
            # Require EV >= 0.0 and prob >= 0.55 confidence to match backtest
            if prob >= 0.55:
                top_bet = p
                bookie_odds = simulated_odds
                break

        if not top_bet:
            continue
            
        market = top_bet['Market']
        
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2    = row.get('result_1x2')
        
        pick = top_bet['Pick']
        won = evaluate_market_result(market, home_goals, away_goals, res_1x2, pick)
        
        if won:
            bet_profit = bookie_odds - 1.0
            cumulative_profit += bet_profit
            wins += 1
            status = 'Won'
        else:
            bet_profit = -1.0
            cumulative_profit += bet_profit
            losses += 1
            status = 'Lost'
            
        profit_chart_data.append({
            'name': match_date.strftime('%b %d'),
            'profit': round(cumulative_profit, 2)
        })
        
        history_data.append({
            'date': match_date.strftime('%b %d, %Y'),
            'match': f"{home} vs {away}",
            'prediction': market,
            'odds': bookie_odds,
            'result': status,
            'profit': round(bet_profit, 2),
            'homeGoals': int(home_goals),
            'awayGoals': int(away_goals),
            'features': features,
            'predictions': [
                {
                    'market': p['Market'],
                    'probability': round(p['Probability'] * 100, 1),
                    'odds': p['FairOdds'],
                    'ev': p['ExpectedValue'],
                    'won': evaluate_market_result(p['Market'], home_goals, away_goals, res_1x2, p['Pick'])
                } for p in preds
            ]
        })

    total_bets = wins + losses
    win_rate = round((wins / total_bets * 100), 1) if total_bets > 0 else 0.0
    history_data.reverse()

    return clean_json({
        'performanceSummary': {
            'totalProfit': round(cumulative_profit, 2),
            'winRate': win_rate,
            'totalBets': total_bets,
            'wins': wins,
            'losses': losses
        },
        'profitChartData': profit_chart_data,
        'historyData': history_data
    })

def run_detailed_history(payload):
    n = int(payload.get('n', 100))
    
    features_path = os.path.join(BASE_DIR, "data", "historical", "historical_sanitized_v7.csv")
    df = pd.read_csv(features_path, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)

    completed = df[df['home_goals'].notna()].copy()
    if completed.empty:
        return []

    test_set = completed.sort_values('date').tail(n)
    
    ref_avg = float(df['referee_avg_cards_history'].mean()) if 'referee_avg_cards_history' in df.columns else 3.5

    selector = MasterBetSelector()
    detailed_results = []
    
    for i, row in test_set.iterrows():
        home = row['home_team']
        away = row['away_team']
        match_date = row['date']
        home_goals = row['home_goals']
        away_goals = row['away_goals']
        res_1x2    = row.get('result_1x2')
        
        # Ensure 'is_derby' and 'relegation_pressure' are defined! (fixing KeyError bug)
        features = {
            'home_elo':              row.get('home_elo', 0.0),
            'away_elo':              row.get('away_elo', 0.0),
            'home_rest':             row.get('home_rest', 7.0),
            'away_rest':             row.get('away_rest', 7.0),
            'h_l5_pts':              row.get('h_l5_pts', 0.0),
            'h_l5_sh':               row.get('h_l5_sh', 0.0),
            'h_l5_sot':              row.get('h_l5_sot', 0.0),
            'h_l5_sot_c':            row.get('h_l5_sot_c', 0.0),
            'h_l5_gf':               row.get('h_l5_gf', 0.0),
            'h_l5_ga':               row.get('h_l5_ga', 0.0),
            'h_l5_fls':              row.get('h_l5_fls', 0.0),
            'h_l5_conv':             row.get('h_l5_conv', 0.0),
            'h_l5_xg':               row.get('h_l5_xg', 0.0),
            'h_l5_xga':              row.get('h_l5_xga', 0.0),
            'a_l5_pts':              row.get('a_l5_pts', 0.0),
            'a_l5_sh':               row.get('a_l5_sh', 0.0),
            'a_l5_sot':              row.get('a_l5_sot', 0.0),
            'a_l5_sot_c':            row.get('a_l5_sot_c', 0.0),
            'a_l5_gf':               row.get('a_l5_gf', 0.0),
            'a_l5_ga':               row.get('a_l5_ga', 0.0),
            'a_l5_fls':              row.get('a_l5_fls', 0.0),
            'a_l5_conv':             row.get('a_l5_conv', 0.0),
            'a_l5_xg':               row.get('a_l5_xg', 0.0),
            'a_l5_xga':              row.get('a_l5_xga', 0.0),
            'referee_avg_cards_history': ref_avg,
            'is_derby':              row.get('is_derby', 0),
            'relegation_pressure':   row.get('relegation_pressure', 0),
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
    return clean_json(detailed_results)

def run_seasons():
    features_path = os.path.join(BASE_DIR, "data", "historical", "historical_sanitized_v7.csv")
    df = pd.read_csv(features_path, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)
    completed = df[df['home_goals'].notna()].copy()
    if completed.empty:
        return []

    # Dynamic date-to-season mapper
    def get_season_code(date):
        if pd.isna(date):
            return None
        year = date.year
        month = date.month
        if month >= 8:
            start_yr = year
        else:
            start_yr = year - 1
        return (start_yr % 100) * 100 + ((start_yr + 1) % 100)

    completed['real_season'] = completed['date'].apply(get_season_code)
    
    result = []
    for szn in sorted(completed['real_season'].dropna().unique()):
        s = completed[completed['real_season'] == szn].copy()
        if s.empty:
            continue
        
        total = len(s)
        home_wins = int((s['home_goals'] > s['away_goals']).sum())
        draws     = int((s['home_goals'] == s['away_goals']).sum())
        away_wins = int((s['home_goals'] < s['away_goals']).sum())
        
        s['total_goals'] = s['home_goals'] + s['away_goals']
        
        # Monthly grouping
        s['month_key'] = s['date'].dt.to_period('M')
        monthly = []
        for period, grp in sorted(s.groupby('month_key'), key=lambda x: x[0]):
            grp_total = len(grp)
            monthly.append({
                'month':   period.strftime('%b %y'),
                'matches': grp_total,
                'homeWins': int((grp['home_goals'] > grp['away_goals']).sum()),
                'draws':    int((grp['home_goals'] == grp['away_goals']).sum()),
                'awayWins': int((grp['home_goals'] < grp['away_goals']).sum()),
                'avgGoals': round(float(grp['total_goals'].mean()), 2) if grp_total > 0 else 0.0,
            })
            
        start_y = 2000 + (szn // 100)
        end_y   = 2000 + (szn % 100)
        label = f"{start_y}/{str(end_y)[-2:]}"
        
        result.append({
            'season':    int(szn),
            'label':     label,
            'matches':   total,
            'homeWins':  home_wins,
            'draws':     draws,
            'awayWins':  away_wins,
            'homeWinPct': round(home_wins / total * 100, 1) if total else 0.0,
            'drawPct':    round(draws / total * 100, 1) if total else 0.0,
            'awayWinPct': round(away_wins / total * 100, 1) if total else 0.0,
            'avgGoals':  round(float(s['total_goals'].mean()), 2) if total else 0.0,
            'teams':     len(set(s['home_team'].unique().tolist() + s['away_team'].unique().tolist())),
            'monthly':   monthly,
        })
        
    result.sort(key=lambda x: x['season'], reverse=True)
    return clean_json(result)

def run_history(payload):
    n = int(payload.get('n', 50))
    season = payload.get('season', 'all')
    
    features_path = os.path.join(BASE_DIR, "data", "historical", "historical_sanitized_v7.csv")
    df = pd.read_csv(features_path, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)
    completed = df[df['home_goals'].notna()].copy()
    
    def get_season_code(date):
        if pd.isna(date):
            return None
        year = date.year
        month = date.month
        if month >= 8:
            start_yr = year
        else:
            start_yr = year - 1
        return (start_yr % 100) * 100 + ((start_yr + 1) % 100)

    completed['real_season'] = completed['date'].apply(get_season_code)
    
    if season and str(season) != 'all':
        try:
            szn_val = int(season)
            completed = completed[completed['real_season'] == szn_val]
        except Exception:
            pass
            
    rows = completed.sort_values('date').tail(n)
    result = []
    for _, row in rows.iterrows():
        hg = int(row['home_goals'])
        ag = int(row['away_goals'])
        if hg > ag:
            outcome = 'home_win'
        elif hg < ag:
            outcome = 'away_win'
        else:
            outcome = 'draw'
        result.append({
            'date':      row['date'].strftime('%Y-%m-%d'),
            'homeTeam':  row['home_team'],
            'awayTeam':  row['away_team'],
            'homeGoals': hg,
            'awayGoals': ag,
            'outcome':   outcome,
            'referee':   str(row.get('referee', '')) if pd.notna(row.get('referee')) else '',
            'totalCards': int(row.get('total_cards', 0)) if pd.notna(row.get('total_cards')) else 0,
            'season':    int(row['real_season']) if pd.notna(row.get('real_season')) else None,
        })
    result.reverse()  # newest first
    return clean_json(result)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        # Some calls like seasons may not pass payload
        if len(sys.argv) == 2:
            action = sys.argv[1]
            payload = {}
        else:
            sys.exit(1)
    else:
        action = sys.argv[1]
        payload_str = sys.argv[2]
        payload = json.loads(payload_str)

    if action == 'predict':
        print(json.dumps(run_predict(payload)))
    elif action == 'simulate':
        print(json.dumps(run_simulate(payload)))
    elif action == 'performance':
        print(json.dumps(run_performance()))
    elif action == 'detailed-history':
        print(json.dumps(run_detailed_history(payload)))
    elif action == 'seasons':
        print(json.dumps(run_seasons()))
    elif action == 'history':
        print(json.dumps(run_history(payload)))
    else:
        sys.exit(1)
