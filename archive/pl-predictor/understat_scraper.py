"""
Understat xG scraper usando la API interna de Understat.
Endpoint descubierto: https://understat.com/getLeagueData/EPL/{year}
Header requerido: x-requested-with: XMLHttpRequest
"""

import json
import requests
import pandas as pd
import os
import time

SEASONS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
SEASON_LABEL = {
    2017: "2017/18", 2018: "2018/19", 2019: "2019/20", 2020: "2020/21",
    2021: "2021/22", 2022: "2022/23", 2023: "2023/24", 2024: "2024/25",
}
OUT_PATH = "data/historical/understat_xg.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "Referer": "https://understat.com/league/EPL/",
}


def fetch_season(year):
    url = f"https://understat.com/getLeagueData/EPL/{year}"
    print(f"  -> GET {url}")
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()

    # La API devuelve {"dates": [...], "teams": {...}, "players": {...}}
    matches_raw = data.get("dates", data.get("datesData", []))
    
    season_label = SEASON_LABEL[year]
    rows = []
    for m in matches_raw:
        if not m.get("isResult"):
            continue
        try:
            rows.append({
                "date": m["datetime"].split(" ")[0],
                "home_team": m["h"]["title"],
                "away_team": m["a"]["title"],
                "home_xg": float(m["xG"]["h"]),
                "away_xg": float(m["xG"]["a"]),
                "season": season_label,
            })
        except (KeyError, TypeError, ValueError):
            pass

    return rows


def main():
    all_rows = []

    for year in SEASONS:
        print(f"\n[{SEASON_LABEL[year]}] Fetching...")
        try:
            rows = fetch_season(year)
            all_rows.extend(rows)
            print(f"  -> OK: {len(rows)} partidos.")
        except Exception as e:
            print(f"  -> ERROR: {e}")
        time.sleep(1)  # Respetar rate-limit

    if not all_rows:
        print("\n❌ No se pudo extraer ningún dato.")
        return

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["season", "date"]).reset_index(drop=True)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"\n✅ Guardado: {OUT_PATH}")
    print(f"   Total filas: {len(df)}\n")
    print(df.groupby("season").size().to_string())
    print("\nPrimeras 5 filas:")
    print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
