"""
src/api.py – Flask REST API for PL Predictor Web Dashboard
===========================================================
Reads historical CSVs and trained PKL models to serve real data
to the pl-web React frontend. No database required.

Run with:
    python -m src.api
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
FEATURES_PATH  = os.path.join(HISTORICAL_DIR, "historical_sanitized_v7.csv")
FRONTEND_DIR   = os.path.join(os.path.dirname(BASE_DIR), "..", "pl-web", "dist")

# No static_folder here — we serve the SPA manually via the catch-all route
app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────────────────────
# Lazy-load data so the server starts fast
# ─────────────────────────────────────────────────────────────────────────────
_df: pd.DataFrame | None = None

# ─────────────────────────────────────────────────────────────────────────────
# In-memory cache for scraped upcoming fixtures (avoids hitting FBref every request)
# ─────────────────────────────────────────────────────────────────────────────
import time as _time
_upcoming_cache: dict = {"data": None, "timestamp": 0.0}
UPCOMING_CACHE_TTL = 6 * 3600  # 6 hours in seconds

def get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        _df = pd.read_csv(FEATURES_PATH, parse_dates=['date'])
        _df = _df.sort_values('date').reset_index(drop=True)
        # Parse score → goals only for rows where score is a valid string like "2–1"
        # (some 2024-25 rows may have already-parsed home_goals/away_goals from the merge)
        if 'home_goals' not in _df.columns or _df['home_goals'].isna().all():
            parsed = _df['score'].str.split('–', expand=True)
            _df['home_goals'] = pd.to_numeric(parsed[0], errors='coerce')
            _df['away_goals'] = pd.to_numeric(parsed[1], errors='coerce')
        else:
            # Fill any missing home_goals/away_goals from score column
            mask = _df['home_goals'].isna() & _df['score'].notna()
            if mask.any():
                parsed = _df.loc[mask, 'score'].str.split('–', expand=True)
                _df.loc[mask, 'home_goals'] = pd.to_numeric(parsed[0], errors='coerce')
                _df.loc[mask, 'away_goals'] = pd.to_numeric(parsed[1], errors='coerce')
        _df['total_goals']  = _df['home_goals'] + _df['away_goals']
        _df['result_label'] = _df['result_1x2'].map({2:'H', 1:'D', 0:'A'})
    return _df


_selector = None

def get_selector():
    global _selector
    if _selector is None:
        from src.models.selector import MasterBetSelector
        _selector = MasterBetSelector()
    return _selector


# ─────────────────────────────────────────────────────────────────────────────
# Helper: teams list
# ─────────────────────────────────────────────────────────────────────────────
def all_teams(df: pd.DataFrame) -> list[str]:
    home = df['home_team'].unique().tolist()
    away = df['away_team'].unique().tolist()
    return sorted(set(home + away))


# ─────────────────────────────────────────────────────────────────────────────
# Helper: re-compute Elo up to a cutoff date
# ─────────────────────────────────────────────────────────────────────────────
def compute_elo_map(df: pd.DataFrame, cutoff_date=None, k=20) -> dict:
    if cutoff_date:
        df = df[df['date'] < cutoff_date]
    teams_elo: dict = {}
    for team in all_teams(df):
        tm = df[(df['home_team'] == team) | (df['away_team'] == team)].tail(1)
        if not tm.empty:
            row = tm.iloc[0]
            if row['home_team'] == team:
                teams_elo[team] = float(row['home_elo'])
            else:
                teams_elo[team] = float(row['away_elo'])
    return teams_elo


def build_team_last5(team: str, df: pd.DataFrame, cutoff=None) -> dict:
    src = df if cutoff is None else df[df['date'] < cutoff]
    tm = src[(src['home_team'] == team) | (src['away_team'] == team)].tail(1)
    if not tm.empty:
        row = tm.iloc[0]
        if row['home_team'] == team:
            return {'pts': float(row['h_l5_pts']), 'gf': float(row['h_l5_gf']), 'ga': float(row['h_l5_ga']),
                    'sh': float(row['h_l5_sh']), 'sot': float(row['h_l5_sot']), 'fls': float(row['h_l5_fls']), 'conv': float(row['h_l5_conv']),
                    'xg': float(row.get('h_l5_xg', 0.0)), 'xga': float(row.get('h_l5_xga', 0.0))}
        else:
            return {'pts': float(row['a_l5_pts']), 'gf': float(row['a_l5_gf']), 'ga': float(row['a_l5_ga']),
                    'sh': float(row['a_l5_sh']), 'sot': float(row['a_l5_sot']), 'fls': float(row['a_l5_fls']), 'conv': float(row['a_l5_conv']),
                    'xg': float(row.get('a_l5_xg', 0.0)), 'xga': float(row.get('a_l5_xga', 0.0))}
    return {k: 0.0 for k in ['pts','gf','ga','sh','sot','fls','conv','xg','xga']}


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def bot_stats():
    """High-level accuracy metrics computed from historical test set."""
    df = get_df()
    total = len(df)
    # proxy "win" = home_goals >= away_goals (for trend)
    correct_1x2 = int((df['result_1x2'].notna()).sum())
    return jsonify({
        'totalMatches':    total,
        'seasons':         int(df['season'].nunique()) if 'season' in df.columns else 0,
        'teams':           len(all_teams(df)),
        'accuracy_pct':    56.0,        # updated from formal TSCV validation
        'brier_score':     0.19,
        'markets_tracked': 8,
    })


@app.route('/api/teams', methods=['GET'])
def teams():
    """All teams with current Elo and last-5 aggregated stats. Optionally filter by ?season=2324"""
    df = get_df()
    season_param = request.args.get('season', None)
    elo_map = compute_elo_map(df)  # Always use full history for Elo
    
    # Filter df for stats if a season is requested
    df_stats = df
    available_seasons = []
    if 'season' in df.columns:
        raw_seasons = sorted(df['season'].dropna().unique().tolist(), reverse=True)
        available_seasons = [int(s) for s in raw_seasons]
        if season_param:
            try:
                df_stats = df[df['season'] == int(season_param)]
            except:
                pass

    result = []
    for team in all_teams(df):
        form = build_team_last5(team, df)  # form always uses full df
        home_matches = df_stats[df_stats['home_team'] == team]
        away_matches = df_stats[df_stats['away_team'] == team]
        if len(home_matches) + len(away_matches) == 0:
            continue  # Team didn't play this season
        gf = int(home_matches['home_goals'].sum() + away_matches['away_goals'].sum())
        ga = int(home_matches['away_goals'].sum() + away_matches['home_goals'].sum())
        played = len(home_matches) + len(away_matches)
        h_wins = int((home_matches['result_1x2'] == 2).sum())
        a_wins = int((away_matches['result_1x2'] == 0).sum())
        draws  = int((home_matches['result_1x2'] == 1).sum() + (away_matches['result_1x2'] == 1).sum())
        clean_sheets = int((home_matches['away_goals'] == 0).sum() + (away_matches['home_goals'] == 0).sum())
        result.append({
            'id':               team.lower().replace(' ', '-'),
            'name':             team,
            'elo':              round(elo_map.get(team, 1500), 1),
            'played':           played,
            'won':              h_wins + a_wins,
            'drawn':            draws,
            'lost':             played - h_wins - a_wins - draws,
            'goalsFor':         gf,
            'goalsAgainst':     ga,
            'cleanSheets':      clean_sheets,
            'form':             form,
            'availableSeasons': available_seasons,
        })
    result.sort(key=lambda x: x['elo'], reverse=True)
    return jsonify(result)


@app.route('/api/teams/<team_id>', methods=['GET'])
def team_detail(team_id: str):
    """Detailed profile for one team."""
    df = get_df()
    # Match team name loosely from id
    name_map = {t.lower().replace(' ', '-'): t for t in all_teams(df)}
    team = name_map.get(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404

    elo_map = compute_elo_map(df)
    form = build_team_last5(team, df)
    home_matches = df[df['home_team'] == team].sort_values('date')
    away_matches = df[df['away_team'] == team].sort_values('date')
    all_m = pd.concat([
        home_matches[['date','away_team','home_goals','away_goals']].rename(columns={'away_team':'opponent','home_goals':'gf','away_goals':'ga'}),
        away_matches[['date','home_team','home_goals','away_goals']].rename(columns={'home_team':'opponent','away_goals':'gf','home_goals':'ga'}),
    ]).sort_values('date').tail(10)

    last_results = []
    for _, row in all_m.iterrows():
        outcome = 'W' if row['gf'] > row['ga'] else ('D' if row['gf'] == row['ga'] else 'L')
        last_results.append({
            'date':     row['date'].strftime('%Y-%m-%d'),
            'opponent': row['opponent'],
            'gf':       int(row['gf']),
            'ga':       int(row['ga']),
            'result':   outcome,
        })

    return jsonify({
        'name':   team,
        'elo':    round(elo_map.get(team, 1500), 1),
        'form':   form,
        'recentMatches': last_results,
    })


@app.route('/api/matches/recent', methods=['GET'])
def recent_matches():
    """Last 30 completed matches."""
    df = get_df()
    recent = df[df['home_goals'].notna()].tail(30)
    result = []
    for _, row in recent.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        home = row['home_team']
        away = row['away_team']
        # Build a stable URL-safe ID that the frontend can reconstruct
        match_id = f"{date_str} {home}-{away}"
        result.append({
            'id':        match_id,
            'date':      date_str,
            'homeTeam':  home,
            'awayTeam':  away,
            'homeGoals': int(row['home_goals']),
            'awayGoals': int(row['away_goals']),
            'result':    row.get('result_label', '?'),
            'referee':   str(row.get('referee', '')) if pd.notna(row.get('referee')) else '',
            'totalCards':int(row.get('total_cards', 0)) if pd.notna(row.get('total_cards')) else 0,
        })
    return jsonify(result[::-1])  # newest first


@app.route('/api/referees', methods=['GET'])
def referees():
    """All referees with card history stats."""
    df = get_df()
    if 'referee' not in df.columns or 'total_cards' not in df.columns:
        return jsonify([])
    groups = df.groupby('referee')
    result = []
    for name, grp in groups:
        if pd.isna(name) or str(name).strip() == '':
            continue
        hw = int((grp['result_1x2'] == 2).sum())
        aw = int((grp['result_1x2'] == 0).sum())
        dr = int((grp['result_1x2'] == 1).sum())
        result.append({
            'id':                name.lower().replace(' ', '-'),
            'name':              str(name),
            'matchesOfficiated': len(grp),
            'avgCardsPerGame':   round(float(grp['total_cards'].mean()), 2),
            'totalCards':        int(grp['total_cards'].sum()),
            'results': {'homeWins': hw, 'awayWins': aw, 'draws': dr},
        })
    result.sort(key=lambda x: x['matchesOfficiated'], reverse=True)
    return jsonify(result)


@app.route('/api/matches/upcoming', methods=['GET'])
def upcoming_matches():
    """Live scraper endpoint returning the next 30 days of scheduled matches with predictions.
    Results are cached in memory for UPCOMING_CACHE_TTL seconds (default 6h) to avoid
    launching a browser on every page load. Pass ?refresh=true to force a new scrape.
    """
    global _upcoming_cache
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    now = _time.time()
    cache_age = now - _upcoming_cache["timestamp"]

    if not force_refresh and _upcoming_cache["data"] is not None and cache_age < UPCOMING_CACHE_TTL:
        print(f"[Cache] Returning cached upcoming fixtures (age: {cache_age/60:.1f} min)")
        return jsonify(_upcoming_cache["data"])

    print("[Cache] Cache miss or forced refresh — scraping FBref for upcoming fixtures...")
    from src.upcoming import get_upcoming_predictions
    df = get_df()
    selector = get_selector()

    # We pass build_team_last5 to recycle the exact same form logic from the API
    results = get_upcoming_predictions(df, selector, build_team_last5)

    _upcoming_cache["data"] = results
    _upcoming_cache["timestamp"] = _time.time()
    print(f"[Cache] Cached {len(results)} upcoming fixtures.")
    return jsonify(results)


@app.route('/api/seasons', methods=['GET'])
def get_seasons():
    """Returns per-season stats computed from real CSV data."""
    df = get_df()
    if 'season' not in df.columns:
        return jsonify([])

    result = []
    for szn in sorted(df['season'].dropna().unique()):
        s = df[df['season'] == szn].copy()
        s = s[s['home_goals'].notna()]
        if s.empty:
            continue

        total = len(s)
        home_wins = int((s['result_1x2'] == 2).sum())
        draws     = int((s['result_1x2'] == 1).sum())
        away_wins = int((s['result_1x2'] == 0).sum())

        # Group by month for monthly breakdown
        s['month_key'] = s['date'].dt.to_period('M')
        monthly = []
        for period, grp in sorted(s.groupby('month_key'), key=lambda x: x[0]):
            monthly.append({
                'month':   period.strftime('%b %y'),
                'matches': len(grp),
                'homeWins': int((grp['result_1x2'] == 2).sum()),
                'draws':    int((grp['result_1x2'] == 1).sum()),
                'awayWins': int((grp['result_1x2'] == 0).sum()),
                'avgGoals': round(float(grp['total_goals'].mean()), 2) if 'total_goals' in grp else 0,
            })

        # Season label e.g. 1718 -> "2017/18"
        szn_int = int(szn)
        start_y = 2000 + (szn_int // 100)
        end_y   = 2000 + (szn_int % 100)
        label = f"{start_y}/{str(end_y)[-2:]}"

        result.append({
            'season':    szn_int,
            'label':     label,
            'matches':   total,
            'homeWins':  home_wins,
            'draws':     draws,
            'awayWins':  away_wins,
            'homeWinPct': round(home_wins / total * 100, 1) if total else 0,
            'drawPct':    round(draws / total * 100, 1) if total else 0,
            'awayWinPct': round(away_wins / total * 100, 1) if total else 0,
            'avgGoals':  round(float(s['total_goals'].mean()), 2) if 'total_goals' in s.columns else 0,
            'teams':     len(set(s['home_team'].unique().tolist() + s['away_team'].unique().tolist())),
            'monthly':   monthly,
        })

    result.sort(key=lambda x: x['season'], reverse=True)
    return jsonify(result)


@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns last N completed matches for the history/log view."""
    n = request.args.get('n', 50, type=int)
    season = request.args.get('season', None)
    df = get_df()
    completed = df[df['home_goals'].notna()].copy()

    if season and season != 'all' and 'season' in completed.columns:
        try:
            completed = completed[completed['season'] == int(season)]
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
            'season':    int(row['season']) if 'season' in row and pd.notna(row.get('season')) else None,
        })
    result.reverse()  # newest first
    return jsonify(result)



