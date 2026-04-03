"""
integrar_xg.py
--------------
Descarga datos de Expected Goals (xG) desde el repositorio oficial de Fantasy Premier League
(vaastav/Fantasy-Premier-League en GitHub). Disponible desde la temporada 2022-23.

Genera columnas:
  - h_match_xg  : xG acumulado del equipo local en ese partido
  - a_match_xg  : xG acumulado del equipo visitante en ese partido
  - xg_diff     : ventaja de xG del local sobre el visita (positiva = local dominó)
  - h_l5_xg     : promedio de xG local en los últimos 5 partidos (forma real reciente)
  - a_l5_xg     : promedio de xG visita en los últimos 5 partidos

Luego fusiona estas columnas al archivo all_match_features_v3.csv
y guarda el resultado en all_match_features_v4.csv listo para re-entrenar el modelo.
"""

import pandas as pd
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
INPUT_PATH  = os.path.join(HISTORICAL_DIR, "all_match_features_v3.csv")
OUTPUT_PATH = os.path.join(HISTORICAL_DIR, "all_match_features_v4.csv")

# ── Temporadas con xG disponible en el repo público (22/23 en adelante) ──────
SEASONS_XG = {
    "2022-23": "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/gws/merged_gw.csv",
    "2023-24": "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/gws/merged_gw.csv",
    "2024-25": "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/gws/merged_gw.csv",
}

# ── Mapeo de nombres de equipo FPL → nombres en nuestro dataset principal ────
TEAM_NAME_MAP = {
    "Arsenal":          "Arsenal",
    "Aston Villa":      "Aston Villa",
    "Brentford":        "Brentford",
    "Brighton":         "Brighton",
    "Burnley":          "Burnley",
    "Chelsea":          "Chelsea",
    "Crystal Palace":   "Crystal Palace",
    "Everton":          "Everton",
    "Fulham":           "Fulham",
    "Leeds":            "Leeds United",
    "Leicester":        "Leicester City",
    "Liverpool":        "Liverpool",
    "Luton":            "Luton Town",
    "Man City":         "Manchester City",
    "Man Utd":          "Manchester Utd",
    "Newcastle":        "Newcastle United",
    "Nott'm Forest":    "Nottingham Forest",
    "Sheffield Utd":    "Sheffield United",
    "Southampton":      "Southampton",
    "Spurs":            "Tottenham Hotspur",
    "West Ham":         "West Ham United",
    "Wolves":           "Wolves",
    "Bournemouth":      "Bournemouth",
    "Ipswich":          "Ipswich Town",
}

def load_fpl_xg():
    all_dfs = []
    for season, url in SEASONS_XG.items():
        try:
            df = pd.read_csv(url)
            if "expected_goals" not in df.columns:
                print(f"  ⚠  {season}: No 'expected_goals' column, skipping.")
                continue
            df = df[["name", "team", "kickoff_time",
                      "expected_goals", "expected_goals_conceded",
                      "was_home", "GW"]].copy()
            df["season"] = season
            all_dfs.append(df)
            print(f"  ✓  {season}: {len(df)} player rows loaded.")
        except Exception as e:
            print(f"  ✗  {season}: {e}")
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()


def aggregate_to_match_level(fpl_df):
    """Suma xG de todos los jugadores del mismo equipo por partido."""
    fpl_df["kickoff_time"] = pd.to_datetime(fpl_df["kickoff_time"]).dt.date
    fpl_df["team_mapped"]  = fpl_df["team"].map(TEAM_NAME_MAP)

    team_match = (
        fpl_df.groupby(["team_mapped", "kickoff_time", "was_home", "GW"])
        .agg(
            match_xg = ("expected_goals",           "sum"),
            match_xgc= ("expected_goals_conceded",  "sum"),
        )
        .reset_index()
    )
    return team_match


def build_xg_features(team_match):
    """Construye h_match_xg, a_match_xg, xg_diff, h_l5_xg, a_l5_xg."""
    home_df = team_match[team_match["was_home"]].copy()
    away_df = team_match[~team_match["was_home"]].copy()

    home_df = home_df.rename(columns={"team_mapped": "home_team",
                                       "kickoff_time": "date",
                                       "match_xg": "h_match_xg",
                                       "match_xgc": "h_match_xgc"})
    away_df = away_df.rename(columns={"team_mapped": "away_team",
                                       "kickoff_time": "date",
                                       "match_xg": "a_match_xg",
                                       "match_xgc": "a_match_xgc"})

    merged = pd.merge(
        home_df[["date", "home_team", "GW", "h_match_xg", "h_match_xgc"]],
        away_df[["date", "away_team", "GW", "a_match_xg", "a_match_xgc"]],
        on=["date", "GW"],
        how="inner"
    )
    merged["xg_diff"] = merged["h_match_xg"] - merged["a_match_xg"]

    # Rolling xG últimos 5 partidos por equipo
    merged = merged.sort_values("date")
    merged["h_l5_xg"] = merged.groupby("home_team")["h_match_xg"].transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).mean()
    )
    merged["a_l5_xg"] = merged.groupby("away_team")["a_match_xg"].transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).mean()
    )
    merged["date"] = pd.to_datetime(merged["date"])
    return merged


def main():
    print("=" * 60)
    print("Integrando Expected Goals (xG) al modelo de apuestas")
    print("=" * 60)

    print("\n[1/4] Descargando datos de xG desde GitHub (FPL oficial)...")
    fpl_df = load_fpl_xg()
    if fpl_df.empty:
        print("ERROR: No se pudo obtener ningún dato de xG. Abortando.")
        return

    print("\n[2/4] Agregando xG a nivel de partido (suma por equipo)...")
    team_match = aggregate_to_match_level(fpl_df)
    print(f"      Generados {len(team_match)} registros equipo-partido.")

    print("\n[3/4] Calculando métricas de xG acumuladas y forma reciente...")
    xg_features = build_xg_features(team_match)
    print(f"      Partidos con xG cruzado: {len(xg_features)}")

    print("\n[4/4] Fusionando con all_match_features_v3.csv...")
    main_df = pd.read_csv(INPUT_PATH)
    main_df["date"] = pd.to_datetime(main_df["date"])

    result_df = pd.merge(
        main_df,
        xg_features[["date", "home_team", "away_team",
                      "h_match_xg", "a_match_xg", "xg_diff",
                      "h_l5_xg", "a_l5_xg"]],
        on=["date", "home_team", "away_team"],
        how="left"
    )

    # Imputamos NaN con la media (partidos pre-2022 no tienen xG disponible)
    for col in ["h_match_xg", "a_match_xg", "xg_diff", "h_l5_xg", "a_l5_xg"]:
        result_df[col] = result_df[col].fillna(result_df[col].mean())

    coverage = result_df["h_match_xg"].notna().sum()
    pct = (result_df["h_match_xg"] > 0).mean() * 100
    print(f"      Cobertura de xG: {pct:.1f}% de partidos con dato real.")

    result_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✅ Listo! Dataset guardado en all_match_features_v4.csv")
    print(f"   Partidos totales: {len(result_df)}")
    print(f"   Columnas nuevas:  h_match_xg, a_match_xg, xg_diff, h_l5_xg, a_l5_xg")


if __name__ == "__main__":
    main()
