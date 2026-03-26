import os
import warnings
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
FEATURES_PATH = os.path.join(BASE_DIR, "data", "historical", "all_match_features_v2.csv")
FBREF_URL     = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
CONFIDENCE_THRESHOLD = 0.57   # Optimized
MIN_ODDS = 1.10
STAKE = 50.0

from src.upcoming import fetch_upcoming_fixtures

def calculate_elo_upto(matches_df, k=20):
    teams_elo = {}
    elo_rows = []
    for _, row in matches_df.iterrows():
        home = row['home_team']
        away = row['away_team']
        he = teams_elo.get(home, 1500)
        ae = teams_elo.get(away, 1500)
        elo_rows.append({'game': row.get('game'), 'home_team': home, 'away_team': away,
                          'home_elo': he, 'away_elo': ae})
        r = row.get('result_1x2', np.nan)
        if pd.notna(r):
            he_exp = 1 / (1 + 10 ** ((ae - he) / 400))
            ae_exp = 1 - he_exp
            if r == 2:   ha, aa = 1, 0
            elif r == 1: ha, aa = 0.5, 0.5
            else:        ha, aa = 0, 1
            teams_elo[home] = he + k * (ha - he_exp)
            teams_elo[away] = ae + k * (aa - ae_exp)
    return teams_elo, pd.DataFrame(elo_rows)

