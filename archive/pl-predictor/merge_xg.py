"""
Paso 1.4 (Fase 1) — Fusiona datasets:
  - all_match_features_v3_odds.csv  (features + cuotas reales)
  - understat_xg.csv                (xG por partido de Understat)
Genera: all_match_features_v4_xg.csv (dataset final Fase 1)
"""

import pandas as pd
import os

BASE = "data/historical"
FEATURES_V3 = os.path.join(BASE, "all_match_features_v3_odds.csv")
XG_FILE     = os.path.join(BASE, "understat_xg.csv")
OUT_FILE    = os.path.join(BASE, "all_match_features_v4_xg.csv")

# Mapa de nombres de equipo Understat → nombres usados en nuestro dataset
TEAM_MAP = {
    # Understat name -> Features dataset name
    "Manchester City":            "Manchester City",
    "Manchester United":          "Manchester Utd",
    "Newcastle United":           "Newcastle United",
    "Tottenham":                   "Tottenham Hotspur",
    "Tottenham Hotspur":           "Tottenham Hotspur",
    "Wolverhampton Wanderers":     "Wolves",
    "Wolves":                      "Wolves",
    "Nottingham Forest":           "Nottingham Forest",
    "West Ham United":             "West Ham United",
    "West Ham":                    "West Ham United",
    "West Bromwich Albion":        "West Brom",
    "West Brom":                   "West Brom",
    "Sheffield United":            "Sheffield Utd",
    "Leeds United":                "Leeds United",
    "Leeds":                       "Leeds United",
    "Leicester City":              "Leicester City",
    "Leicester":                   "Leicester City",
    "Burnley":                     "Burnley",
    "Arsenal":                     "Arsenal",
    "Chelsea":                     "Chelsea",
    "Liverpool":                   "Liverpool",
    "Everton":                     "Everton",
    "Southampton":                 "Southampton",
    "Watford":                     "Watford",
    "Brighton":                    "Brighton",
    "Crystal Palace":              "Crystal Palace",
    "Bournemouth":                 "Bournemouth",
    "Swansea":                     "Swansea City",
    "Swansea City":                "Swansea City",
    "Huddersfield":                "Huddersfield Town",
    "Huddersfield Town":           "Huddersfield Town",
    "Cardiff":                     "Cardiff City",
    "Cardiff City":                "Cardiff City",
    "Norwich":                     "Norwich City",
    "Norwich City":                "Norwich City",
    "Brentford":                   "Brentford",
    "Luton":                       "Luton Town",
    "Luton Town":                  "Luton Town",
    "Ipswich":                     "Ipswich Town",
    "Ipswich Town":                "Ipswich Town",
    "Fulham":                      "Fulham",
    "Aston Villa":                 "Aston Villa",
    "Stoke":                       "Stoke City",
    "Stoke City":                  "Stoke City",
}

def normalize(name):
    return TEAM_MAP.get(str(name).strip(), str(name).strip())


def main():
    print("Cargando datasets...")
    df_feat = pd.read_csv(FEATURES_V3)
    df_xg   = pd.read_csv(XG_FILE)

    df_feat['date'] = pd.to_datetime(df_feat['date'], errors='coerce')
    df_xg['date']   = pd.to_datetime(df_xg['date'], errors='coerce')

    # Normalizar nombres en xG
    df_xg['home_team_norm'] = df_xg['home_team'].apply(normalize)
    df_xg['away_team_norm'] = df_xg['away_team'].apply(normalize)

    xg_keys = df_xg[['date', 'home_team_norm', 'away_team_norm', 'home_xg', 'away_xg']].copy()
    xg_keys.rename(columns={'home_team_norm': 'home_team', 'away_team_norm': 'away_team'}, inplace=True)
    xg_keys = xg_keys.drop_duplicates(subset=['date', 'home_team', 'away_team'])

    print(f"Features rows: {len(df_feat)}")
    print(f"xG rows:       {len(xg_keys)}")

    merged = pd.merge(df_feat, xg_keys, on=['date', 'home_team', 'away_team'], how='left')

    matched = merged['home_xg'].notna().sum()
    print(f"\n✅ xG merged en {matched}/{len(merged)} partidos ({100*matched/len(merged):.1f}%).")

    merged.to_csv(OUT_FILE, index=False)
    print(f"💾 Guardado: {OUT_FILE}")
    print(f"   Columnas nuevas: home_xg, away_xg")

    # Mostrar distribución del xG para validar
    print("\nEstadísticas xG:")
    print(merged[['home_xg', 'away_xg']].describe().to_string())


if __name__ == "__main__":
    main()
