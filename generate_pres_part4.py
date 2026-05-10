import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pres_dir = r'c:\Users\sergi\Desktop\datascience\Carpeta_Presentacion'
os.makedirs(pres_dir, exist_ok=True)

# 1. ANTES (Raw Data)
raw_path = r'c:\Users\sergi\Desktop\datascience\archive\pl-predictor\data\historical\all_match_features_v4_xg.csv'
df_raw = pd.read_csv(raw_path)

# Drop non-numeric and targets for the "Before" matrix
drop_cols = ['date', 'home_team', 'away_team', 'referee', 'venue', 'match_report', 'notes', 'league', 'game_id', 'result_1x2']
cols_before = [c for c in df_raw.columns if c not in drop_cols and pd.api.types.is_numeric_dtype(df_raw[c])]
corr_before = df_raw[cols_before].corr().values

# 2. DESPUES (Sanitized Data - Only Model Features)
sanitized_path = r'c:\Users\sergi\Desktop\datascience\archive\pl-predictor\data\historical\historical_sanitized_v8.csv'
df_sanitized = pd.read_csv(sanitized_path)

FEATURES = [
    'home_elo', 'away_elo', 'home_rest', 'away_rest',
    'h_l5_pts', 'h_l5_sh', 'h_l5_sot', 'h_l5_sot_c', 'h_l5_gf', 'h_l5_ga', 'h_l5_fls', 'h_l5_conv', 'h_l5_xg', 'h_l5_xga',
    'a_l5_pts', 'a_l5_sh', 'a_l5_sot', 'a_l5_sot_c', 'a_l5_gf', 'a_l5_ga', 'a_l5_fls', 'a_l5_conv', 'a_l5_xg', 'a_l5_xga',
    'referee_avg_cards_history', 'is_derby', 'relegation_pressure'
]

# Ensure we only use features present in the dataset (handling minor naming diffs if any)
cols_after = [f for f in FEATURES if f in df_sanitized.columns]
corr_after = df_sanitized[cols_after].corr().values

# 3. PLOTTING
plt.style.use('ggplot')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

# Left Plot (Before)
cax1 = ax1.matshow(corr_before, cmap='coolwarm', vmin=-1, vmax=1)
fig.colorbar(cax1, ax=ax1, fraction=0.046, pad=0.04)
ax1.set_title(f'ANTES: Todas las Variables Crudas ({len(cols_before)} variables)\nBloques rojos oscuros indican fuerte Multicolinealidad', pad=20, fontsize=14)
ax1.set_xticks(np.arange(len(cols_before)))
ax1.set_yticks(np.arange(len(cols_before)))
ax1.set_xticklabels(cols_before, rotation=90, ha='center', fontsize=6)
ax1.set_yticklabels(cols_before, fontsize=6)

# Right Plot (After)
cax2 = ax2.matshow(corr_after, cmap='coolwarm', vmin=-1, vmax=1)
fig.colorbar(cax2, ax=ax2, fraction=0.046, pad=0.04)
ax2.set_title(f'DESPUÉS: Selección Estricta para el Modelo ({len(cols_after)} Features)\nMulticolinealidad reducida (menos bloques de correlación extrema)', pad=20, fontsize=14)
ax2.set_xticks(np.arange(len(cols_after)))
ax2.set_yticks(np.arange(len(cols_after)))
ax2.set_xticklabels(cols_after, rotation=90, ha='center', fontsize=8)
ax2.set_yticklabels(cols_after, fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(pres_dir, '10_Matriz_Correlacion_Completa.png'), dpi=300)
plt.close()

print('Grafico 10 generado correctamente.')
