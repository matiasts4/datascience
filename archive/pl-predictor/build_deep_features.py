import pandas as pd
import numpy as np
import os
import glob

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
OUTPUT_PATH = os.path.join(HISTORICAL_DIR, "all_match_features_v2.csv")

def calculate_elo(matches, k=20):
    # Initial Elo
    teams_elo = {}
    elo_history = []
    
    for idx, row in matches.iterrows():
        home = row['home_team']
        away = row['away_team']
        
        home_elo = teams_elo.get(home, 1500)
        away_elo = teams_elo.get(away, 1500)
        
        # Save pre-match Elo for features
        elo_history.append((home_elo, away_elo))
        
        # Expected outcomes
        home_exp = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        away_exp = 1 / (1 + 10 ** ((home_elo - away_elo) / 400))
        
        # Actual outcomes (1=win, 0.5=draw, 0=loss)
        if row['result_1x2'] == 2:
            home_act, away_act = 1, 0
        elif row['result_1x2'] == 1:
            home_act, away_act = 0.5, 0.5
        else:
            home_act, away_act = 0, 1
            
        # Update Elo
        teams_elo[home] = home_elo + k * (home_act - home_exp)
        teams_elo[away] = away_elo + k * (away_act - away_exp)
        
    elo_df = pd.DataFrame(elo_history, columns=['home_elo', 'away_elo'])
    return pd.concat([matches, elo_df], axis=1)

