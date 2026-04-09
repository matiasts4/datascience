import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("🏆 INICIANDO PIPELINE EXPERTO - OPTIMIZACIÓN EXTREMA 🏆")
print("="*70)

base_path = "archive/pl-scraper/data/processed/2020"

# =========================================================
# 1. CARGA Y PREPARACIÓN BÁSICA
# =========================================================
print("[1/6] Cargando datos y aplicando correcciones...")
df_matches = pd.read_csv(f"{base_path}/matches.csv")
df_summary = pd.read_csv(f"{base_path}/player_stats_summary.csv")

team_mapping = {
    'West Bromwich Albion': 'West Brom',
    'Brighton & Hove Albion': 'Brighton',
    'Manchester United': 'Manchester Utd',
    'Wolverhampton Wanderers': 'Wolves'
}
df_summary['team'] = df_summary['team'].replace(team_mapping)

df_matches[['home_goals', 'away_goals']] = df_matches['score'].str.replace('–', '-').str.split('-', expand=True).astype(float)
df_matches['home_win'] = (df_matches['home_goals'] > df_matches['away_goals']).astype(int)
df_matches['draw'] = (df_matches['home_goals'] == df_matches['away_goals']).astype(int)
df_matches['away_win'] = (df_matches['home_goals'] < df_matches['away_goals']).astype(int)

# Codificación para XGBoost: 0=Local, 1=Empate, 2=Visita
df_matches['result_1x2'] = np.where(df_matches['home_win']==1, 0, np.where(df_matches['draw']==1, 1, 2))
df_matches['date'] = pd.to_datetime(df_matches['date'])
df_matches = df_matches.sort_values('date').reset_index(drop=True)

# =========================================================
# 2. CALCULO DE SISTEMA ELO (Fuerza real del equipo)
# =========================================================
print("[2/6] Calculando Rating ELO Histórico (Fuerza del Calendario)...")
def calculate_elo(df):
    elo_dict = {team: 1500 for team in pd.concat([df['home_team'], df['away_team']]).unique()}
    K = 20 # Factor de actualización
    
    home_elo_pre = []
    away_elo_pre = []
    
    for idx, row in df.iterrows():
        home = row['home_team']
        away = row['away_team']
        
        # Guardar ELO antes del partido (evita Leakage)
        home_elo = elo_dict[home]
        away_elo = elo_dict[away]
        home_elo_pre.append(home_elo)
        away_elo_pre.append(away_elo)
        
        # Calcular probabilidades esperadas
        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        expected_away = 1 - expected_home
        
        # Resultados reales (1 gana, 0.5 empata, 0 pierde)
        if row['home_goals'] > row['away_goals']:
            actual_home, actual_away = 1, 0
        elif row['home_goals'] < row['away_goals']:
            actual_home, actual_away = 0, 1
        else:
            actual_home, actual_away = 0.5, 0.5
            
        # Actualizar ELO para el próximo partido
        elo_dict[home] = home_elo + K * (actual_home - expected_home)
        elo_dict[away] = away_elo + K * (actual_away - expected_away)
        
    df['home_elo_pre'] = home_elo_pre
    df['away_elo_pre'] = away_elo_pre
    df['elo_diff'] = df['home_elo_pre'] - df['away_elo_pre']
    return df

df_matches = calculate_elo(df_matches)

# =========================================================
# 3. ROLLING AVERAGES (Momentum del equipo)
# =========================================================
print("[3/6] Calculando promedios móviles avanzados...")
team_match_stats = df_summary.groupby(['game_id', 'team'])[['Performance_Sh', 'Performance_SoT']].sum().reset_index()

home_df = df_matches[['game_id', 'date', 'home_team', 'home_goals', 'away_goals', 'home_win', 'draw']].rename(
    columns={'home_team': 'team', 'home_goals': 'goals_scored', 'away_goals': 'goals_conceded'}
)
home_df['points'] = np.where(home_df['home_win']==1, 3, np.where(home_df['draw']==1, 1, 0))
home_df['is_home'] = 1

away_df = df_matches[['game_id', 'date', 'away_team', 'away_goals', 'home_goals', 'away_win', 'draw']].rename(
    columns={'away_team': 'team', 'away_goals': 'goals_scored', 'home_goals': 'goals_conceded'}
)
away_df['points'] = np.where(away_df['away_win']==1, 3, np.where(away_df['draw']==1, 1, 0))
away_df['is_home'] = 0

team_games = pd.concat([home_df, away_df]).sort_values(['team', 'date']).reset_index(drop=True)
team_games = pd.merge(team_games, team_match_stats, on=['game_id', 'team'], how='left')

window = 5
features_to_roll = ['goals_scored', 'goals_conceded', 'points', 'Performance_Sh', 'Performance_SoT']

for feat in features_to_roll:
    team_games[f'{feat}_roll5'] = team_games.groupby('team')[feat].transform(lambda x: x.rolling(window, min_periods=1).mean().shift(1))

cols_to_keep = ['game_id', 'date', 'team', 'is_home'] + [f'{feat}_roll5' for feat in features_to_roll]
team_games_clean = team_games[cols_to_keep]

