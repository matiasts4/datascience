import pandas as pd, joblib, os, sys

BASE_DIR     = os.path.abspath(os.path.dirname(__file__))
MODELS_DIR   = os.path.join(BASE_DIR, "models")
FEATURES_PATH = os.path.join(BASE_DIR, "data", "historical", "all_match_features_v2.csv")

sys.path.insert(0, BASE_DIR)
from src.config import FEATURES

df      = pd.read_csv(FEATURES_PATH)
scaler  = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
m_1x2   = joblib.load(os.path.join(MODELS_DIR, 'model_1X2_Match_Winner.pkl'))
m_dc1x  = joblib.load(os.path.join(MODELS_DIR, 'model_Double_Chance_1X_Home_or_Draw.pkl'))
m_dcx2  = joblib.load(os.path.join(MODELS_DIR, 'model_Double_Chance_X2_Away_or_Draw.pkl'))
m_btts  = joblib.load(os.path.join(MODELS_DIR, 'model_BTTS_Both_Teams_To_Score.pkl'))
m_o25   = joblib.load(os.path.join(MODELS_DIR, 'model_Over_2_5_Goals.pkl'))
m_u25   = joblib.load(os.path.join(MODELS_DIR, 'model_Under_2_5_Goals.pkl'))
m_hcs   = joblib.load(os.path.join(MODELS_DIR, 'model_Home_Clean_Sheet.pkl'))

home = "Manchester City"
away = "Liverpool"

# Cuotas reales aproximadas FA Cup semi (ajusta si tienes cuotas en vivo)
odds_h, odds_d, odds_a = 1.90, 3.60, 4.00

h_stats = df[(df['home_team'] == home) & df['h_l5_atk'].notna()].iloc[-1]
a_stats = df[(df['away_team'] == away) & df['a_l5_atk'].notna()].iloc[-1]

sim = {}
for f in FEATURES:
    if   f.startswith('h_'):          sim[f] = h_stats.get(f, 0)
    elif f.startswith('a_'):          sim[f] = a_stats.get(f, 0)
    elif f == 'home_elo':             sim[f] = h_stats['home_elo']
    elif f == 'away_elo':             sim[f] = a_stats['away_elo']
    elif f == 'team_home_win_pct':    sim[f] = h_stats['team_home_win_pct']
    elif f == 'team_away_win_pct':    sim[f] = a_stats['team_away_win_pct']
    elif f == 'h2h_home_pts_avg':
        h2h = df[(df['home_team'] == home) & (df['away_team'] == away)]
        sim[f] = h2h['h2h_home_pts_avg'].iloc[-1] if not h2h.empty else 1.5
    elif f == 'B365H':               sim[f] = odds_h
    elif f == 'B365D':               sim[f] = odds_d
    elif f == 'B365A':               sim[f] = odds_a
    elif f == 'precipitation_mm':    sim[f] = 0.0
    elif f == 'temp_max_c':          sim[f] = 14.0
    elif f == 'is_raining':          sim[f] = 0
    elif f == 'is_cold':             sim[f] = 0
    else:                            sim[f] = h_stats.get(f, 0)

X    = pd.DataFrame([sim])[FEATURES].fillna(0)
X_sc = scaler.transform(X)

p_1x2  = m_1x2.predict_proba(X_sc)[0]
p_dc1x = m_dc1x.predict_proba(X_sc)[0][1]
p_dcx2 = m_dcx2.predict_proba(X_sc)[0][1]
p_btts = m_btts.predict_proba(X_sc)[0][1]
p_o25  = m_o25.predict_proba(X_sc)[0][1]
p_u25  = m_u25.predict_proba(X_sc)[0][1]
p_hcs  = m_hcs.predict_proba(X_sc)[0][1]

def ev(p, odd): return round(p * odd - 1, 4)

print()
print("=" * 62)
print("  🔮  ORÁCULO — Manchester City vs Liverpool  🔮")
print("=" * 62)
print(f"  🏟  Wembley | 14°C, cielo despejado")
print(f"  📊 Cuotas usadas: City {odds_h} | Empate {odds_d} | Liverpool {odds_a}")
print()
print("┌── PROBABILIDADES IA ──────────────────────────────────────┐")
print(f"│  ⚽ Victoria City      :  {p_1x2[0]*100:5.1f}%  (cuota impl. {1/p_1x2[0]:.2f}x)")
print(f"│  🤝 Empate             :  {p_1x2[1]*100:5.1f}%  (cuota impl. {1/p_1x2[1]:.2f}x)")
print(f"│  ⚽ Victoria Liverpool :  {p_1x2[2]*100:5.1f}%  (cuota impl. {1/p_1x2[2]:.2f}x)")
print("├── MERCADOS ESPECIALES ─────────────────────────────────────┤")
print(f"│  🛡  1X (City o Empate):  {p_dc1x*100:.1f}%   EV: {ev(p_dc1x,1.28):+.4f}")
print(f"│  🛡  X2 (Empate o Liv):   {p_dcx2*100:.1f}%   EV: {ev(p_dcx2,1.40):+.4f}")
print(f"│  ⚡ BTTS (ambos marcan):  {p_btts*100:.1f}%   EV: {ev(p_btts,1.85):+.4f}")
print(f"│  📈 Over 2.5 Goles:       {p_o25*100:.1f}%   EV: {ev(p_o25,1.80):+.4f}")
print(f"│  📉 Under 2.5 Goles:      {p_u25*100:.1f}%   EV: {ev(p_u25,2.00):+.4f}")
print(f"│  🧤 Clean Sheet City:     {p_hcs*100:.1f}%")
print("├── FEATURES CLAVE (nuevas v2) ─────────────────────────────┤")
missing_h = int(h_stats.get('h_missing_key_player', 0))
missing_a = int(a_stats.get('a_missing_key_player', 0))
print(f"│  City      — Atk L5: {h_stats.get('h_l5_atk',0):.2f} | Def L5: {h_stats.get('h_l5_def',0):.2f} | Baja: {'⚠ SÍ' if missing_h else '✅ NO'}")
print(f"│  Liverpool — Atk L5: {a_stats.get('a_l5_atk',0):.2f} | Def L5: {a_stats.get('a_l5_def',0):.2f} | Baja: {'⚠ SÍ' if missing_a else '✅ NO'}")
print("├── 💡 RECOMENDACIÓN BOT ─────────────────────────────────────┤")

recs = []
if ev(p_btts, 1.85) > 0:   recs.append(f"⚡ BTTS ({p_btts*100:.1f}%)  EV: {ev(p_btts,1.85):+.4f}")
if ev(p_o25, 1.80) > 0:    recs.append(f"📈 Over 2.5 ({p_o25*100:.1f}%)  EV: {ev(p_o25,1.80):+.4f}")
if ev(p_dc1x, 1.28) > 0:   recs.append(f"🛡  1X ({p_dc1x*100:.1f}%)  EV: {ev(p_dc1x,1.28):+.4f}")
if ev(p_dcx2, 1.40) > 0:   recs.append(f"🛡  X2 ({p_dcx2*100:.1f}%)  EV: {ev(p_dcx2,1.40):+.4f}")

if recs:
    print("│  👉 Value Bets encontradas:")
    for r in recs:
        print(f"│     • {r}")
else:
    print("│  ⚠️  No se detectan value bets claras con estas cuotas.")

print("└───────────────────────────────────────────────────────────┘")
