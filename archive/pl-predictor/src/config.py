import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
FEATURES_PATH = os.path.join(HISTORICAL_DIR, "all_match_features_v2.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# ─────────────────────────────────────────────────────────────────────────────
# ACTIVE MARKETS — Cuota esperada realista ≥ 1.50 con EV potencialmente positivo
# ─────────────────────────────────────────────────────────────────────────────
TARGETS = {
    "1X2 (Match Winner)":              'target_1x2',
    "Double Chance 1X (Home or Draw)": 'target_dc_1X',
    "Double Chance X2 (Away or Draw)": 'target_dc_X2',
    "Over 2.5 Goals":                  'target_over_2_5_goals',
    "Under 2.5 Goals":                 'target_under_2_5_goals',
    "BTTS (Both Teams To Score)":      'target_btts',
    "BTTS - No":                       'target_btts_no',
    "Home Clean Sheet":                'target_home_clean_sheet',
}

# ─────────────────────────────────────────────────────────────────────────────
# DISABLED MARKETS — Eliminados por EV negativo estructural
# ─────────────────────────────────────────────────────────────────────────────
# "Home Team Over 0.5 Goals"   → Accuracy ~88% pero cuota implícita ~1.10. EV ≈ -5%.
# "Away Team Over 0.5 Goals"   → Accuracy ~82% pero cuota implícita ~1.15. EV ≈ -5%.
# "Over 22.5 Fouls"            → Accuracy ~58%, cuota ~1.55. EV ≈ -10%.
# "Under 22.5 Fouls"           → Accuracy ~60%, cuota ~1.55. EV ≈ -7%.
# "Over 4.5 Cards"             → Evento raro (~35%), cuota real ~2.50. Modelo no tiene ventaja.
# "Under 4.5 Cards"            → Demasiado frecuente; odds ~1.30. EV negativo.
# "Away Clean Sheet"           → Baja frecuencia, alta varianza. Accuracy inconsistente.
# "Home Win to Nil"            → Evento compuesto (<25% partidos). Alta varianza, bajo EV.
# ─────────────────────────────────────────────────────────────────────────────

FEATURES = [
    'home_elo', 'away_elo',
    'h_missing_key_player', 'a_missing_key_player',
    'h_l5_pts', 'h_l5_sh', 'h_l5_sot', 'h_l5_sot_c', 'h_l5_gf', 'h_l5_ga', 'h_l5_fls', 'h_l5_atk', 'h_l5_def',
    'a_l5_pts', 'a_l5_sh', 'a_l5_sot', 'a_l5_sot_c', 'a_l5_gf', 'a_l5_ga', 'a_l5_fls', 'a_l5_atk', 'a_l5_def',
    'referee_avg_cards_history', 'team_home_win_pct', 'team_away_win_pct', 'h2h_home_pts_avg'
]