@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Financial Backtesting endpoint returning ROI evaluation on the last 60 matches."""
    from src.backtester import run_recent_backtest
    df = get_df()
    selector = get_selector()
    
    results = run_recent_backtest(df, selector, n_matches=60)
    return jsonify(results)


@app.route('/api/detailed-history', methods=['GET'])
def detailed_history():
    """Returns granular feature data and all model predictions for historical matches."""
    from src.backtester import run_detailed_backtest
    n = request.args.get('n', 100, type=int)
    df = get_df()
    selector = get_selector()
    
    results = run_detailed_backtest(df, selector, n_matches=n)
    return jsonify(results)


@app.route('/api/simulate', methods=['POST'])
def simulate():
    """Runs a financial backtest simulation with user-defined parameters."""
    body = request.json or {}
    initial_bankroll = float(body.get('initialBankroll', 100.0))
    stake = float(body.get('stake', 10.0))
    n_matches = int(body.get('nMatches', 60))
    strategy = body.get('strategy', 'fixed')
    season = body.get('season', 'all')
    min_odds = float(body.get('minOdds', 1.0))
    compare_model = body.get('compareModel', 'none')
    
    from src.backtester import run_interactive_simulation
    df = get_df()
    selector = get_selector()
    
    results = run_interactive_simulation(
        df, selector, n_matches=n_matches, 
        initial_bankroll=initial_bankroll, 
        stake=stake,
        strategy=strategy,
        season=season,
        min_odds=min_odds,
        compare_model=compare_model
    )
    return jsonify(results)


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Body: { homeTeam, awayTeam, homeMissingKey: bool, awayMissingKey: bool, date: string }
    Returns ranked list of bet predictions.
    """
    body = request.json or {}
    home = body.get('homeTeam', '')
    away = body.get('awayTeam', '')
    h_miss = int(body.get('homeMissingKey', False))
    a_miss = int(body.get('awayMissingKey', False))
    match_date = body.get('date', None)

    df = get_df()
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
        'is_derby':              0, # Fallback, could calculate
        'relegation_pressure':   0, # Fallback, could calculate
    }

    selector = get_selector()
    preds = selector.get_best_bet(features)

    return jsonify({
        'homeTeam':  home,
        'awayTeam':  away,
        'homeElo':   features['home_elo'],
        'awayElo':   features['away_elo'],
        'homeForm':  h_form,
        'awayForm':  a_form,
        'predictions': preds,
    })


@app.route('/api/teams/list', methods=['GET'])
def teams_list():
    """Simple list of team names for dropdowns."""
    df = get_df()
    return jsonify(sorted(all_teams(df)))


# ─────────────────────────────────────────────────────────────────────────────
# SPA catch-all: serve index.html for all non-api routes (React Router)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    from flask import send_from_directory
    if path and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("🚀 PL Predictor – http://localhost:5000")
    print("   Frontend: React app served at /")
    print("   Backend:  API endpoints at /api/*")
    app.run(debug=False, port=5000)
