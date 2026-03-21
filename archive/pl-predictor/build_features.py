import pandas as pd
import numpy as np
import os

# Define paths
BASE_DIR = r"c:\Users\PC\DataScience\archive\pl-predictor"
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
OUTPUT_PATH = os.path.join(HISTORICAL_DIR, "all_match_features.csv")

def build_advanced_features():
    print("Loading datasets across all seasons...")
    all_matches = []
    all_events = []
    
    for season_folder in os.listdir(HISTORICAL_DIR):
        season_path = os.path.join(HISTORICAL_DIR, season_folder)
        if os.path.isdir(season_path):
            matches_file = os.path.join(season_path, "matches.csv")
            events_file = os.path.join(season_path, "match_events.csv")
            if os.path.exists(matches_file):
                all_matches.append(pd.read_csv(matches_file))
            if os.path.exists(events_file):
                all_events.append(pd.read_csv(events_file))
                
    if not all_matches:
        print("No match data found!")
        return

    matches_df = pd.concat(all_matches, ignore_index=True)
    events_df = pd.concat(all_events, ignore_index=True)
    
    matches_df['date'] = pd.to_datetime(matches_df['date'])
    matches_df = matches_df.sort_values(by=['date', 'time']).reset_index(drop=True)
    
    print("1. Extracting Match Goals and Results...")
    matches_df[['home_goals', 'away_goals']] = matches_df['score'].str.split('–', expand=True).astype(float)
    matches_df['total_goals'] = matches_df['home_goals'] + matches_df['away_goals']
    matches_df['btts'] = ((matches_df['home_goals'] > 0) & (matches_df['away_goals'] > 0)).astype(int)
    
    # 1X2 result: 2 = Home Win, 1 = Draw, 0 = Away Win
    conditions = [
        matches_df['home_goals'] > matches_df['away_goals'],
        matches_df['home_goals'] == matches_df['away_goals'],
        matches_df['home_goals'] < matches_df['away_goals']
    ]
    matches_df['result_1x2'] = np.select(conditions, [2, 1, 0], default=np.nan)
    
    print("2. Extracting Card Events...")
    cards_df = events_df[events_df['event_type'].isin(['yellow_card', 'red_card', 'second_yellow_card'])]
    card_counts = cards_df.groupby('game').size().reset_index(name='total_cards')
    matches_df = pd.merge(matches_df, card_counts, on='game', how='left')
    matches_df['total_cards'] = matches_df['total_cards'].fillna(0)
    
    print("3. Referee Historical Strictness...")
    matches_df['referee_avg_cards_history'] = matches_df.groupby('referee')['total_cards'].apply(
        lambda x: x.shift(1).expanding().mean()
    ).reset_index(level=0, drop=True)
    matches_df['referee_avg_cards_history'] = matches_df['referee_avg_cards_history'].fillna(matches_df['total_cards'].mean())
    
    print("4. Team Form (Last 5 Matches) & Rest Days...")
    home_perf = matches_df[['game', 'date', 'home_team', 'home_goals', 'away_goals', 'result_1x2']].copy()
    home_perf.columns = ['game', 'date', 'team', 'gf', 'ga', 'match_result']
    home_perf['points'] = np.select([home_perf['match_result'] == 2, home_perf['match_result'] == 1], [3, 1], default=0)
    
    away_perf = matches_df[['game', 'date', 'away_team', 'away_goals', 'home_goals', 'result_1x2']].copy()
    away_perf.columns = ['game', 'date', 'team', 'gf', 'ga', 'match_result']
    away_perf['points'] = np.select([away_perf['match_result'] == 0, away_perf['match_result'] == 1], [3, 1], default=0)
    
    team_perf = pd.concat([home_perf, away_perf], ignore_index=True).sort_values(by='date')
    
    # Group by team to calculate moving averages
    team_groups = team_perf.groupby('team')
    
    # Rest Days
    team_perf['rest_days'] = team_groups['date'].diff().dt.days
    team_perf['rest_days'] = team_perf['rest_days'].fillna(7) # Default 7 days of rest
    
    # Rolling last 5 matches
    team_perf['last5_pts'] = team_groups['points'].apply(lambda x: x.shift(1).rolling(5, min_periods=1).sum()).reset_index(level=0, drop=True)
    team_perf['last5_gf'] = team_groups['gf'].apply(lambda x: x.shift(1).rolling(5, min_periods=1).mean()).reset_index(level=0, drop=True)
    team_perf['last5_ga'] = team_groups['ga'].apply(lambda x: x.shift(1).rolling(5, min_periods=1).mean()).reset_index(level=0, drop=True)
    
    # Global historical avg (like before, but let's keep it simple)
    team_perf['hist_gf'] = team_groups['gf'].apply(lambda x: x.shift(1).expanding().mean()).reset_index(level=0, drop=True)
    
    team_stats_home = team_perf[['game', 'team', 'rest_days', 'last5_pts', 'last5_gf', 'last5_ga', 'hist_gf']].rename(
        columns={'team': 'home_team', 'rest_days':'home_rest', 'last5_pts':'home_last5_pts', 'last5_gf':'home_last5_gf', 'last5_ga':'home_last5_ga', 'hist_gf':'home_hist_gf'}
    )
    team_stats_away = team_perf[['game', 'team', 'rest_days', 'last5_pts', 'last5_gf', 'last5_ga', 'hist_gf']].rename(
        columns={'team': 'away_team', 'rest_days':'away_rest', 'last5_pts':'away_last5_pts', 'last5_gf':'away_last5_gf', 'last5_ga':'away_last5_ga', 'hist_gf':'away_hist_gf'}
    )
    
    matches_df = pd.merge(matches_df, team_stats_home, on=['game', 'home_team'], how='left')
    matches_df = pd.merge(matches_df, team_stats_away, on=['game', 'away_team'], how='left')
    
    print("5. Head-to-Head (H2H) Features...")
    matches_df['h2h_key'] = matches_df.apply(lambda x: "_".join(sorted([x['home_team'], x['away_team']])), axis=1)
    matches_df['h2h_total_goals'] = matches_df.groupby('h2h_key')['total_goals'].transform(lambda x: x.shift(1).expanding().mean())
    matches_df = matches_df.sort_values(by='date').reset_index(drop=True)
    matches_df['h2h_total_goals'] = matches_df['h2h_total_goals'].fillna(matches_df['total_goals'].mean())
    
    # Final cleanup
    final_features = matches_df[[
        'game', 'season', 'date', 'home_team', 'away_team', 'referee',
        'home_rest', 'home_last5_pts', 'home_last5_gf', 'home_last5_ga', 'home_hist_gf',
        'away_rest', 'away_last5_pts', 'away_last5_gf', 'away_last5_ga', 'away_hist_gf',
        'referee_avg_cards_history', 'h2h_total_goals',
        'home_goals', 'away_goals', 'total_goals', 'btts', 'total_cards', 'result_1x2'
    ]].dropna()
    
    print(f"Saving {len(final_features)} processed matches to: {OUTPUT_PATH}")
    final_features.to_csv(OUTPUT_PATH, index=False)

if __name__ == "__main__":
    build_advanced_features()
