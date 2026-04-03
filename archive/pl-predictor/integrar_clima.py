"""
integrar_clima.py
-----------------
Descarga datos climáticos históricos del día de cada partido (sin API key)
usando la API pública gratuita de Open-Meteo Historical Weather Archive.

Cubre las coordenadas GPS de los estadios de los 20 equipos de la Premier League.

Variables generadas:
  - precipitation_mm : Lluvia en mm el día del partido (0 = seco, >5 = lluvia real)
  - temp_max_c       : Temperatura máxima del día en °C
  - temp_min_c       : Temperatura mínima del día en °C
  - is_raining       : 1 si cayeron >1mm (lluvia), 0 si estuvo seco
  - is_cold          : 1 si temperatura máxima < 8°C (invierno clásico PL)

Fusiona las columnas a all_match_features_v4.csv
y guarda el resultado en all_match_features_v5.csv listo para re-entrenar.
"""

import pandas as pd
import requests
import time
import os

BASE_DIR       = os.path.abspath(os.path.dirname(__file__))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
INPUT_PATH     = os.path.join(HISTORICAL_DIR, "all_match_features_v4.csv")
OUTPUT_PATH    = os.path.join(HISTORICAL_DIR, "all_match_features_v5.csv")

# ── Coordenadas GPS de estadios Premier League ──────────────────────────────
STADIUM_COORDS = {
    "Arsenal":           (51.5549,  -0.1084),
    "Aston Villa":       (52.5090,  -1.8847),
    "Bournemouth":       (50.7352,  -1.8383),
    "Brentford":         (51.4882,  -0.2886),
    "Brighton":          (50.8618,  -0.0837),
    "Burnley":           (53.7892,  -2.2302),
    "Cardiff City":      (51.4731,  -3.2028),
    "Chelsea":           (51.4816,  -0.1909),
    "Crystal Palace":    (51.3983,  -0.0855),
    "Everton":           (53.4388,  -2.9661),
    "Fulham":            (51.4749,  -0.2218),
    "Huddersfield Town": (53.6541,  -1.7680),
    "Ipswich Town":      (52.0543,   1.1445),
    "Leeds United":      (53.7775,  -1.5724),
    "Leicester City":    (52.6204,  -1.1422),
    "Liverpool":         (53.4308,  -2.9608),
    "Luton Town":        (51.8837,  -0.4318),
    "Manchester City":   (53.4831,  -2.2004),
    "Manchester Utd":    (53.4631,  -2.2913),
    "Newcastle United":  (54.9756,  -1.6216),
    "Norwich City":      (52.6222,   1.3089),
    "Nottingham Forest": (52.9399,  -1.1328),
    "Sheffield United":  (53.3703,  -1.4701),
    "Southampton":       (50.9058,  -1.3912),
    "Stoke City":        (53.0006,  -2.1736),
    "Swansea City":      (51.6427,  -3.9343),
    "Tottenham Hotspur": (51.6033,  -0.0660),
    "Watford":           (51.6498,  -0.4017),
    "West Brom":         (52.5090,  -1.9641),
    "West Ham United":   (51.5386,  0.0169),
    "Wolves":            (52.5904,  -2.1302),
}

def fetch_weather_for_stadium(lat, lon, start_date, end_date):
    """Llama a Open-Meteo Archive API y retorna un DataFrame con fechas y clima."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":  lat,
        "longitude": lon,
        "start_date": str(start_date),
        "end_date":   str(end_date),
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
        "timezone": "Europe/London"
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()["daily"]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["time"])
        df = df.rename(columns={
            "precipitation_sum": "precipitation_mm",
            "temperature_2m_max": "temp_max_c",
            "temperature_2m_min": "temp_min_c",
        })
        return df[["date", "precipitation_mm", "temp_max_c", "temp_min_c"]]
    except Exception as e:
        print(f"    ⚠  Weather API error: {e}")
        return pd.DataFrame()


def main():
    print("=" * 60)
    print("Integrando Datos Climáticos (Open-Meteo) al modelo")
    print("=" * 60)

    print("\n[1/4] Cargando dataset v4...")
    main_df = pd.read_csv(INPUT_PATH)
    main_df["date"] = pd.to_datetime(main_df["date"])
    print(f"      {len(main_df)} partidos cargados. Fechas: {main_df['date'].min().date()} → {main_df['date'].max().date()}")

    global_start = main_df["date"].min().strftime("%Y-%m-%d")
    global_end   = main_df["date"].max().strftime("%Y-%m-%d")

    print("\n[2/4] Descargando clima por estadio...")
    weather_frames = []
    for team, (lat, lon) in STADIUM_COORDS.items():
        print(f"      → {team} ({lat}, {lon})")
        df_w = fetch_weather_for_stadium(lat, lon, global_start, global_end)
        if not df_w.empty:
            df_w["home_team"] = team
            weather_frames.append(df_w)
        time.sleep(0.3)  # Cortesía con la API pública

    if not weather_frames:
        print("ERROR: No se pudo obtener ningún dato climático.")
        return

    weather_df = pd.concat(weather_frames, ignore_index=True)
    print(f"\n      Total filas de clima: {len(weather_df)}")

    print("\n[3/4] Calculando variables binarias de clima...")
    weather_df["is_raining"] = (weather_df["precipitation_mm"] > 1.0).astype(int)
    weather_df["is_cold"]    = (weather_df["temp_max_c"] < 8.0).astype(int)

    print("\n[4/4] Fusionando con dataset principal (por fecha + equipo local)...")
    result_df = pd.merge(
        main_df,
        weather_df[["date", "home_team", "precipitation_mm", "temp_max_c", "temp_min_c", "is_raining", "is_cold"]],
        on=["date", "home_team"],
        how="left"
    )

    # Imputar con valores típicos de Londres si el merge falla
    result_df["precipitation_mm"] = result_df["precipitation_mm"].fillna(2.0)
    result_df["temp_max_c"]       = result_df["temp_max_c"].fillna(13.0)
    result_df["temp_min_c"]       = result_df["temp_min_c"].fillna(7.0)
    result_df["is_raining"]       = result_df["is_raining"].fillna(0).astype(int)
    result_df["is_cold"]          = result_df["is_cold"].fillna(0).astype(int)

    pct = (result_df["precipitation_mm"] > 0).mean() * 100
    rain_pct = result_df["is_raining"].mean() * 100
    print(f"      Cobertura clima: {pct:.1f}% · Partidos con lluvia real: {rain_pct:.1f}%")

    result_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✅ Dataset guardado → all_match_features_v5.csv")
    print(f"   Partidos: {len(result_df)} | Columnas nuevas: precipitation_mm, temp_max_c, temp_min_c, is_raining, is_cold")


if __name__ == "__main__":
    main()
