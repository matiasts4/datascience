"""
append_2025.py
========================
Appends the scraped 2025/2026 matches to all_match_features_v2.csv by dynamically
computing Elo and L5 form using the historical data state of v2.
"""

import os
import sys
import pandas as pd
import numpy as np
import shutil
from collections import defaultdict, deque

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
V2_PATH        = os.path.join(HISTORICAL_DIR, "all_match_features_v2.csv")
BACKUP_PATH    = os.path.join(HISTORICAL_DIR, "all_match_features_v2_backup.csv")

# Path to scraped 2025 matches
SCRAPER_DIR    = os.path.join(BASE_DIR, "..", "pl-scraper", "data", "processed", "2025")
RAW_2526_PATH  = os.path.join(SCRAPER_DIR, "matches.csv")

# Ensure 2526 matches exists
if not os.path.exists(RAW_2526_PATH):
    print(f"Error: Could not find {RAW_2526_PATH}")
    sys.exit(1)

# Copy to historical/2025 (Optional, for consistency)
dest_2025_dir = os.path.join(HISTORICAL_DIR, "2025")
os.makedirs(dest_2025_dir, exist_ok=True)
shutil.copy2(RAW_2526_PATH, os.path.join(dest_2025_dir, "matches.csv"))

# ──────────────────────────────────────────────────────────────────────────────
# 1. Load v2 base (already contains up to 2024-25)
# ──────────────────────────────────────────────────────────────────────────────
print("Loading v2 base dataset …")
v2 = pd.read_csv(V2_PATH, parse_dates=["date"])
v2 = v2.sort_values("date").reset_index(drop=True)
print(f"  v2 shape: {v2.shape}, seasons: {sorted(v2['season'].unique())}")

# Optional: backup v2
if not os.path.exists(BACKUP_PATH):
    shutil.copy2(V2_PATH, BACKUP_PATH)
    print("  Backed up v2 to", BACKUP_PATH)

# Check if 2025 handles are already there
if 2526 in v2['season'].unique():
    print("  Season 2526 already present in v2 dataset. Exiting to avoid duplicate appending.")
    sys.exit(0)

# ──────────────────────────────────────────────────────────────────────────────
# 2. Load and prep 2025-26 raw matches
# ──────────────────────────────────────────────────────────────────────────────
print("Loading 2025-26 raw matches …")
raw = pd.read_csv(RAW_2526_PATH, parse_dates=["date"])
raw = raw.sort_values("date").reset_index(drop=True)
print(f"  raw shape: {raw.shape}")

# Parse goals from score (same separator as v2)
raw[["home_goals", "away_goals"]] = (
    raw["score"].str.split("–", expand=True).astype(float)
)
raw["total_goals"] = raw["home_goals"] + raw["away_goals"]
raw["btts"] = ((raw["home_goals"] > 0) & (raw["away_goals"] > 0)).astype(int)

conds = [
    raw["home_goals"] > raw["away_goals"],
    raw["home_goals"] == raw["away_goals"],
    raw["home_goals"] < raw["away_goals"],
]
raw["result_1x2"] = np.select(conds, [2, 1, 0], default=np.nan)

# Keep only completed matches (score parsed OK)
raw = raw[raw["home_goals"].notna()].copy()
print(f"  2025-26 completed rows: {len(raw)}")

if len(raw) == 0:
    print("  No completed games in 2025-26 to append. Exiting.")
    sys.exit(0)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Build ELO map from v2 and continue for 2025-26
# ──────────────────────────────────────────────────────────────────────────────
print("Computing Elo ratings …")

K = 20

def _elo_update(ratings: dict, home: str, away: str, result_1x2: float):
    h_elo = ratings.get(home, 1500.0)
    a_elo = ratings.get(away, 1500.0)
    pre = (h_elo, a_elo)
    h_exp = 1 / (1 + 10 ** ((a_elo - h_elo) / 400))
    a_exp = 1 - h_exp
    if result_1x2 == 2:
        h_act, a_act = 1, 0
    elif result_1x2 == 1:
        h_act, a_act = 0.5, 0.5
    else:
        h_act, a_act = 0, 1
    ratings[home] = h_elo + K * (h_act - h_exp)
    ratings[away]  = a_elo + K * (a_act - a_exp)
    return pre

# Replay v2 to get end-of-season Elo state
elo_state: dict = {}
for _, row in v2.iterrows():
    if pd.notna(row["result_1x2"]):
        _elo_update(elo_state, row["home_team"], row["away_team"], row["result_1x2"])

