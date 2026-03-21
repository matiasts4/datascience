"""
optimizer.py - Iterative grid search for the best betting simulator configuration.
Tests every valid combination of: strategy, minOdds, stake/stake_frac, and season.
Ranks results by: final bankroll, ROI%, winrate%, and # of bets placed.
"""
import sys
import os
import io
import itertools
import pandas as pd

# Silence stderr from imports
sys.stderr = io.StringIO()
from src.api import get_df, get_selector
sys.stderr = sys.__stderr__

import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# GRID CONFIG
# ─────────────────────────────────────────────────────────────────────────────
INITIAL_BANKROLL  = 100_000      # Bankroll inicial en todas las pruebas

# Estrategias
STRATEGIES        = ['fixed', 'variable']

# Cuota mínima (Filtro EV)
MIN_ODDS_OPTIONS  = [1.0, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.80, 2.00]

# Apuesta fija (en pesos absolutos)
FIXED_STAKE_OPTIONS  = [1_000, 2_500, 5_000, 10_000, 15_000, 20_000]

# Fracción máxima del bankroll para Kelly (%)
VARIABLE_FRAC_OPTIONS = [2, 3, 5, 7, 10, 15]

# Temporadas / partidos recientes por testear
SEASON_OPTIONS = [
    ('all',  60),   # últimos 60 partidos
    ('all',  120),  # últimos 120 partidos
    ('2324', None),  # temporada 2023/24 completa
    ('2223', None),  # temporada 2022/23 completa
]

# ─────────────────────────────────────────────────────────────────────────────

def run_one(df, selector, strategy, stake, min_odds, season, n_matches):
    from src.backtester import run_interactive_simulation
    try:
        res = run_interactive_simulation(
            df, selector,
            n_matches=n_matches or 999,
            initial_bankroll=INITIAL_BANKROLL,
            stake=stake,
            strategy=strategy,
            season=season,
            min_odds=min_odds
        )
        ps = res.get('performanceSummary', {})
        total_bets = ps.get('totalBets', 0)
        if total_bets == 0:
            return None
        wins   = ps.get('wins', 0)
        losses = ps.get('losses', 0)
        final  = ps.get('finalBankroll', INITIAL_BANKROLL)
        profit = final - INITIAL_BANKROLL
        roi    = round(profit / INITIAL_BANKROLL * 100, 2)
        winrate = round(wins / total_bets * 100, 1)
        return {
            'strategy':    strategy,
            'stake_param': stake,
            'min_odds':    min_odds,
            'season':      season,
            'n_matches':   n_matches or 'full',
            'total_bets':  total_bets,
            'wins':        wins,
            'losses':      losses,
            'final_bankroll': round(final, 0),
            'profit':      round(profit, 0),
            'roi_pct':     roi,
            'winrate_pct': winrate,
        }
    except Exception as e:
        return None


def main():
    print("Cargando datos y modelos... (espera ~10s)")
    df       = get_df()
    selector = get_selector()
    print("Iniciando búsqueda de hiperparámetros...")

    results = []
    total_runs = 0

    for (season, n_matches) in SEASON_OPTIONS:
        for min_odds in MIN_ODDS_OPTIONS:
            # ── ESTRATEGIA FIJA ──────────────────────────────────────────
            for stake in FIXED_STAKE_OPTIONS:
                total_runs += 1
                r = run_one(df, selector,
                            strategy='fixed', stake=stake,
                            min_odds=min_odds, season=season,
                            n_matches=n_matches)
                if r:
                    results.append(r)

            # ── ESTRATEGIA VARIABLE (Kelly) ──────────────────────────────
            for frac in VARIABLE_FRAC_OPTIONS:
                total_runs += 1
                r = run_one(df, selector,
                            strategy='variable', stake=frac,
                            min_odds=min_odds, season=season,
                            n_matches=n_matches)
                if r:
                    results.append(r)
                    
    print(f"\nEjecutadas {total_runs} pruebas sin errores → {len(results)} resultados válidos.\n")

    if not results:
        print("⚠️  No se obtuvieron resultados válidos.")
        return

    df_res = pd.DataFrame(results)

    # ── RANKING POR ROI ──────────────────────────────────────────────────────
    df_res.sort_values('roi_pct', ascending=False, inplace=True)
    
    print("=" * 110)
    print(f"{'RANK':<5} {'ESTRATEGIA':<10} {'STAKE_PARAM':<13} {'CUOTA_MIN':<11} {'TEMPORADA':<10} {'N':<7} {'APUESTAS':<10} {'WINRATE':<10} {'ROI%':<8} {'GANANCIA'}")
    print("=" * 110)
    
    for rank, (_, row) in enumerate(df_res.head(30).iterrows(), 1):
        print(
            f"{rank:<5} {row['strategy']:<10} {row['stake_param']:<13} {row['min_odds']:<11} "
            f"{row['season']:<10} {str(row['n_matches']):<7} {row['total_bets']:<10} "
            f"{row['winrate_pct']:<10} {row['roi_pct']:<8} ${row['profit']:,.0f}"
        )
    
    print("=" * 110)
    best = df_res.iloc[0]
    print(f"\n🏆 MEJOR CONFIGURACIÓN ENCONTRADA:")
    print(f"  Estrategia : {best['strategy']}")
    print(f"  Stake Param: {best['stake_param']}  {'(% máx Kelly)' if best['strategy'] == 'variable' else '(apuesta fija)'}")
    print(f"  Cuota Mín  : {best['min_odds']}")
    print(f"  Temporada  : {best['season']} / Partidos: {best['n_matches']}")
    print(f"  Apuestas   : {best['total_bets']}  (Aciertos: {best['wins']}, Fallos: {best['losses']})")
    print(f"  Winrate    : {best['winrate_pct']}%")
    print(f"  ROI        : {best['roi_pct']}%")
    print(f"  Bankroll   : ${INITIAL_BANKROLL:,.0f} → ${best['final_bankroll']:,.0f}")
    print(f"  Ganancia   : ${best['profit']:,.0f}")
    
    # Save to CSV
    df_res.to_csv('optimization_results.csv', index=False, encoding='utf-8')
    print(f"\n📊 Resultados completos guardados en: optimization_results.csv")

if __name__ == '__main__':
    main()
