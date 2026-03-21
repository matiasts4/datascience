"""
optimizer_fast.py - Fast iterative grid search.
Loads the data ONCE, vectorizes all 16 model predictions ONCE,
then evaluates every parameter combination instantly in memory.
"""
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from src.api import get_df, get_selector
from src.backtester import evaluate_market_result

INITIAL_BANKROLL = 100_000.0

print("Cargando datos y modelos...")
df = get_df()
selector = get_selector()

# Use all completed matches
completed = df[df['home_goals'].notna()].copy()
from src.config import FEATURES
X_scaled = selector.scaler.transform(completed[FEATURES])

market_names  = list(selector.models.keys())
n_markets     = len(market_names)
n_matches     = len(completed)

print(f"  Partidos: {n_matches} | Mercados: {n_markets}")

# ── Pre-compute ALL probabilities (n_matches x n_markets) ──────────────────
print("Pre-calculando probabilidades de los 16 mercados...")
all_probs = np.zeros((n_matches, n_markets))
for i, (mkt, mdl) in enumerate(selector.models.items()):
    if len(mdl.classes_) == 2 and 1 in mdl.classes_:
        idx = list(mdl.classes_).index(1)
        all_probs[:, i] = mdl.predict_proba(X_scaled)[:, idx]
    else:
        all_probs[:, i] = np.max(mdl.predict_proba(X_scaled), axis=1)

# ── Pre-compute simulated bookie odds (n_matches x n_markets) ─────────────
all_odds = np.where(all_probs > 0, (1.0 / all_probs) * 0.95, 1.01)
all_odds = np.maximum(all_odds, 1.01)

# ── Pre-compute match outcomes for each market ─────────────────────────────
print("Evaluando resultados históricos...")
outcomes = np.zeros((n_matches, n_markets), dtype=bool)
for j, mkt in enumerate(market_names):
    for i, (_, row) in enumerate(completed.iterrows()):
        hg, ag = row['home_goals'], row['away_goals']
        r1x2  = row.get('result_1x2')
        won = evaluate_market_result(mkt, hg, ag, r1x2)
        if mkt == '1X2':
            helo = row.get('home_elo', 1500)
            aelo = row.get('away_elo', 1500)
            won = (hg > ag) if helo >= aelo else (ag > hg)
        outcomes[i, j] = won

# ── Season index (for slicing) ─────────────────────────────────────────────
completed_reset = completed.reset_index(drop=True)
season_col = completed_reset['season'] if 'season' in completed_reset.columns else None

def get_season_mask(season_val):
    if season_val == 'all':
        return np.ones(n_matches, dtype=bool)
    if season_col is not None:
        try:
            return (season_col == int(season_val)).values
        except:
            return (season_col.astype(str) == season_val).values
    return np.ones(n_matches, dtype=bool)

# ─────────────────────────────────────────────────────────────────────────────
# GRID PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────
MIN_ODDS_OPTIONS    = [1.00, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.80, 2.00]
FIXED_STAKES        = [1_000, 2_500, 5_000, 10_000, 15_000, 20_000]
VARIABLE_FRACS      = [2, 3, 5, 7, 10, 15]   # % fraction of bankroll (Kelly)
SEASON_OPTIONS      = [
    ('all',   -60),   # últimos 60 partidos
    ('all',  -120),   # últimos 120 partidos
    ('2324', None),
    ('2223', None),
]

# ─────────────────────────────────────────────────────────────────────────────
# VECTORIZED SIMULATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def simulate(slice_idx, strategy, stake_param, min_odds_threshold):
    bankroll = INITIAL_BANKROLL
    wins = losses = total_bets = 0

    for i in slice_idx:
        # Find the best valid bet (highest prob where odds >= threshold)
        row_odds  = all_odds[i]
        row_probs = all_probs[i]
        
        # Filter by min_odds
        valid_mask = row_odds >= min_odds_threshold
        if not valid_mask.any():
            continue
        
        # Among valid, pick highest probability
        valid_probs = np.where(valid_mask, row_probs, -1)
        best_j = int(np.argmax(valid_probs))
        
        if valid_probs[best_j] <= 0:
            continue
        
        prob      = row_probs[best_j]
        odds_used = row_odds[i, best_j] if row_odds.ndim > 1 else row_odds[best_j]
        
        # Compute stake
        if strategy == 'variable':
            frac = stake_param / 100.0
            stake_amount = max(bankroll * prob * frac, 1.0)
        else:
            stake_amount = float(stake_param)
        
        stake_amount = min(stake_amount, bankroll)
        if stake_amount < 1.0 or bankroll < 1.0:
            continue
            
        won = outcomes[i, best_j]
        bankroll -= stake_amount
        if won:
            bankroll += stake_amount * odds_used
            wins += 1
        else:
            losses += 1
        total_bets += 1
    
    return total_bets, wins, losses, bankroll


