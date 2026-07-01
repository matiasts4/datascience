import os
import sqlite3
import json

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../pl_web.db"))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upcoming_matches (
            id TEXT PRIMARY KEY,
            date TEXT,
            home_team TEXT,
            away_team TEXT,
            home_elo REAL,
            away_elo REAL,
            top_market TEXT,
            top_probability REAL,
            top_confidence TEXT,
            top_pick INTEGER,
            top_fair_odds REAL,
            top_ev REAL,
            top_stake_pct REAL,
            all_predictions TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_upcoming_matches(matches_list):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clear the table first
    cursor.execute("DELETE FROM upcoming_matches")
    
    for m in matches_list:
        top_pred = m.get('topPrediction') or {}
        cursor.execute("""
            INSERT INTO upcoming_matches (
                id, date, home_team, away_team, home_elo, away_elo,
                top_market, top_probability, top_confidence, top_pick,
                top_fair_odds, top_ev, top_stake_pct, all_predictions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m['id'],
            m['date'],
            m['homeTeam'],
            m['awayTeam'],
            m['homeElo'],
            m['awayElo'],
            top_pred.get('Market'),
            top_pred.get('Probability'),
            top_pred.get('Confidence'),
            top_pred.get('Pick'),
            top_pred.get('FairOdds'),
            top_pred.get('ExpectedValue'),
            top_pred.get('RecommendedStakePct'),
            json.dumps(m.get('allPredictions', []))
        ))
        
    conn.commit()
    conn.close()

def get_upcoming_matches():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM upcoming_matches ORDER BY date ASC")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        top_pred = None
        if r['top_market']:
            top_pred = {
                'Market': r['top_market'],
                'Probability': r['top_probability'],
                'Confidence': r['top_confidence'],
                'Pick': r['top_pick'],
                'FairOdds': r['top_fair_odds'],
                'ExpectedValue': r['top_ev'],
                'RecommendedStakePct': r['top_stake_pct']
            }
        
        result.append({
            'id': r['id'],
            'date': r['date'],
            'homeTeam': r['home_team'],
            'awayTeam': r['away_team'],
            'homeElo': r['home_elo'],
            'awayElo': r['away_elo'],
            'topPrediction': top_pred,
            'allPredictions': json.loads(r['all_predictions'] or '[]')
        })
    return result
