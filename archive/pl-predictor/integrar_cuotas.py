import pandas as pd
import os
import urllib.request
from datetime import datetime

print("Descargando cuotas históricas desde Football-Data.co.uk (Top #1 IA)...")

# Años a recolectar desde la 17/18 hasta la 25/26
seasons = ['1718', '1819', '1920', '2021', '2122', '2223', '2324', '2425', '2526']
all_odds = []

for s in seasons:
    url = f'https://www.football-data.co.uk/mmz4281/{s}/E0.csv'
    try:
        df_season = pd.read_csv(url, usecols=['Date', 'HomeTeam', 'AwayTeam', 'B365H', 'B365D', 'B365A'], encoding='latin-1')
        all_odds.append(df_season)
        print(f"  ✓ Temporada {s} descargada.")
    except Exception as e:
        print(f"  ? Temporada {s} aún no disponible o con error.")

odds_df = pd.concat(all_odds, ignore_index=True)

# Mapeo de nombres para alinear Football-Data con tu Dataset de FBref
name_mapper = {
    'Man City': 'Manchester City',
    'Man United': 'Manchester Utd',
    'Newcastle': 'Newcastle United',
    "Nott'm Forest": 'Nottingham Forest',
    'Sheffield Weds': 'Sheffield United', 
    'Tottenham': 'Tottenham Hotspur',
    'West Ham': 'West Ham United',
    'Luton': 'Luton Town',
    'Leicester': 'Leicester City',
    'Norwich': 'Norwich City',
    'Cardiff': 'Cardiff City',
    'Stoke': 'Stoke City',
    'Swansea': 'Swansea City',
    'Ipswich': 'Ipswich Town',
    'Huddersfield': 'Huddersfield Town',
}
odds_df['HomeTeam'] = odds_df['HomeTeam'].replace(name_mapper)
odds_df['AwayTeam'] = odds_df['AwayTeam'].replace(name_mapper)

# Convertir la fecha de DD/MM/YYYY a YYYY-MM-DD
def parse_date(d):
    parts = d.split('/')
    if len(parts[2]) == 2: # Ej: 11/08/17 -> 2017
        parts[2] = '20' + parts[2]
    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

odds_df['Date'] = odds_df['Date'].astype(str).str.strip()
odds_df['date'] = odds_df['Date'].apply(parse_date)
odds_df['date'] = pd.to_datetime(odds_df['date'])

# Cargar tu dataset procesado
features_path = 'data/historical/all_match_features_v2.csv'
if not os.path.exists(features_path):
    print("Error: all_match_features_v2.csv no existe, corre build_deep_features.py primero.")
    exit(1)

my_df = pd.read_csv(features_path)
my_df['date'] = pd.to_datetime(my_df['date'])

# Hacemos un cruce (merge) por fecha y equipo local
print("Fusionando las cuotas de Bet365 a nuestro Machine Learning...")
merged_df = pd.merge(my_df, odds_df[['date', 'HomeTeam', 'B365H', 'B365D', 'B365A']], 
                     left_on=['date', 'home_team'], 
                     right_on=['date', 'HomeTeam'], 
                     how='left')

# Llenar huecos nulos con cuotas promedio o neutrales si alguna falló el cruce
merged_df['B365H'] = merged_df['B365H'].fillna(2.5)
merged_df['B365D'] = merged_df['B365D'].fillna(3.2)
merged_df['B365A'] = merged_df['B365A'].fillna(2.5)

merged_df.drop(columns=['HomeTeam'], inplace=True, errors='ignore')

merged_df.to_csv('data/historical/all_match_features_v3.csv', index=False)
print("¡Fusión Terminada! Features del monstruo guardados en all_match_features_v3.csv")