# ─────────────────────────────────────────────────────────────────────────────
# RUN ALL COMBINATIONS
# ─────────────────────────────────────────────────────────────────────────────
print("Iniciando grid search...\n")
records = []

# Precompute sorted index for 'all'
all_idx_sorted   = np.arange(n_matches)  # completed is already sorted by date
last60_idx       = all_idx_sorted[-60:]
last120_idx      = all_idx_sorted[-120:]

season_masks = {
    ('all',   -60):  last60_idx,
    ('all',  -120):  last120_idx,
    ('2324', None):  np.where(get_season_mask('2324'))[0],
    ('2223', None):  np.where(get_season_mask('2223'))[0],
}

total = 0
for (season_val, n_tail), min_odds in [(s, m) for s in SEASON_OPTIONS for m in MIN_ODDS_OPTIONS]:
    idx = season_masks[(season_val, n_tail)]
    if len(idx) == 0:
        continue

    for s_strategy, s_params in [('fixed', FIXED_STAKES), ('variable', VARIABLE_FRACS)]:
        for param in s_params:
            total += 1
            tb, w, l, final = simulate(idx, s_strategy, param, min_odds)
            if tb == 0:
                continue
            profit = final - INITIAL_BANKROLL
            roi    = profit / INITIAL_BANKROLL * 100
            wr     = w / tb * 100
            records.append({
                'strategy':    s_strategy,
                'stake_param': param,
                'min_odds':    min_odds,
                'season':      season_val,
                'n':           len(idx),
                'bets':        tb,
                'wins':        w,
                'losses':      l,
                'winrate%':    round(wr, 1),
                'roi%':        round(roi, 2),
                'final':       round(final, 0),
                'ganancia':    round(profit, 0),
            })

print(f"Combinaciones testadas: {total} | Válidas: {len(records)}\n")

if not records:
    print("Sin resultados.")
    exit()

df_res = pd.DataFrame(records).sort_values('roi%', ascending=False)

print("=" * 120)
print(f"{'#':<4}{'ESTRATEGIA':<11}{'PARAM':<8}{'CUOTA_MIN':<11}{'TEMPORADA':<10}{'N_PARTIDOS':<12}{'APUESTAS':<10}{'WINRATE':<10}{'ROI%':<10}{'GANANCIA'}")
print("=" * 120)
for rank, (_, r) in enumerate(df_res.head(20).iterrows(), 1):
    print(f"{rank:<4}{r['strategy']:<11}{r['stake_param']:<8}{r['min_odds']:<11}{r['season']:<10}{r['n']:<12}{r['bets']:<10}{r['winrate%']:<10}{r['roi%']:<10}${r['ganancia']:,.0f}")

print("=" * 120)
best = df_res.iloc[0]
print(f"""
🏆  MEJOR CONFIGURACIÓN:
   Estrategia : {best['strategy']}  ({'% Kelly' if best['strategy'] == 'variable' else 'Apuesta fija'})
   Parámetro  : {best['stake_param']}  {"(% máx del capital)" if best['strategy'] == 'variable' else "(pesos por apuesta)"}
   Cuota Mínima: {best['min_odds']}
   Temporada  : {best['season']} ({best['n']} partidos)
   Apuestas   : {best['bets']}  (Gana: {best['wins']} | Pierde: {best['losses']})
   Winrate    : {best['winrate%']}%
   ROI        : {best['roi%']}%
   Capital    : ${INITIAL_BANKROLL:,.0f}  →  ${best['final']:,.0f}
   Ganancia   : ${best['ganancia']:,.0f}
""")

df_res.to_csv('optimization_results.csv', index=False, encoding='utf-8')
print("📊 Guardado en: optimization_results.csv")
