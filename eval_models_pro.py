import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("="*60)
print("🚀 INICIANDO PIPELINE DE ML - NIVEL PRO (SIN DATA LEAKAGE) 🚀")
print("="*60)

base_path = "archive/pl-scraper/data/processed/2020"

# =========================================================
# 1. CARGA DE DATOS Y LIMPIEZA
# =========================================================
print("[1/5] Cargando y alineando datos...")
df_matches = pd.read_csv(f"{base_path}/matches.csv")
df_summary = pd.read_csv(f"{base_path}/player_stats_summary.csv")

# Mapeo de nombres (Calidad de Datos)
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

df_matches['result_1x2'] = np.where(df_matches['home_win']==1, 1, np.where(df_matches['draw']==1, 0, 2))
df_matches['over_25'] = ((df_matches['home_goals'] + df_matches['away_goals']) > 2.5).astype(int)

df_matches['date'] = pd.to_datetime(df_matches['date'])
df_matches = df_matches.sort_values('date').reset_index(drop=True)

# =========================================================
# 2. FEATURE ENGINEERING (Team Level Stats)
# =========================================================
print("[2/5] Calculando estadísticas de partido por equipo...")
team_match_stats = df_summary.groupby(['game_id', 'team'])[['Performance_Sh', 'Performance_SoT', 'Performance_Fls', 'Performance_CrdY']].sum().reset_index()

home_df = df_matches[['game_id', 'date', 'home_team', 'home_goals', 'away_goals']].rename(
    columns={'home_team': 'team', 'home_goals': 'goals_scored', 'away_goals': 'goals_conceded'}
)
home_df['points'] = np.where(df_matches['home_win']==1, 3, np.where(df_matches['draw']==1, 1, 0))
home_df['is_home'] = 1

away_df = df_matches[['game_id', 'date', 'away_team', 'away_goals', 'home_goals']].rename(
    columns={'away_team': 'team', 'away_goals': 'goals_scored', 'home_goals': 'goals_conceded'}
)
away_df['points'] = np.where(df_matches['away_win']==1, 3, np.where(df_matches['draw']==1, 1, 0))
away_df['is_home'] = 0

team_games = pd.concat([home_df, away_df]).sort_values(['team', 'date']).reset_index(drop=True)
team_games = pd.merge(team_games, team_match_stats, on=['game_id', 'team'], how='left')

# =========================================================
# 3. ROLLING AVERAGES (Evitando Data Leakage)
# =========================================================
print("[3/5] Creando variables rezagadas (Rolling Averages)...")
window = 5
features_to_roll = ['goals_scored', 'goals_conceded', 'points', 'Performance_Sh', 'Performance_SoT', 'Performance_Fls', 'Performance_CrdY']

for feat in features_to_roll:
    # shift(1) es la CLAVE
    team_games[f'{feat}_roll5'] = team_games.groupby('team')[feat].transform(lambda x: x.rolling(window, min_periods=1).mean().shift(1))

# Solo nos quedamos con las variables calculadas PREVIAS al partido (roll5) y las llaves
cols_to_keep = ['game_id', 'date', 'team', 'is_home'] + [f'{feat}_roll5' for feat in features_to_roll]
team_games_clean = team_games[cols_to_keep]

home_features = team_games_clean[team_games_clean['is_home'] == 1].rename(columns=lambda x: f'home_{x}' if x not in ['game_id', 'date'] else x)
away_features = team_games_clean[team_games_clean['is_home'] == 0].rename(columns=lambda x: f'away_{x}' if x not in ['game_id', 'date'] else x)

df_model = pd.merge(df_matches[['game_id', 'date', 'home_team', 'away_team', 'result_1x2', 'over_25']], 
                    home_features.drop(columns=['home_team', 'home_is_home']), on=['game_id', 'date'])
df_model = pd.merge(df_model, away_features.drop(columns=['away_team', 'away_is_home']), on=['game_id', 'date'])

# Ahora sí, podemos dropear los nulos reales (las jornadas 1)
df_model = df_model.dropna().reset_index(drop=True)

# =========================================================
# 4. PREPARACIÓN DE MODELOS
# =========================================================
print(f"[4/5] Entrenando modelos con {len(df_model)} partidos viables...")

feature_cols = [col for col in df_model.columns if 'roll5' in col]

split_idx = int(len(df_model) * 0.75)
train = df_model.iloc[:split_idx]
test = df_model.iloc[split_idx:]

X_train, y_train_1x2, y_train_ou = train[feature_cols], train['result_1x2'], train['over_25']
X_test, y_test_1x2, y_test_ou = test[feature_cols], test['result_1x2'], test['over_25']

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

models = {
    "Regresión Logística": LogisticRegression(C=1.0, max_iter=1000),
    "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_leaf=5, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42)
}

# =========================================================
# 5. EVALUACIÓN DE RESULTADOS REALISTAS
# =========================================================
print("\n" + "="*60)
print("📊 RESULTADOS FINALES (DATOS HONESTOS) 📊")
print("="*60)

baseline_home = (y_test_1x2 == 1).mean()
baseline_under = (y_test_ou == 0).mean()
print(f"🔸 BASELINE 1X2 (Predecir siempre Local Gana): {baseline_home*100:.2f}%")
print(f"🔸 BASELINE OVER/UNDER (Predecir siempre Under 2.5): {baseline_under*100:.2f}%")
print("-" * 60)

best_acc_1x2 = 0
best_model_1x2 = ""
best_acc_ou = 0
best_model_ou = ""

for name, model in models.items():
    xtr = X_train_scaled if name == "Regresión Logística" else X_train
    xte = X_test_scaled if name == "Regresión Logística" else X_test
    
    # Modelo 1X2
    model.fit(xtr, y_train_1x2)
    acc_1x2 = accuracy_score(y_test_1x2, model.predict(xte))
    if acc_1x2 > best_acc_1x2:
        best_acc_1x2 = acc_1x2
        best_model_1x2 = name
        
    # Modelo O/U
    model.fit(xtr, y_train_ou)
    acc_ou = accuracy_score(y_test_ou, model.predict(xte))
    if acc_ou > best_acc_ou:
        best_acc_ou = acc_ou
        best_model_ou = name
        
    print(f"✅ {name.ljust(20)} | 1X2: {acc_1x2*100:.2f}% | O/U 2.5: {acc_ou*100:.2f}%")

print("-" * 60)
print(f"🏆 MEJOR MODELO 1X2: {best_model_1x2} ({best_acc_1x2*100:.2f}%)")
print(f"🏆 MEJOR MODELO O/U: {best_model_ou} ({best_acc_ou*100:.2f}%)")
print("="*60)

best_clf = models["Gradient Boosting"]
best_clf.fit(X_train, y_train_1x2)
importances = best_clf.feature_importances_
indices = np.argsort(importances)[::-1]
print("\n🔍 TOP 5 VARIABLES MÁS IMPORTANTES (Ganador 1X2):")
for i in range(5):
    print(f"  {i+1}. {feature_cols[indices[i]]}: {importances[indices[i]]:.4f}")
