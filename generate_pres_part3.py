import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pres_dir = r'c:\Users\sergi\Desktop\datascience\Carpeta_Presentacion'
os.makedirs(pres_dir, exist_ok=True)

# Load Data
raw_path = r'c:\Users\sergi\Desktop\datascience\archive\pl-predictor\data\historical\historical_sanitized_v8.csv'
df = pd.read_csv(raw_path)

plt.style.use('ggplot')

# ==========================================
# 9. CATEGORICAS: ONE-HOT VS ELO RATING
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# --- LEFT: Mock Sparse Matrix (One-Hot Encoding Problem) ---
# Create a dummy sparse matrix simulating 20 teams
n_teams = 20
sparse_matrix = np.zeros((n_teams, n_teams))
np.fill_diagonal(sparse_matrix, 1)

# Heatmap to show sparsity (mostly 0s)
cax1 = ax1.matshow(sparse_matrix, cmap='Blues')
ax1.set_title('EL PROBLEMA: One-Hot Encoding\n(Genera matrices dispersas llenas de ceros)', pad=20)
ax1.set_xlabel('20 Nuevas Columnas (Una por Equipo)')
ax1.set_ylabel('Partidos')
ax1.set_xticks([])
ax1.set_yticks([])

# Add some text to emphasize
ax1.text(n_teams/2, n_teams/2, "Alta Cardinalidad\nCeros Inútiles", 
         ha='center', va='center', color='red', fontsize=16, fontweight='bold', alpha=0.7, rotation=45)

# --- RIGHT: Actual Elo Rating Distribution (Our Solution) ---
elo_data = df['home_elo'].dropna()

ax2.hist(elo_data, bins=30, color='#9b59b6', alpha=0.8, edgecolor='white')
ax2.set_title('LA SOLUCIÓN: Elo Rating\n(Convierte el "Nombre" en una Métrica Matemática Continua)')
ax2.set_xlabel('Puntaje de Fuerza (Elo Rating)')
ax2.set_ylabel('Frecuencia de Partidos')

# Add vertical lines to show the tiers
mean_elo = elo_data.mean()
ax2.axvline(mean_elo, color='black', linestyle='--', label='Promedio')
ax2.axvline(1850, color='gold', linestyle='-', linewidth=2, label='Élite (Ej. Man City)')
ax2.axvline(1550, color='brown', linestyle='-', linewidth=2, label='Descenso')
ax2.legend()

plt.tight_layout()
plt.savefig(os.path.join(pres_dir, '9_Categoricas_Elo_vs_OneHot.png'), dpi=200)
plt.close()

print('Grafico 9 generado correctamente.')
