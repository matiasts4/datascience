import pandas as pd
import joblib
import os
import requests
from src.config import FEATURES

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
MODELS_DIR = os.path.join(BASE_DIR, "models")
FEATURES_PATH = os.path.join(HISTORICAL_DIR, "all_match_features_v7.csv")

df = pd.read_csv(FEATURES_PATH)
scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
m_1x2 = joblib.load(os.path.join(MODELS_DIR, 'model_1X2_Match_Winner.pkl'))
m_dc1x = joblib.load(os.path.join(MODELS_DIR, 'model_Double_Chance_1X_Home_or_Draw.pkl'))

home = "West Ham United"
away = "Wolves"
odds_h = 1.83
odds_d = 3.75
odds_a = 4.20

h_stats = df[df['home_team'] == home].iloc[-1]
a_stats = df[df['away_team'] == away].iloc[-1]

sim = {}
for f in FEATURES:
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
    elif f == 'B365H': val = odds_h
    elif f == 'B365D': val = odds_d
    elif f == 'B365A': val = odds_a
    elif f == 'precipitation_mm': val = 0.0
    elif f == 'temp_max_c': val = 15.0
    elif f == 'is_raining': val = 0
    elif f == 'is_cold': val = 0
    else: val = h_stats.get(f, 0)
    
    sim[f] = 0.0 if pd.isna(val) else val

X = pd.DataFrame([sim])[FEATURES].fillna(0)
X_sc = scaler.transform(X)

p_dc1x = m_dc1x.predict_proba(X_sc)[0][1]

print("=========================================")
print(f"Probabilidad Doble Oportunidad 1X: {p_dc1x*100:.2f}%")
print("=========================================")
