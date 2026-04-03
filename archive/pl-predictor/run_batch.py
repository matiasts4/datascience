import pandas as pd
import numpy as np
import joblib
import os
from src.config import FEATURES

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
MODELS_DIR = os.path.join(BASE_DIR, "models")
FEATURES_PATH = os.path.join(HISTORICAL_DIR, "all_match_features_v7.csv")

df = pd.read_csv(FEATURES_PATH)
scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
m_1x2 = joblib.load(os.path.join(MODELS_DIR, 'model_1X2_Match_Winner.pkl'))
m_dc1x = joblib.load(os.path.join(MODELS_DIR, 'model_Double_Chance_1X_Home_or_Draw.pkl'))

matches = [
    ("West Ham United", "Wolves"),
    ("Arsenal", "Bournemouth"),
    ("Brentford", "Everton"),
    ("Burnley", "Brighton"),
    ("Liverpool", "Fulham"),
    ("Crystal Palace", "Newcastle United")
]

for home, away in matches:
    h_stats = df[df['home_team'] == home].iloc[-1]
    a_stats = df[df['away_team'] == away].iloc[-1]
    
    sim = {}
    for f in FEATURES:
        # Default initialization for the loop
        val = 0.0
        
        if f.startswith('h_'): val = h_stats[f]
        elif f.startswith('a_'): val = a_stats[f]
        elif f == 'home_elo': val = h_stats['home_elo']
        elif f == 'away_elo': val = a_stats['away_elo']
        elif f == 'team_home_win_pct': val = h_stats['team_home_win_pct']
        elif f == 'team_away_win_pct': val = a_stats['team_away_win_pct']
        elif f == 'h2h_home_pts_avg':
            h2h = df[(df['home_team'] == home) & (df['away_team'] == away)]
            val = h2h['h2h_home_pts_avg'].iloc[-1] if not h2h.empty else 1.5
        elif f in ['B365H', 'B365D', 'B365A']: val = 2.0
        elif f == 'precipitation_mm': val = 0.0
        elif f == 'temp_max_c': val = 15.0
        elif f == 'is_raining': val = 0
        elif f == 'is_cold': val = 0
        else: val = h_stats.get(f, 0)
        
        sim[f] = 0.0 if pd.isna(val) else val
        
    X = pd.DataFrame([sim])[FEATURES]
    X_sc = scaler.transform(X)
    
    p_1x2 = m_1x2.predict_proba(X_sc)[0]
    p_dc1x = m_dc1x.predict_proba(X_sc)[0][1]
    
    print(f"\n--- {home} vs {away} ---")
    print(f"1({p_1x2[0]*100:.1f}%) | X({p_1x2[1]*100:.1f}%) | 2({p_1x2[2]*100:.1f}%)")
    print(f"Seguridad 1X: {p_dc1x*100:.1f}%")
    if p_dc1x > 0.73:
        print(">> APUESTA RECOMENDADA: 1X (Doble Oportunidad Local)")
    elif p_1x2[2] > 0.50:
        print(">> APUESTA RECOMENDADA: X2 (Apoyar a Visita)")
    else:
        print(">> EVITAR APUESTA / RIESGO ALTO")
