import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

base_path = "archive/pl-scraper/data/processed/2020"

# 1. Cargar Datos
df_matches = pd.read_csv(f"{base_path}/matches.csv")
df_summary = pd.read_csv(f"{base_path}/player_stats_summary.csv")

# Extraer goles y resultado
df_matches[['home_goals', 'away_goals']] = df_matches['score'].str.replace('–', '-').str.split('-', expand=True).astype(float)
df_matches['home_win'] = (df_matches['home_goals'] > df_matches['away_goals']).astype(int)
df_matches['draw'] = (df_matches['home_goals'] == df_matches['away_goals']).astype(int)
df_matches['away_win'] = (df_matches['home_goals'] < df_matches['away_goals']).astype(int)
df_matches['result'] = np.where(df_matches['home_win']==1, 1, np.where(df_matches['draw']==1, 0, 2)) # 1: Home, 0: Draw, 2: Away
df_matches['over_25'] = ((df_matches['home_goals'] + df_matches['away_goals']) > 2.5).astype(int)

# Ordenar por fecha para evitar data leakage
df_matches['date'] = pd.to_datetime(df_matches['date'])
df_matches = df_matches.sort_values('date')

# 2. FEATURE ENGINEERING (Promedios Históricos - Rolling Averages)
# Calcular goles a favor y en contra históricos por equipo
teams = pd.concat([df_matches['home'], df_matches['away']]).unique()
historical_stats = {team: {'gf': [], 'gc': [], 'games': 0} for team in teams}

home_gf_hist = []
home_gc_hist = []
away_gf_hist = []
away_gc_hist = []

for idx, row in df_matches.iterrows():
    home = row['home']
    away = row['away']
    
    # Obtener promedios antes del partido
    if historical_stats[home]['games'] > 0:
        home_gf_hist.append(sum(historical_stats[home]['gf']) / historical_stats[home]['games'])
        home_gc_hist.append(sum(historical_stats[home]['gc']) / historical_stats[home]['games'])
    else:
        home_gf_hist.append(1.0) # Baseline
        home_gc_hist.append(1.0)
        
    if historical_stats[away]['games'] > 0:
        away_gf_hist.append(sum(historical_stats[away]['gf']) / historical_stats[away]['games'])
        away_gc_hist.append(sum(historical_stats[away]['gc']) / historical_stats[away]['games'])
    else:
        away_gf_hist.append(1.0)
        away_gc_hist.append(1.0)
        
    # Actualizar estadisticas post-partido
    historical_stats[home]['gf'].append(row['home_goals'])
    historical_stats[home]['gc'].append(row['away_goals'])
    historical_stats[home]['games'] += 1
    
    historical_stats[away]['gf'].append(row['away_goals'])
    historical_stats[away]['gc'].append(row['home_goals'])
    historical_stats[away]['games'] += 1

df_matches['home_gf_hist'] = home_gf_hist
df_matches['home_gc_hist'] = home_gc_hist
df_matches['away_gf_hist'] = away_gf_hist
df_matches['away_gc_hist'] = away_gc_hist

# Features y Targets
features = ['home_gf_hist', 'home_gc_hist', 'away_gf_hist', 'away_gc_hist']
df_model = df_matches.dropna(subset=features + ['result', 'over_25'])

# Split temporal (entrenamos con la primera parte de la temporada, probamos con la última)
split_idx = int(len(df_model) * 0.75)
train = df_model.iloc[:split_idx]
test = df_model.iloc[split_idx:]

X_train, y_train_1x2, y_train_ou = train[features], train['result'], train['over_25']
X_test, y_test_1x2, y_test_ou = test[features], test['result'], test['over_25']

# 3. ENTRENAMIENTO Y EVALUACIÓN
models = {
    "Regresión Logística": LogisticRegression(max_iter=1000),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
}

print("="*50)
print("🚀 EVALUACIÓN DE MERCADOS CON DATA SIN LEAKAGE")
print("="*50)

for name, model in models.items():
    print(f"\n--- Modelo: {name} ---")
    
    # Mercado 1X2 (Gana Local, Empate, Gana Visita)
    model.fit(X_train, y_train_1x2)
    preds_1x2 = model.predict(X_test)
    acc_1x2 = accuracy_score(y_test_1x2, preds_1x2)
    print(f"✅ Mercado 1X2 (Ganador): {acc_1x2*100:.2f}% de precisión")
    
    # Mercado Over/Under 2.5
    model.fit(X_train, y_train_ou)
    preds_ou = model.predict(X_test)
    acc_ou = accuracy_score(y_test_ou, preds_ou)
    print(f"✅ Mercado Over/Under 2.5: {acc_ou*100:.2f}% de precisión")

print("\n" + "="*50)
print("📊 BASELINES DEL TEST SET")
print(f"Si predices siempre Local Gana: {(y_test_1x2 == 1).mean()*100:.2f}%")
print(f"Si predices siempre Under 2.5: {(y_test_ou == 0).mean()*100:.2f}%")
print("="*50)