# Now compute Elo for each 2025-26 match using the inherited state
home_elos, away_elos = [], []
elo_state_copy = dict(elo_state)  # snapshot for feature use
for _, row in raw.iterrows():
    home = row["home_team"]
    away = row["away_team"]
    pre_h, pre_a = _elo_update(elo_state_copy, home, away, row["result_1x2"])
    home_elos.append(round(pre_h, 1))
    away_elos.append(round(pre_a, 1))

raw["home_elo"] = home_elos
raw["away_elo"] = away_elos

# ──────────────────────────────────────────────────────────────────────────────
# 4. Build L5 form features using combined history
# ──────────────────────────────────────────────────────────────────────────────
print("Computing L5 form features …")

home_v2 = v2[["game", "date", "home_team", "h_l5_pts", "h_l5_sh", "h_l5_sot",
               "h_l5_sot_c", "h_l5_gf", "h_l5_ga", "h_l5_fls", "h_l5_conv"]].rename(
    columns={"home_team": "team", "h_l5_pts": "last5_pts", "h_l5_sh": "last5_shots",
             "h_l5_sot": "last5_sot", "h_l5_sot_c": "last5_sot_c",
             "h_l5_gf": "last5_gf", "h_l5_ga": "last5_ga",
             "h_l5_fls": "last5_fouls", "h_l5_conv": "last5_conv"})
home_v2["gf"] = v2["home_goals"]
home_v2["ga"] = v2["away_goals"]
home_v2["result_1x2"] = v2["result_1x2"]
home_v2["pts"] = np.select([v2["result_1x2"] == 2, v2["result_1x2"] == 1], [3, 1], default=0)

away_v2 = v2[["game", "date", "away_team", "a_l5_pts", "a_l5_sh", "a_l5_sot",
               "a_l5_sot_c", "a_l5_gf", "a_l5_ga", "a_l5_fls", "a_l5_conv"]].rename(
    columns={"away_team": "team", "a_l5_pts": "last5_pts", "a_l5_sh": "last5_shots",
             "a_l5_sot": "last5_sot", "a_l5_sot_c": "last5_sot_c",
             "a_l5_gf": "last5_gf", "a_l5_ga": "last5_ga",
             "a_l5_fls": "last5_fouls", "a_l5_conv": "last5_conv"})
away_v2["gf"] = v2["away_goals"]
away_v2["ga"] = v2["home_goals"]
away_v2["result_1x2"] = v2["result_1x2"]
away_v2["pts"] = np.select([v2["result_1x2"] == 0, v2["result_1x2"] == 1], [3, 1], default=0)

last_form_home = home_v2.sort_values("date").groupby("team").last()
last_form_away = away_v2.sort_values("date").groupby("team").last()

form_cols = ["last5_pts", "last5_shots", "last5_sot", "last5_sot_c",
             "last5_gf", "last5_ga", "last5_fouls", "last5_conv", "gf", "ga", "pts"]
combined_last = pd.concat([last_form_home, last_form_away]).groupby(level=0)[form_cols].mean()

def ewm_from_list(vals: list, span=5):
    if not vals: return 0.0
    alpha = 2.0 / (span + 1)
    ewma = vals[0]
    for v in vals[1:]: ewma = alpha * v + (1 - alpha) * ewma
    return ewma

team_history: dict = defaultdict(lambda: {
    "pts": deque(maxlen=5), "sh": deque(maxlen=5), "sot": deque(maxlen=5),
    "sot_c": deque(maxlen=5), "gf": deque(maxlen=5), "ga": deque(maxlen=5),
    "fls": deque(maxlen=5), "conv": deque(maxlen=5)
})

for team in combined_last.index:
    row = combined_last.loc[team]
    team_history[team]["pts"].append(row["pts"] if pd.notna(row["pts"]) else 0)
    team_history[team]["gf"].append(row["gf"] if pd.notna(row["gf"]) else 0)
    team_history[team]["ga"].append(row["ga"] if pd.notna(row["ga"]) else 0)
    team_history[team]["sh"].append(row["last5_shots"] if pd.notna(row["last5_shots"]) else 0)
    team_history[team]["sot"].append(row["last5_sot"] if pd.notna(row["last5_sot"]) else 0)
    team_history[team]["sot_c"].append(row["last5_sot_c"] if pd.notna(row["last5_sot_c"]) else 0)
    team_history[team]["fls"].append(row["last5_fouls"] if pd.notna(row["last5_fouls"]) else 0)
    team_history[team]["conv"].append(row["last5_conv"] if pd.notna(row["last5_conv"]) else 0)