def get_team_last5_form(team, match_date, raw_matches, team_pstats):
    home_m = raw_matches[(raw_matches['home_team'] == team) & (raw_matches['date'] < match_date)].copy()
    away_m = raw_matches[(raw_matches['away_team'] == team) & (raw_matches['date'] < match_date)].copy()

    home_m['gf'] = home_m['home_goals']; home_m['ga'] = home_m['away_goals']
    home_m['pts'] = home_m['result_1x2'].map({2: 3, 1: 1, 0: 0}).fillna(0)
    home_m['opp_elo'] = home_m['away_elo']

    away_m['gf'] = away_m['away_goals']; away_m['ga'] = away_m['home_goals']
    away_m['pts'] = away_m['result_1x2'].map({0: 3, 1: 1, 2: 0}).fillna(0)
    away_m['opp_elo'] = away_m['home_elo']

    perf = pd.concat([home_m[['date', 'game', 'gf', 'ga', 'pts', 'opp_elo']],
                      away_m[['date', 'game', 'gf', 'ga', 'pts', 'opp_elo']]], ignore_index=True)
    perf = perf.sort_values('date').reset_index(drop=True)

    if perf.empty:
        return {k: 0 for k in ['l5_pts', 'l5_gf', 'l5_ga', 'l5_sh', 'l5_sot', 'l5_sot_c', 'l5_fls', 'l5_conv', 'rest_days']}

    last_match_date = perf['date'].iloc[-1]
    rest_days = (pd.Timestamp(match_date) - pd.Timestamp(last_match_date)).days
    rest_days = min(max(rest_days, 1), 14)

    game_ids = perf['game'].tolist()
    ps = team_pstats[(team_pstats['team'] == team) & (team_pstats['game'].isin(game_ids))]
    perf = pd.merge(perf, ps[['game', 'shots', 'sot', 'fouls']], on='game', how='left').fillna(0)

    opp_ps = team_pstats[(team_pstats['team'] != team) & (team_pstats['game'].isin(game_ids))]
    perf = pd.merge(perf, opp_ps[['game', 'sot']].rename(columns={'sot': 'sot_conceded'}), on='game', how='left').fillna(0)

    perf['adj_factor'] = np.clip(perf['opp_elo'] / 1500.0, 0.7, 1.3)
    perf['adj_pts'] = perf['pts'] * perf['adj_factor']
    perf['adj_shots'] = perf['shots'] * perf['adj_factor']
    perf['adj_sot'] = perf['sot'] * perf['adj_factor']
    perf['adj_sot_c'] = perf['sot_conceded'] / perf['adj_factor']
    perf['adj_gf'] = perf['gf'] * perf['adj_factor']
    perf['adj_ga'] = perf['ga'] / perf['adj_factor']
    perf['conv_rate'] = np.where(perf['adj_shots'] > 0, perf['adj_gf'] / perf['adj_shots'], 0)
    
    ewma_pts = perf['adj_pts'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_gf = perf['adj_gf'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_ga = perf['adj_ga'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_sh = perf['adj_shots'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_sot = perf['adj_sot'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_sot_c = perf['adj_sot_c'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_fls = perf['fouls'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_conv = perf['conv_rate'].ewm(span=5, min_periods=1).mean().iloc[-1]

    return {
        'l5_pts':  ewma_pts, 'l5_gf':   ewma_gf, 'l5_ga':   ewma_ga,
        'l5_sh':   ewma_sh, 'l5_sot':  ewma_sot, 'l5_sot_c': ewma_sot_c,
        'l5_fls':  ewma_fls, 'l5_conv': ewma_conv, 'rest_days': rest_days
    }

def get_referee_avg_cards(referee, match_date, raw_matches):
    hist = raw_matches[(raw_matches['referee'] == referee) & (raw_matches['date'] < match_date)]
    if hist.empty or 'total_cards' not in hist.columns:
        return raw_matches['total_cards'].mean() if 'total_cards' in raw_matches.columns else 3.5
    return hist['total_cards'].mean()

def main():
    print("📂 Loading historical match database...\n")
    raw = pd.read_csv(FEATURES_PATH, parse_dates=['date'])
    raw = raw.sort_values('date').reset_index(drop=True)

    needed_cols = ['game', 'home_team', 'away_team', 'date', 'result_1x2',
                   'home_goals', 'away_goals', 'h_l5_sh', 'h_l5_sot', 'h_l5_fls',
                   'a_l5_sh', 'a_l5_sot', 'a_l5_fls', 'home_elo', 'away_elo', 'referee', 'total_cards']
    needed_cols = [c for c in needed_cols if c in raw.columns]
    raw = raw[needed_cols]

    home_pstat = raw[['game', 'home_team', 'h_l5_sh', 'h_l5_sot', 'h_l5_fls']].rename(
        columns={'home_team': 'team', 'h_l5_sh': 'shots', 'h_l5_sot': 'sot', 'h_l5_fls': 'fouls'})
    away_pstat = raw[['game', 'away_team', 'a_l5_sh', 'a_l5_sot', 'a_l5_fls']].rename(
        columns={'away_team': 'team', 'a_l5_sh': 'shots', 'a_l5_sot': 'sot', 'a_l5_fls': 'fouls'})
    team_pstats = pd.concat([home_pstat, away_pstat], ignore_index=True)

    fixtures = fetch_upcoming_fixtures()
    if fixtures is None or fixtures.empty:
        print("No fixtures to process. Exiting.")
        return

    from src.models.selector import MasterBetSelector
    selector = MasterBetSelector()

    print("\n" + "=" * 70)
    print("       ⭐  PREDICTING UPCOMING BETS  ⭐")
    print("=" * 70)

    upcoming_bets = []

    for _, fixture in fixtures.iterrows():
        home     = fixture['home_team']
        away     = fixture['away_team']
        match_dt = pd.Timestamp(fixture['date'])

        past_matches = raw[raw['date'] < match_dt].copy()
        elo_state, _ = calculate_elo_upto(past_matches)
        home_elo = elo_state.get(home, 1500)
        away_elo = elo_state.get(away, 1500)

        h_form = get_team_last5_form(home, match_dt, past_matches, team_pstats)
        a_form = get_team_last5_form(away, match_dt, past_matches, team_pstats)

        referee   = raw[raw['date'] < match_dt]['referee'].iloc[-1] if not past_matches.empty else 'Unknown'
        ref_cards = get_referee_avg_cards(referee, match_dt, past_matches)

        features = {
            'home_elo':              home_elo, 'away_elo':              away_elo,
            'h_missing_key_player':  0, 'a_missing_key_player':  0,
            'home_rest': h_form['rest_days'], 'away_rest': a_form['rest_days'],
            'h_l5_pts':  h_form['l5_pts'], 'h_l5_sh':   h_form['l5_sh'],
            'h_l5_sot':  h_form['l5_sot'], 'h_l5_sot_c':h_form['l5_sot_c'],
            'h_l5_gf':   h_form['l5_gf'], 'h_l5_ga':   h_form['l5_ga'],
            'h_l5_fls':  h_form['l5_fls'], 'h_l5_conv': h_form['l5_conv'],
            'a_l5_pts':  a_form['l5_pts'], 'a_l5_sh':   a_form['l5_sh'],
            'a_l5_sot':  a_form['l5_sot'], 'a_l5_sot_c':a_form['l5_sot_c'],
            'a_l5_gf':   a_form['l5_gf'], 'a_l5_ga':   a_form['l5_ga'],
            'a_l5_fls':  a_form['l5_fls'], 'a_l5_conv': a_form['l5_conv'],
            'referee_avg_cards_history': ref_cards,
        }

        predictions = selector.get_best_bet(features)

        for p in predictions:
            prob = p['Probability']
            f_odds = 1.0 / prob if prob > 0 else 2.0
            simulated_odds = round(max(1.01, f_odds * 0.95), 2)
            
            if simulated_odds >= MIN_ODDS and prob >= CONFIDENCE_THRESHOLD:
                upcoming_bets.append({
                    'Date': match_dt.date(),
                    'Match': f"{home} vs {away}",
                    'Market': p['Market'],
                    'Confidence': f"{prob*100:.1f}%",
                    'Pick': p['Pick'],
                    'Estimated_Value_Odds': simulated_odds,
                    'Recommended_Stake': STAKE
                })

    if upcoming_bets:
        df_out = pd.DataFrame(upcoming_bets)
        out_file = "upcoming_bets.csv"
        df_out.to_csv(out_file, index=False)
        print(f"\n✅ Created {out_file} with {len(upcoming_bets)} recommended bets.")
        print(df_out.to_string())
    else:
        print("\nℹ️ No upcoming bets met the strict criteria.")

if __name__ == '__main__':
    main()
