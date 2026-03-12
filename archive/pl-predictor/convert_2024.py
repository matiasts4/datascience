"""
Converts the 2024-25 Kaggle-format CSV to the same schema used by the pl-scraper
(FBref format) and saves it to data/historical/2024/matches.csv
"""
import pandas as pd
import os

SRC = r"c:\Users\PC\DataScience\archive\pl-predictor\data\raw\pl_24-25_matches_clean.csv"
DST_DIR = r"c:\Users\PC\DataScience\archive\pl-predictor\data\historical\2024"
DST = os.path.join(DST_DIR, "matches.csv")

os.makedirs(DST_DIR, exist_ok=True)

df = pd.read_csv(SRC)

# Normalise team names to match the scraper naming convention
NAME_MAP = {
    "Manchester Utd": "Manchester United",
    "Nott'ham Forest": "Nottingham Forest",
    "Newcastle Utd":  "Newcastle United",
    "Sheffield Utd":  "Sheffield United",
    "Wolves":         "Wolverhampton Wanderers",
}
df["home_team"] = df["home_team"].replace(NAME_MAP)
df["away_team"] = df["away_team"].replace(NAME_MAP)

# Build the game column (date + home vs away, like the scraper)
df["game"] = (
    df["date"].astype(str) + " " +
    df["home_team"] + "-" + df["away_team"]
)

# Map columns to the scraper schema
result = pd.DataFrame({
    "league":       "ENG-Premier League",
    "season":       2425,                         # same integer pattern: 2425 = 24/25
    "game":         df["game"],
    "week":         df["gameweek"],
    "day":          df["dayofweek"],
    "date":         df["date"],
    "time":         df["start_time"],
    "home_team":    df["home_team"],
    "score":        df["score"],
    "away_team":    df["away_team"],
    "attendance":   df["attendance"] if "attendance" in df.columns else "",
    "venue":        df["venue"]     if "venue"       in df.columns else "",
    "referee":      df["referee"]   if "referee"     in df.columns else "",
    "match_report": "",
    "notes":        df["notes"]     if "notes"       in df.columns else "",
    "game_id":      df["id"].apply(lambda x: f"kaggle_{x}"),
})

result.to_csv(DST, index=False)
print(f"Saved {len(result)} rows → {DST}")
print(result.head(3).to_string())