def get_l5(team: str) -> dict:
    h = team_history[team]
    return {
        "pts":   ewm_from_list(list(h["pts"])), "sh":    ewm_from_list(list(h["sh"])),
        "sot":   ewm_from_list(list(h["sot"])), "sot_c": ewm_from_list(list(h["sot_c"])),
        "gf":    ewm_from_list(list(h["gf"])),  "ga":    ewm_from_list(list(h["ga"])),
        "fls":   ewm_from_list(list(h["fls"])), "conv":  ewm_from_list(list(h["conv"])),
    }

def update_history(team: str, gf: float, ga: float, pts: float, avg_shots: float, avg_sot: float):
    h = team_history[team]
    h["pts"].append(pts); h["gf"].append(gf); h["ga"].append(ga); h["sh"].append(avg_shots); h["sot"].append(avg_sot)

rows_2526 = []
for _, row in raw.iterrows():
    home = row["home_team"]
    away = row["away_team"]

    h_form = get_l5(home)
    a_form = get_l5(away)

    new_row = {
        "league":       row.get("league", "ENG-Premier League"),
        "season":       row.get("season", 2526),
        "game":         row.get("game", f"{row['date'].strftime('%Y-%m-%d')} {home}-{away}"),
        "week":         row.get("week", np.nan),
        "day":          row.get("day", np.nan),
        "date":         row["date"],
        "time":         row.get("time", ""),
        "home_team":    home,
        "score":        row["score"],
        "away_team":    away,
        "attendance":   row.get("attendance", np.nan),
        "venue":        row.get("venue", ""),
        "referee":      row.get("referee", ""),
        "match_report": row.get("match_report", ""),
        "notes":        row.get("notes", ""),
        "game_id":      row.get("game_id", ""),
        "home_goals":   row["home_goals"],
        "away_goals":   row["away_goals"],
        "total_goals":  row["total_goals"],
        "btts":         row["btts"],
        "result_1x2":   row["result_1x2"],
        "home_elo":     row["home_elo"],
        "away_elo":     row["away_elo"],
        "home_match_fouls": np.nan, "away_match_fouls": np.nan,
        "home_rest":    7, "away_rest":    7,
        "h_missing_key_player": 0, "a_missing_key_player": 0,
        "h_l5_pts":  h_form["pts"], "h_l5_sh":   h_form["sh"], "h_l5_sot":  h_form["sot"], "h_l5_sot_c":h_form["sot_c"],
        "h_l5_gf":   h_form["gf"],  "h_l5_ga":   h_form["ga"], "h_l5_fls":  h_form["fls"], "h_l5_conv": h_form["conv"],
        "a_l5_pts":  a_form["pts"], "a_l5_sh":   a_form["sh"], "a_l5_sot":  a_form["sot"], "a_l5_sot_c":a_form["sot_c"],
        "a_l5_gf":   a_form["gf"],  "a_l5_ga":   a_form["ga"], "a_l5_fls":  a_form["fls"], "a_l5_conv": a_form["conv"],
        "total_cards": np.nan, "referee_avg_cards_history": np.nan,
        "h2h_total_goals": v2['total_goals'].mean(),
    }
    rows_2526.append(new_row)

    home_pts = 3 if row["result_1x2"] == 2 else (1 if row["result_1x2"] == 1 else 0)
    away_pts = 3 if row["result_1x2"] == 0 else (1 if row["result_1x2"] == 1 else 0)
    update_history(home, row["home_goals"], row["away_goals"], home_pts, h_form["sh"], h_form["sot"])
    update_history(away, row["away_goals"], row["home_goals"], away_pts, a_form["sh"], a_form["sot"])

df_2526 = pd.DataFrame(rows_2526)
print(f"  2025-26 feature rows built: {len(df_2526)}")

# ──────────────────────────────────────────────────────────────────────────────
# 5. Merge and save
# ──────────────────────────────────────────────────────────────────────────────
print("Merging with v2 …")
v2_cols = list(v2.columns)
for col in v2_cols:
    if col not in df_2526.columns:
        df_2526[col] = np.nan
df_2526 = df_2526[v2_cols]

unified = pd.concat([v2, df_2526], ignore_index=True)
unified = unified.sort_values("date").reset_index(drop=True)

global_avg_cards = v2["total_cards"].mean()
unified["total_cards"] = unified["total_cards"].fillna(global_avg_cards)
unified["referee_avg_cards_history"] = (
    unified.groupby("referee")["total_cards"]
    .transform(lambda x: x.shift(1).expanding().mean())
)
unified["referee_avg_cards_history"] = unified["referee_avg_cards_history"].fillna(global_avg_cards)

print(f"Unified dataset shape: {unified.shape}")
print(f"Seasons: {sorted(unified['season'].unique())}")
unified.to_csv(V2_PATH, index=False)
print(f"✅ Saved appended data to -> {V2_PATH}")