def build_deep_features():
    print("Loading Deep Stats (Player Summaries) and Matches...")
    all_matches = []
    all_pstats = []
    all_events = []
    
    for season_folder in os.listdir(HISTORICAL_DIR):
        season_path = os.path.join(HISTORICAL_DIR, season_folder)
        if os.path.isdir(season_path):
            m_file = os.path.join(season_path, "matches.csv")
            p_file = os.path.join(season_path, "player_stats_summary.csv")
            e_file = os.path.join(season_path, "match_events.csv")
            
            if os.path.exists(m_file):
                all_matches.append(pd.read_csv(m_file))
            if os.path.exists(p_file):
                all_pstats.append(pd.read_csv(p_file))
            if os.path.exists(e_file):
                all_events.append(pd.read_csv(e_file))
                
    matches_df = pd.concat(all_matches, ignore_index=True)
    pstats_df = pd.concat(all_pstats, ignore_index=True)
    events_df = pd.concat(all_events, ignore_index=True)
    
    matches_df['date'] = pd.to_datetime(matches_df['date'], format='mixed', dayfirst=False, errors='coerce')
    matches_df = matches_df.sort_values(by=['date', 'time']).reset_index(drop=True)
    
    print("Extracting Goals and 1X2...")
    matches_df[['home_goals', 'away_goals']] = matches_df['score'].str.split('–', expand=True).astype(float)
    matches_df['total_goals'] = matches_df['home_goals'] + matches_df['away_goals']
    matches_df['btts'] = ((matches_df['home_goals'] > 0) & (matches_df['away_goals'] > 0)).astype(int)
    
    conds = [matches_df['home_goals'] > matches_df['away_goals'], matches_df['home_goals'] == matches_df['away_goals'], matches_df['home_goals'] < matches_df['away_goals']]
    matches_df['result_1x2'] = np.select(conds, [2, 1, 0], default=np.nan)
    
    # Calculate Elo
    print("Calculating Dynamic Elo Ratings...")
    matches_df = calculate_elo(matches_df)
    
    print("Aggregating Player Stats to Team Level (Shots, SoT, Fouls)...")
    
    print("Finding Missing Key Players...")
    # Clean pstats cols
    print("  cleaning pstats...")
    for col in ['Performance_Sh', 'Performance_SoT', 'Performance_Fls', 'Performance_Gls', 'min']:
        pstats_df[col] = pd.to_numeric(pstats_df[col], errors='coerce').fillna(0)
    
    print("  grouping team pstats...")
    team_pstats = pstats_df.groupby(['game', 'team'])[['Performance_Sh', 'Performance_SoT', 'Performance_Fls']].sum().reset_index()
    team_pstats.columns = ['game', 'team', 'shots', 'sot', 'fouls']
    
    print("  evaluating key players...")
    # Evaluate key players
    player_totals = pstats_df.groupby(['team', 'player'])['Performance_Gls'].sum().reset_index()
    print("  sorting players...")
    top_players = player_totals.sort_values(['team', 'Performance_Gls'], ascending=[True, False]).groupby('team').head(2)
    print("  merging key pstats...")
    key_pstats = pstats_df.merge(top_players[['team', 'player']], on=['team', 'player'])
    print("  grouping key played...")
    key_played = key_pstats[key_pstats['min'] > 0].groupby(['game', 'team']).size().reset_index(name='key_players_active')
    
    print("  merging back to team_pstats...")
    team_pstats = pd.merge(team_pstats, key_played, on=['game', 'team'], how='left')
    team_pstats['key_players_active'] = team_pstats['key_players_active'].fillna(0)
    team_pstats['missing_key_player'] = (team_pstats['key_players_active'] < 2).astype(int)
    
    print("Extracting Form and Rolling Advanced Stats...")
    home_perf = matches_df[['game', 'date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'result_1x2', 'away_elo']].copy()
    home_perf.columns = ['game', 'date', 'team', 'opponent', 'gf', 'ga', 'match_result', 'opp_elo']
    home_perf['points'] = np.select([home_perf['match_result'] == 2, home_perf['match_result'] == 1], [3, 1], default=0)
    
    away_perf = matches_df[['game', 'date', 'away_team', 'home_team', 'away_goals', 'home_goals', 'result_1x2', 'home_elo']].copy()
    away_perf.columns = ['game', 'date', 'team', 'opponent', 'gf', 'ga', 'match_result', 'opp_elo']
    away_perf['points'] = np.select([away_perf['match_result'] == 0, away_perf['match_result'] == 1], [3, 1], default=0)
    
    perf = pd.concat([home_perf, away_perf], ignore_index=True)
    perf = pd.merge(perf, team_pstats, on=['game', 'team'], how='left')
    
    # Now get opponent shots and sot to calculate "shots conceded"
    opp_pstats = team_pstats[['game', 'team', 'shots', 'sot', 'fouls']].rename(columns={'team': 'opponent', 'shots': 'shots_conceded', 'sot': 'sot_conceded', 'fouls':'fouls_drawn'})
    perf = pd.merge(perf, opp_pstats, on=['game', 'opponent'], how='left')
    
    perf = perf.sort_values(by='date').reset_index(drop=True)
    groups = perf.groupby('team')
    
    # Rest Days
    perf['rest_days'] = groups['date'].diff().dt.days.fillna(7).clip(upper=14)
    
    # Strength of Schedule (SoS) adjustment factor
    # Average Elo is ~1500. So an opponent with 1650 Elo gives factor 1.1.
    perf['adj_factor'] = np.clip(perf['opp_elo'] / 1500.0, 0.7, 1.3)
    
    # Adjust stats
    perf['adj_pts'] = perf['points'] * perf['adj_factor']
    perf['adj_shots'] = perf['shots'] * perf['adj_factor']
    perf['adj_sot'] = perf['sot'] * perf['adj_factor']
    perf['adj_sot_c'] = perf['sot_conceded'] / perf['adj_factor'] # penalize more if conceding against weak team
    perf['adj_gf'] = perf['gf'] * perf['adj_factor']
    perf['adj_ga'] = perf['ga'] / perf['adj_factor']
    
    # Conversion rate
    perf['conv_rate'] = np.where(perf['adj_shots'] > 0, perf['adj_gf'] / perf['adj_shots'], 0)
    
    # Exponential Weighted Moving Average (EWMA) for last 5 matches
    perf['last5_pts']   = groups['adj_pts'].apply(lambda x: x.shift(1).ewm(span=5, min_periods=1).mean()).reset_index(level=0, drop=True)
    perf['last5_shots'] = groups['adj_shots'].apply(lambda x: x.shift(1).ewm(span=5, min_periods=1).mean()).reset_index(level=0, drop=True)
    perf['last5_sot']   = groups['adj_sot'].apply(lambda x: x.shift(1).ewm(span=5, min_periods=1).mean()).reset_index(level=0, drop=True)
    perf['last5_sot_c'] = groups['adj_sot_c'].apply(lambda x: x.shift(1).ewm(span=5, min_periods=1).mean()).reset_index(level=0, drop=True)
    perf['last5_gf']    = groups['adj_gf'].apply(lambda x: x.shift(1).ewm(span=5, min_periods=1).mean()).reset_index(level=0, drop=True)
    perf['last5_ga']    = groups['adj_ga'].apply(lambda x: x.shift(1).ewm(span=5, min_periods=1).mean()).reset_index(level=0, drop=True)
    perf['last5_fouls'] = groups['fouls'].apply(lambda x: x.shift(1).ewm(span=5, min_periods=1).mean()).reset_index(level=0, drop=True)
    perf['last5_conv']  = groups['conv_rate'].apply(lambda x: x.shift(1).ewm(span=5, min_periods=1).mean()).reset_index(level=0, drop=True)
    
    # Split back to home and away
    home_features = perf[['game', 'team', 'fouls', 'rest_days', 'missing_key_player', 'last5_pts', 'last5_shots', 'last5_sot', 'last5_sot_c', 'last5_gf', 'last5_ga', 'last5_fouls', 'last5_conv']].rename(
        columns={'team':'home_team', 'fouls':'home_match_fouls', 'rest_days':'home_rest', 'missing_key_player':'h_missing_key_player', 'last5_pts':'h_l5_pts', 'last5_shots':'h_l5_sh', 'last5_sot':'h_l5_sot', 'last5_sot_c':'h_l5_sot_c', 'last5_gf':'h_l5_gf', 'last5_ga':'h_l5_ga', 'last5_fouls':'h_l5_fls', 'last5_conv':'h_l5_conv'}
    )
    away_features = perf[['game', 'team', 'fouls', 'rest_days', 'missing_key_player', 'last5_pts', 'last5_shots', 'last5_sot', 'last5_sot_c', 'last5_gf', 'last5_ga', 'last5_fouls', 'last5_conv']].rename(
        columns={'team':'away_team', 'fouls':'away_match_fouls', 'rest_days':'away_rest', 'missing_key_player':'a_missing_key_player', 'last5_pts':'a_l5_pts', 'last5_shots':'a_l5_sh', 'last5_sot':'a_l5_sot', 'last5_sot_c':'a_l5_sot_c', 'last5_gf':'a_l5_gf', 'last5_ga':'a_l5_ga', 'last5_fouls':'a_l5_fls', 'last5_conv':'a_l5_conv'}
    )
    
    matches_df = pd.merge(matches_df, home_features, on=['game', 'home_team'], how='left')
    matches_df = pd.merge(matches_df, away_features, on=['game', 'away_team'], how='left')

    print("Extracting Psychological & Context Flags...")
    # Banderas Psicológicas (Derbis y Presión)
    london_teams = ['Arsenal', 'Chelsea', 'Tottenham Hotspur', 'West Ham United', 'Crystal Palace', 'Fulham', 'Brentford', 'QPR', 'Charlton Athletic']
    manchester_teams = ['Manchester City', 'Manchester Utd']
    merseyside_teams = ['Liverpool', 'Everton']
    birmingham_teams = ['Aston Villa', 'Birmingham City', 'West Brom']

    def is_derby(home, away):
        for group in [london_teams, manchester_teams, merseyside_teams, birmingham_teams]:
            if home in group and away in group:
                return 1
        return 0

    matches_df['is_derby'] = matches_df.apply(lambda row: is_derby(row['home_team'], row['away_team']), axis=1)

    # Relegation pressure (Meses criticos + bajos puntos)
    # Suponiendo que meses 2,3,4,5 son criticos de fin de temporada en Premier y puntos bajos (ej: < 1.0 por partido) significa riesgo.
    matches_df['month'] = matches_df['date'].dt.month
    def calc_relegation_pressure(row):
        is_critical_month = row['month'] in [2, 3, 4, 5]
        # Puntos historicos l5 es un indicador de si estan urgidos
        home_urgency = 1 if is_critical_month and row['h_l5_pts'] < 1.2 else 0
        away_urgency = 1 if is_critical_month and row['a_l5_pts'] < 1.2 else 0
        return max(home_urgency, away_urgency)

    matches_df['relegation_pressure'] = matches_df.apply(calc_relegation_pressure, axis=1)


    print("Extracting Cards Data...")
    cards_df = events_df[events_df['event_type'].isin(['yellow_card', 'red_card', 'second_yellow_card'])]
    card_counts = cards_df.groupby('game').size().reset_index(name='total_cards')
    matches_df = pd.merge(matches_df, card_counts, on='game', how='left')
    matches_df['total_cards'] = matches_df['total_cards'].fillna(0)
    
    # Referee history
    matches_df['referee_avg_cards_history'] = matches_df.groupby('referee')['total_cards'].transform(lambda x: x.shift(1).expanding().mean())
    matches_df['referee_avg_cards_history'] = matches_df['referee_avg_cards_history'].fillna(matches_df['total_cards'].mean())
    
    # Fill remaining NaNs from first matches of teams
    matches_df = matches_df.fillna(0)
    
    # Save features
    final = matches_df
    print(f"Saving {len(final)} highly advanced processed matches to: {OUTPUT_PATH}")
    final.to_csv(OUTPUT_PATH, index=False)

if __name__ == "__main__":
    build_deep_features()
