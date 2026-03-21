"""
predict_upcoming.py – Live Premier League Bet Predictor
=======================================================
This script:
1. Scrapes the upcoming Premier League fixtures from FBref.
2. Reconstructs each team's features (Elo, Last-5 form, Shot Conversion Rate, etc.)
   using **ONLY historical data prior to the match date** to maintain temporal integrity.
3. Prompts the user to flag any missing key players (injuries/suspensions).
4. Runs the MasterBetSelector and prints actionable "Star Bets" (>=70% confidence).
"""

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
BASE_DIR      = r"c:\Users\PC\DataScience\archive\pl-predictor"
FEATURES_PATH = os.path.join(BASE_DIR, "data", "historical", "all_match_features_v2.csv")
FBREF_URL     = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
CONFIDENCE_THRESHOLD = 0.70   # Only show bets with >= 70% confidence

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 – Scrape upcoming fixtures from FBref
# ─────────────────────────────────────────────────────────────────────────────
def fetch_upcoming_fixtures():
    print("📡 Fetching upcoming Premier League fixtures from FBref via SeleniumBase (Anti-Detect)...")
    try:
        from seleniumbase import Driver
        import time
        # Using uc=True (undetected-chromedriver) to bypass Cloudflare
        # headless=False helps avoid detection and allows manual captcha solving if needed
        driver = Driver(uc=True, headless=False)
        driver.get(FBREF_URL)
        # We wait up to 60 seconds for the actual data table to appear. 
        # If Cloudflare asks for a manual checkbox click, you have 60 seconds to click it in the popup window!
        driver.wait_for_element("table", timeout=60)
        time.sleep(2) # Extra buffer for JS parsing
        html = driver.page_source
        driver.quit()
        tables = pd.read_html(html, encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ Could not fetch FBref automatically ({e}).")
        print("  → Falling back to manual input mode.\n")
        try:
            driver.quit()
        except:
            pass
        return manual_fixture_input()

    # FBref fixture table has columns: Wk, Day, Date, Time, Home, Score, Away...
    fixtures = tables[0]
    fixtures.columns = [str(c).strip() for c in fixtures.columns]

    # Filter rows where Score is empty (= match not played yet)
    score_col = next((c for c in fixtures.columns if 'Score' in c), None)
    home_col  = next((c for c in fixtures.columns if 'Home' in c), None)
    away_col  = next((c for c in fixtures.columns if 'Away' in c), None)
    date_col  = next((c for c in fixtures.columns if 'Date' == c), None)

    if not all([score_col, home_col, away_col, date_col]):
        print("  ⚠ Could not parse FBref table structure. Falling back to manual input.")
        return manual_fixture_input()

    fixtures['date_parsed'] = pd.to_datetime(fixtures[date_col], errors='coerce')
    today = pd.Timestamp(datetime.now().date())
    upcoming = fixtures[(fixtures['date_parsed'] >= today) & (fixtures[score_col].isna() | (fixtures[score_col] == ''))]

    if upcoming.empty:
        print("  ⚠ No upcoming fixtures found (or all played). Falling back to manual.")
        return manual_fixture_input()

    # Keep next 7 days
    upcoming = upcoming[upcoming['date_parsed'] <= today + timedelta(days=7)]
    result = upcoming[['date_parsed', home_col, away_col]].rename(
        columns={'date_parsed': 'date', home_col: 'home_team', away_col: 'away_team'}).reset_index(drop=True)

    print(f"  ✅ Found {len(result)} upcoming fixture(s):\n")
    for i, row in result.iterrows():
        print(f"     [{i+1}] {row['home_team']} vs {row['away_team']}  –  {row['date'].date()}")
    return result


def manual_fixture_input():
    """Fallback: let user type in matches manually."""
    matches = []
    print("Enter upcoming matches manually (type 'done' when finished):")
    while True:
        home = input("  Home team (or 'done'): ").strip()
        if home.lower() == 'done':
            break
        away = input("  Away team: ").strip()
        date_str = input("  Match date (YYYY-MM-DD): ").strip()
        try:
            d = pd.Timestamp(date_str)
        except Exception:
            d = pd.Timestamp(datetime.now().date())
        matches.append({'date': d, 'home_team': home, 'away_team': away})
    return pd.DataFrame(matches)


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 – Reconstruct team state using ONLY data before match date (temporal safety)
# ─────────────────────────────────────────────────────────────────────────────
def calculate_elo_upto(matches_df, k=20):
    """Re-run Elo from scratch chronologically. Guarantees no future leakage."""
    teams_elo = {}
    elo_rows = []
    for _, row in matches_df.iterrows():
        home = row['home_team']
        away = row['away_team']
        he = teams_elo.get(home, 1500)
        ae = teams_elo.get(away, 1500)
        elo_rows.append({'game': row.get('game'), 'home_team': home, 'away_team': away,
                          'home_elo': he, 'away_elo': ae})
        # update only if result is known
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
    """
    Returns the EWMA form vector for a team
    using ONLY matches strictly before `match_date`.
    """
    # Filter historical matches for this team before the given date
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

    # Calculate rest days between last match and current date
    last_match_date = perf['date'].iloc[-1]
    rest_days = (pd.Timestamp(match_date) - pd.Timestamp(last_match_date)).days
    rest_days = min(max(rest_days, 1), 14) # Clip between 1 and 14

    # Merge with player stats for that team
    game_ids = perf['game'].tolist()
    ps = team_pstats[(team_pstats['team'] == team) & (team_pstats['game'].isin(game_ids))]
    
    # Needs to align shots, sot, fouls per game
    perf = pd.merge(perf, ps[['game', 'shots', 'sot', 'fouls']], on='game', how='left').fillna(0)

    # Opponent shots conceded
    opp_ps = team_pstats[(team_pstats['team'] != team) & (team_pstats['game'].isin(game_ids))]
    perf = pd.merge(perf, opp_ps[['game', 'sot']].rename(columns={'sot': 'sot_conceded'}), on='game', how='left').fillna(0)

    # Strength of Schedule (SoS) adjustment
    perf['adj_factor'] = np.clip(perf['opp_elo'] / 1500.0, 0.7, 1.3)
    
    perf['adj_pts'] = perf['pts'] * perf['adj_factor']
    perf['adj_shots'] = perf['shots'] * perf['adj_factor']
    perf['adj_sot'] = perf['sot'] * perf['adj_factor']
    perf['adj_sot_c'] = perf['sot_conceded'] / perf['adj_factor']
    perf['adj_gf'] = perf['gf'] * perf['adj_factor']
    perf['adj_ga'] = perf['ga'] / perf['adj_factor']
    
    perf['conv_rate'] = np.where(perf['adj_shots'] > 0, perf['adj_gf'] / perf['adj_shots'], 0)
    
    # EWMA calculation on the historical sequence
    ewma_pts = perf['adj_pts'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_gf = perf['adj_gf'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_ga = perf['adj_ga'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_sh = perf['adj_shots'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_sot = perf['adj_sot'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_sot_c = perf['adj_sot_c'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_fls = perf['fouls'].ewm(span=5, min_periods=1).mean().iloc[-1]
    ewma_conv = perf['conv_rate'].ewm(span=5, min_periods=1).mean().iloc[-1]

    return {
        'l5_pts':  ewma_pts,
        'l5_gf':   ewma_gf,
        'l5_ga':   ewma_ga,
        'l5_sh':   ewma_sh,
        'l5_sot':  ewma_sot,
        'l5_sot_c': ewma_sot_c,
        'l5_fls':  ewma_fls,
        'l5_conv': ewma_conv,
        'rest_days': rest_days
    }


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 – Referee historical average cards (temporal-safe)
# ─────────────────────────────────────────────────────────────────────────────
def get_referee_avg_cards(referee, match_date, raw_matches):
    hist = raw_matches[(raw_matches['referee'] == referee) & (raw_matches['date'] < match_date)]
    if hist.empty or 'total_cards' not in hist.columns:
        return raw_matches['total_cards'].mean() if 'total_cards' in raw_matches.columns else 3.5
    return hist['total_cards'].mean()


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 – Interactive injury prompt
# ─────────────────────────────────────────────────────────────────────────────
def ask_missing_key_player(home_team, away_team):
    print()
    h_missing = input(f"  ❓ Is a KEY PLAYER (top-2 scorer) missing for {home_team}? (y/N): ").strip().lower()
    a_missing = input(f"  ❓ Is a KEY PLAYER (top-2 scorer) missing for {away_team}? (y/N): ").strip().lower()
    return int(h_missing == 'y'), int(a_missing == 'y')


# ─────────────────────────────────────────────────────────────────────────────
# Main Orchestrator
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # --- Load historical data ---
    print("📂 Loading historical match database...\n")
    raw = pd.read_csv(FEATURES_PATH, parse_dates=['date'])
    raw = raw.sort_values('date').reset_index(drop=True)

    # Rebuild team_pstats proxy inline (we need shots/sot/fouls per game/team)
    needed_cols = ['game', 'home_team', 'away_team', 'date', 'result_1x2',
                   'home_goals', 'away_goals',
                   'h_l5_sh', 'h_l5_sot', 'h_l5_fls',
                   'a_l5_sh', 'a_l5_sot', 'a_l5_fls',
                   'home_elo', 'away_elo', 'referee', 'total_cards']
    needed_cols = [c for c in needed_cols if c in raw.columns]
    raw = raw[needed_cols]

    # Build a per-game shots table (approximated from last-5 averages in CSV)
    # This is sufficient for reconstructing opponent context
    home_pstat = raw[['game', 'home_team', 'h_l5_sh', 'h_l5_sot', 'h_l5_fls']].rename(
        columns={'home_team': 'team', 'h_l5_sh': 'shots', 'h_l5_sot': 'sot', 'h_l5_fls': 'fouls'})
    away_pstat = raw[['game', 'away_team', 'a_l5_sh', 'a_l5_sot', 'a_l5_fls']].rename(
        columns={'away_team': 'team', 'a_l5_sh': 'shots', 'a_l5_sot': 'sot', 'a_l5_fls': 'fouls'})
    team_pstats = pd.concat([home_pstat, away_pstat], ignore_index=True)

    # --- Fetch fixtures ---
    fixtures = fetch_upcoming_fixtures()
    if fixtures is None or fixtures.empty:
        print("No fixtures to process. Exiting.")
        return

    # --- Load MasterBetSelector ---
    from src.models.selector import MasterBetSelector
    selector = MasterBetSelector()

    print("\n" + "=" * 70)
    print("       ⭐  MASTER BET SELECTOR  –  UPCOMING FIXTURES  ⭐")
    print("=" * 70)

    for _, fixture in fixtures.iterrows():
        home     = fixture['home_team']
        away     = fixture['away_team']
        match_dt = pd.Timestamp(fixture['date'])

        print(f"\n\n{'─'*70}")
        print(f"  🏟  {home}  vs  {away}   |   {match_dt.date()}")
        print(f"{'─'*70}")

        # ── Temporal-safe Elo ──────────────────────────────────────────────
        past_matches = raw[raw['date'] < match_dt].copy()
        elo_state, _ = calculate_elo_upto(past_matches)
        home_elo = elo_state.get(home, 1500)
        away_elo = elo_state.get(away, 1500)

        # ── Last-5 form (temporally safe) ─────────────────────────────────
        h_form = get_team_last5_form(home, match_dt, past_matches, team_pstats)
        a_form = get_team_last5_form(away, match_dt, past_matches, team_pstats)

        # ── Referee avg cards ─────────────────────────────────────────────
        referee   = raw[raw['date'] < match_dt]['referee'].iloc[-1] if not past_matches.empty else 'Unknown'
        ref_cards = get_referee_avg_cards(referee, match_dt, past_matches)

        # ── Injury prompt ─────────────────────────────────────────────────
        h_miss, a_miss = ask_missing_key_player(home, away)

        # ── Build feature dict ────────────────────────────────────────────
        features = {
            'home_elo':              home_elo,
            'away_elo':              away_elo,
            'h_missing_key_player':  h_miss,
            'a_missing_key_player':  a_miss,
            'home_rest': h_form['rest_days'],
            'away_rest': a_form['rest_days'],
            'h_l5_pts':  h_form['l5_pts'],
            'h_l5_sh':   h_form['l5_sh'],
            'h_l5_sot':  h_form['l5_sot'],
            'h_l5_sot_c':h_form['l5_sot_c'],
            'h_l5_gf':   h_form['l5_gf'],
            'h_l5_ga':   h_form['l5_ga'],
            'h_l5_fls':  h_form['l5_fls'],
            'h_l5_conv': h_form['l5_conv'],
            'a_l5_pts':  a_form['l5_pts'],
            'a_l5_sh':   a_form['l5_sh'],
            'a_l5_sot':  a_form['l5_sot'],
            'a_l5_sot_c':a_form['l5_sot_c'],
            'a_l5_gf':   a_form['l5_gf'],
            'a_l5_ga':   a_form['l5_ga'],
            'a_l5_fls':  a_form['l5_fls'],
            'a_l5_conv': a_form['l5_conv'],
            'referee_avg_cards_history': ref_cards,
        }

        # ── Run selector ──────────────────────────────────────────────────
        predictions = selector.get_best_bet(features)

        star_bets = [p for p in predictions if p['Probability'] >= CONFIDENCE_THRESHOLD]
        
        if star_bets:
            print(f"\n  ⭐ RECOMMENDED BETS (≥{int(CONFIDENCE_THRESHOLD*100)}% confidence):\n")
            for rank, bet in enumerate(star_bets, 1):
                print(f"     {rank}. {bet['Market']:<40}  →  {bet['Confidence']}")
        else:
            # Show top-3 regardless
            print(f"\n  ℹ No bet reached {int(CONFIDENCE_THRESHOLD*100)}%. Top options:\n")
            for bet in predictions[:3]:
                print(f"     · {bet['Market']:<40}  →  {bet['Confidence']}")

    print("\n" + "=" * 70)
    print("  Analysis complete. Always gamble responsibly.")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