home_features = team_games_clean[team_games_clean['is_home'] == 1].rename(columns=lambda x: f'home_{x}' if x not in ['game_id', 'date'] else x)
away_features = team_games_clean[team_games_clean['is_home'] == 0].rename(columns=lambda x: f'away_{x}' if x not in ['game_id', 'date'] else x)

df_model = pd.merge(df_matches[['game_id', 'date', 'home_team', 'away_team', 'result_1x2', 'elo_diff', 'home_elo_pre', 'away_elo_pre']], 
                    home_features.drop(columns=['home_team', 'home_is_home']), on=['game_id', 'date'])
df_model = pd.merge(df_model, away_features.drop(columns=['away_team', 'away_is_home']), on=['game_id', 'date'])

df_model = df_model.dropna().reset_index(drop=True)

# =========================================================
# 4. PREPARACIÓN DE ENTRENAMIENTO
# =========================================================
print("[4/6] Dividiendo datos (Train/Test Temporal)...")
feature_cols = ['elo_diff', 'home_elo_pre', 'away_elo_pre'] + [col for col in df_model.columns if 'roll5' in col]

split_idx = int(len(df_model) * 0.75)
train = df_model.iloc[:split_idx]
test = df_model.iloc[split_idx:]

X_train, y_train = train[feature_cols], train['result_1x2']
X_test, y_test = test[feature_cols], test['result_1x2']

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LogisticRegression(C=0.5, max_iter=1000, class_weight='balanced')
model.fit(X_train_scaled, y_train)

# =========================================================
# 5. ESTRATEGIA 1: PROBABILITY THRESHOLDING (El secreto profesional)
# =========================================================
print("\n[5/6] 🎯 ESTRATEGIA 1: UMBRAL DE CONFIANZA (Mercado 1X2) 🎯")
print("En vez de apostar en todos los partidos, el modelo solo apuesta cuando está seguro.")

probs = model.predict_proba(X_test_scaled)
confidences = np.max(probs, axis=1)
predictions = model.classes_[np.argmax(probs, axis=1)]

thresholds = [0.0, 0.50, 0.55, 0.60]

for t in thresholds:
    mask = confidences >= t
    if mask.sum() > 0:
        acc = accuracy_score(y_test[mask], predictions[mask])
        if t == 0.0:
            print(f"🔸 Sin filtro (Todos los {mask.sum()} partidos): {acc*100:.2f}% Precisión")
        else:
            print(f"✅ Apostando solo si Confianza > {t*100:.0f}%: {acc*100:.2f}% Precisión (En {mask.sum()} partidos)")

# =========================================================
# 6. ESTRATEGIA 2: CAMBIO DE MERCADO (Draw No Bet)
# =========================================================
print("\n[6/6] 🥊 ESTRATEGIA 2: MERCADO 'DRAW NO BET' (Sin Empate) 🥊")
print("Eliminamos el ruido del empate. Predecimos solo Local vs Visita.")

# Filtramos los empates del test set y train set
train_dnb = train[train['result_1x2'] != 1].copy()
test_dnb = test[test['result_1x2'] != 1].copy()

# Target DNB: 1 (Gana Local), 0 (Gana Visita)
train_dnb['target_dnb'] = np.where(train_dnb['result_1x2'] == 0, 1, 0)
test_dnb['target_dnb'] = np.where(test_dnb['result_1x2'] == 0, 1, 0)

X_train_dnb = scaler.fit_transform(train_dnb[feature_cols])
y_train_dnb = train_dnb['target_dnb']
X_test_dnb = scaler.transform(test_dnb[feature_cols])
y_test_dnb = test_dnb['target_dnb']

# Usamos XGBoost para esto
xgb_dnb = XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42)
xgb_dnb.fit(X_train_dnb, y_train_dnb)

preds_dnb = xgb_dnb.predict(X_test_dnb)
acc_dnb = accuracy_score(y_test_dnb, preds_dnb)

print(f"🚀 Precisión base en Draw No Bet (XGBoost): {acc_dnb*100:.2f}%")

# Le aplicamos Threshold al DNB
probs_dnb = xgb_dnb.predict_proba(X_test_dnb)
conf_dnb = np.max(probs_dnb, axis=1)

mask_dnb = conf_dnb >= 0.65
if mask_dnb.sum() > 0:
    acc_dnb_thresh = accuracy_score(y_test_dnb[mask_dnb], preds_dnb[mask_dnb])
    print(f"🚀 Precisión DNB con Confianza > 65%: {acc_dnb_thresh*100:.2f}% (En {mask_dnb.sum()} partidos)")

print("\n" + "="*70)
print("💡 RESUMEN PARA TU PROFESOR:")
print("1. Implementamos ELO Rating para medir la fuerza real de los equipos.")
print("2. Aplicamos 'Probability Thresholding' para evitar predecir partidos aleatorios.")
print("3. Evaluamos mercados binarios (Draw No Bet) donde el ruido estadístico es menor.")
print("="*70)
