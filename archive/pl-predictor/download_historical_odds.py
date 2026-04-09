import os
import pandas as pd
import requests
import io
from datetime import datetime

# We will merge into the unified features dataset
FEATURES_FILE = "data/historical/all_match_features_v2.csv"
OUTPUT_FILE = "data/historical/all_match_features_v3_odds.csv"

# Seasons to fetch from football-data.co.uk
SEASONS_MAP = {
    '2017/18': '1718',
    '2018/19': '1819',
    '2019/20': '1920',
    '2020/21': '2021',
    '2021/22': '2122',
    '2022/23': '2223',
    '2023/24': '2324',
    '2024/25': '2425',
    '2025/26': '2526'
}

TEAM_NAME_MAP = {
    "Man United": "Manchester Utd",
    "Man City": "Manchester City",
    "Newcastle": "Newcastle United",
    "Tottenham": "Tottenham Hotspur",
    "Wolves": "Wolves",
    "Nott'm Forest": "Nottingham Forest",
    "Nott'ham Forest": "Nottingham Forest",
    "Forest": "Nottingham Forest",
    "West Ham": "West Ham United",
    "Leeds": "Leeds United",
    "Sheffield United": "Sheffield Utd",
    "Leicester": "Leicester City",
    "Huddersfield": "Huddersfield Town",
    "Swansea": "Swansea City",
    "Stoke": "Stoke City",
    "Cardiff": "Cardiff City",
    "Norwich": "Norwich City",
    "Luton": "Luton Town",
    "Ipswich": "Ipswich Town"
}

def clean_team_name(name):
    # Strip spaces and apply the map
    name = str(name).strip()
    return TEAM_NAME_MAP.get(name, name)

def download_odds():
    print("Fetching historical odds from football-data.co.uk...")
    all_odds = []
    
    for season_name, season_code in SEASONS_MAP.items():
        url = f"https://www.football-data.co.uk/mmz4281/{season_code}/E0.csv"
        try:
            print(f"  -> Fetching {season_name} ({url})...")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Read CSV content from response
            df_odds = pd.read_csv(io.StringIO(response.text))
            
            # Football-data dates can be DD/MM/YY or DD/MM/YYYY
            # We enforce standard format
            df_odds['Date_Parsed'] = pd.to_datetime(df_odds['Date'], format="%d/%m/%Y", errors='coerce')
            df_odds['Date_Parsed'] = df_odds['Date_Parsed'].fillna(pd.to_datetime(df_odds['Date'], format="%d/%m/%y", errors='coerce'))
            
            # Select important columns (B365 and Pinnacle odds if available)
            # PS = Pinnacle (PSH, PSD, PSA). B365 = Bet365
            keep_cols = ['Date_Parsed', 'HomeTeam', 'AwayTeam']
            odds_cols = ['B365H', 'B365D', 'B365A', 'PSH', 'PSD', 'PSA']
            
            # Add existing odds columns
            avail_cols = [c for c in keep_cols + odds_cols if c in df_odds.columns]
            df_odds = df_odds[avail_cols].copy()
            
            # Normalize Team Names
            df_odds['HomeTeam'] = df_odds['HomeTeam'].apply(clean_team_name)
            df_odds['AwayTeam'] = df_odds['AwayTeam'].apply(clean_team_name)
            
            df_odds.rename(columns={'HomeTeam': 'home_team', 'AwayTeam': 'away_team', 'Date_Parsed': 'date'}, inplace=True)
            
            # We just need one row per match
            df_odds = df_odds.drop_duplicates(subset=['date', 'home_team', 'away_team'])
            
            all_odds.append(df_odds)
            
        except Exception as e:
            print(f"  ❌ Error fetching {season_name}: {e}")
            
    if not all_odds:
        print("No odds were downloaded.")
        return
        
    combined_odds = pd.concat(all_odds, ignore_index=True)
    print(f"\n✅ Total odds downloaded: {len(combined_odds)} matches.")
    
    # Now merge into our unified dataset
    print(f"\nMerging odds into {FEATURES_FILE}...")
    if not os.path.exists(FEATURES_FILE):
        print(f"FATAL: Database {FEATURES_FILE} not found!")
        return
        
    unified_df = pd.read_csv(FEATURES_FILE)
    unified_df['date'] = pd.to_datetime(unified_df['date'], errors='coerce')
    
    # We will merge using date and home_team. We do a left join.
    # Due to FBref and football-data timezone/day differences sometimes, it's safer to merge on home_team & away_team 
    # and require Date difference < 2 days. But exact date + teams usually works if mapped well.
    merged = pd.merge(unified_df, combined_odds, on=['date', 'home_team', 'away_team'], how='left')
    
    # Let's count how many matches got mapped successfully
    matched_count = merged['B365H'].notna().sum()
    print(f"✅ Merged! Real Odds found for {matched_count} out of {len(merged)} matches.")
    
    # Output to V3
    merged.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Saved as {OUTPUT_FILE}")

if __name__ == '__main__':
    download_odds()
