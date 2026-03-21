"""
diagnose_ev.py - Diagnoses why the simulator shows negative ROI.
Computes real EV per market on the 2023/24 holdout test set.
"""
import numpy as np
import pandas as pd
import warnings, collections
warnings.filterwarnings('ignore')

from src.api import get_df, get_selector
from src.config import FEATURES
from src.backtester import evaluate_market_result

df = get_df()
completed = df[df['home_goals'].notna()].copy()
selector = get_selector()

# 2023/24 season - 100% out-of-sample test data
test = completed[completed['season'] == 2324].sort_values('date').reset_index(drop=True)
print(f"Partidos 23/24 (fuera del entrenamiento): {len(test)}\n")

X = selector.scaler.transform(test[FEATURES])
markets = list(selector.models.keys())
n = len(markets)

all_probs = np.zeros((len(test), n))
for i, (m, mdl) in enumerate(selector.models.items()):
    if len(mdl.classes_) == 2 and 1 in mdl.classes_:
        idx = list(mdl.classes_).index(1)
        all_probs[:, i] = mdl.predict_proba(X)[:, idx]
    else:
        all_probs[:, i] = np.max(mdl.predict_proba(X), axis=1)

# Simulated bookie odds with 5% vig
all_odds = np.maximum(np.where(all_probs > 0, (1.0 / all_probs) * 0.95, 1.01), 1.01)

# Pre-compute outcomes
outcomes = np.zeros((len(test), n), dtype=bool)
for j, mkt in enumerate(markets):
    for i, row in test.iterrows():
        hg, ag = row['home_goals'], row['away_goals']
        r1x2 = row.get('result_1x2')
        won = evaluate_market_result(mkt, hg, ag, r1x2)
        if mkt == '1X2':
            won = (hg > ag) if row.get('home_elo', 1500) >= row.get('away_elo', 1500) else (ag > hg)
        outcomes[i, j] = won

# ─── EVALUATE DIFFERENT min_odds THRESHOLDS ────────────────────────────────
print("=" * 75)
print("IMPACTO DEL UMBRAL DE CUOTA MÍNIMA (Kelly 15%, Temporada 23/24)")
print("=" * 75)
print(f"{'Cuota Min':<12} {'Apuestas':<10} {'Winrate':<10} {'EV Prom':<12} {'ROI Simulado'}")
print("-" * 75)

BANKROLL = 100_000.0
for min_odds in [1.0, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.80, 2.00, 2.20, 2.50]:
    bankroll = BANKROLL
    wins = losses = bets = 0
    for i in range(len(test)):
        valid = all_odds[i] >= min_odds
        if not valid.any():
            continue
        best_j = int(np.argmax(np.where(valid, all_probs[i], -1)))
        if all_probs[i, best_j] <= 0:
            continue
        prob = all_probs[i, best_j]
        odds_v = all_odds[i, best_j]
        stake = max(bankroll * prob * 0.15, 1.0)
        stake = min(stake, bankroll)
        if bankroll < 1.0:
            break
        bankroll -= stake
        if outcomes[i, best_j]:
            bankroll += stake * odds_v
            wins += 1
        else:
            losses += 1
        bets += 1
    if bets == 0:
        continue
    wr = wins / bets * 100
    roi = (bankroll - BANKROLL) / BANKROLL * 100
    print(f"{min_odds:<12.2f} {bets:<10} {wr:<10.1f} {'--':<12} {roi:+.2f}%  (${bankroll:,.0f})")

# ─── BREAKDOWN BY MARKET at min_odds=1.8 ─────────────────────────────────
print("\n" + "=" * 75)
print("DESGLOSE POR MERCADO (cuota mín 1.80, Kelly 15%)")
print("=" * 75)
print(f"{'Mercado':<32} {'Elegido':<8} {'Winrate':<10} {'Odds Prom':<12} {'EV Prom'}")
print("-" * 75)

mkt_stats = collections.defaultdict(lambda: {'n': 0, 'w': 0, 'odds_sum': 0, 'ev_sum': 0})
for i in range(len(test)):
    valid = all_odds[i] >= 1.80
    if not valid.any():
        continue
    best_j = int(np.argmax(np.where(valid, all_probs[i], -1)))
    if all_probs[i, best_j] <= 0:
        continue
    prob = all_probs[i, best_j]
    odds_v = all_odds[i, best_j]
    mkt = markets[best_j]
    ev = prob * odds_v - 1
    mkt_stats[mkt]['n'] += 1
    mkt_stats[mkt]['w'] += outcomes[i, best_j]
    mkt_stats[mkt]['odds_sum'] += odds_v
    mkt_stats[mkt]['ev_sum'] += ev

for m, s in sorted(mkt_stats.items(), key=lambda x: -x[1]['n']):
    wr = s['w'] / s['n'] * 100
    avg_odds = s['odds_sum'] / s['n']
    avg_ev = s['ev_sum'] / s['n'] * 100
    print(f"{m:<32} {s['n']:<8} {wr:<10.1f} {avg_odds:<12.2f} {avg_ev:+.1f}%")

print("\n=> EV negativo = el modelo pierde dinero en ese mercado a largo plazo.")
print("   EV positivo = el modelo tiene ventaja matemática real.")
