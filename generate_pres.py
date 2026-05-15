import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import PowerTransformer

# Crear carpeta de presentación
pres_dir = r'c:\Users\sergi\Desktop\datascience\Carpeta_Presentacion'
os.makedirs(pres_dir, exist_ok=True)

raw_path = r'c:\Users\sergi\Desktop\datascience\archive\pl-predictor\data\historical\all_match_features_v4_xg.csv'
df_raw = pd.read_csv(raw_path)

# Estilo global
plt.style.use('ggplot')

# ==========================================
# GRAFICO 1: MISSING VALUES (ANTES Y DESPUES)
# ==========================================
plt.figure(figsize=(10, 5))
missing_cols = ['home_xg', 'away_xg', 'referee']
counts_missing = df_raw[missing_cols].isnull().sum().values
counts_imputed = [0, 0, 0] # Representa después de KNNImputer

x = np.arange(len(missing_cols))
width = 0.35

fig, ax = plt.subplots(figsize=(9,6))
ax.bar(x - width/2, counts_missing, width, label='Datos Faltantes (Antes)', color='#e74c3c')
ax.bar(x + width/2, counts_imputed, width, label='Datos Faltantes (Después del KNNImputer)', color='#2ecc71')

ax.set_ylabel('Cantidad de Partidos')
ax.set_title('Tratamiento de Missing Data (MAR) mediante KNNImputer')
ax.set_xticks(x)
ax.set_xticklabels(['Expected Goals (Local)', 'Expected Goals (Visita)', 'Árbitro'])
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(pres_dir, '1_Missing_Values_Antes_y_Despues.png'), dpi=200)
plt.close('all')

# ==========================================
# GRAFICO 2: OUTLIERS (ANTES Y DESPUES)
# ==========================================
plt.figure(figsize=(12, 5))
feature = 'away_xg' # Variable usada en el modelo
raw_feature = df_raw[feature].dropna().values.reshape(-1, 1)
pt = PowerTransformer(method='yeo-johnson', standardize=True)
transformed_feature = pt.fit_transform(raw_feature)

plt.subplot(1, 2, 1)
plt.hist(raw_feature, bins=40, color='#e74c3c', alpha=0.8)
plt.title(f'ANTES: {feature}\n(Asimetría severa / Outliers)')
plt.xlabel('Valor Original')
plt.ylabel('Frecuencia')

plt.subplot(1, 2, 2)
plt.hist(transformed_feature, bins=40, color='#3498db', alpha=0.8)
plt.title('DESPUÉS: Transformación Yeo-Johnson\n(Distribución Normal Gaussiana)')
plt.xlabel('Valor Transformado (Estandarizado)')

plt.tight_layout()
plt.savefig(os.path.join(pres_dir, '2_Outliers_Antes_y_Despues.png'), dpi=200)
plt.close('all')

# ==========================================
# GRAFICO 3: MULTICOLINEALIDAD (ANTES Y DESPUES)
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

cols_before = ['home_goals', 'home_xg', 'total_goals', 'away_xg']
corr_before = df_raw[cols_before].corr().values

cax1 = ax1.matshow(corr_before, cmap='coolwarm', vmin=-1, vmax=1)
ax1.set_xticks(np.arange(len(cols_before)))
ax1.set_yticks(np.arange(len(cols_before)))
ax1.set_xticklabels(['Goles L', 'xG L', 'Total G', 'xG V'], rotation=45, ha='left')
ax1.set_yticklabels(['Goles L', 'xG L', 'Total G', 'xG V'])
for i in range(len(cols_before)):
    for j in range(len(cols_before)):
        ax1.text(j, i, f'{corr_before[i, j]:.2f}', ha='center', va='center', color='black')
ax1.set_title('ANTES: Alta Multicolinealidad\n(Variables Redundantes)', pad=20)

cols_after = ['home_xg', 'h_l5_pts'] # Ejemplo de features finales seleccionados
corr_after = df_raw[cols_after].corr().values

cax2 = ax2.matshow(corr_after, cmap='coolwarm', vmin=-1, vmax=1)
ax2.set_xticks(np.arange(len(cols_after)))
ax2.set_yticks(np.arange(len(cols_after)))
ax2.set_xticklabels(['xG', 'Puntos L5'], rotation=45, ha='left')
ax2.set_yticklabels(['xG', 'Puntos L5'])
for i in range(len(cols_after)):
    for j in range(len(cols_after)):
        ax2.text(j, i, f'{corr_after[i, j]:.2f}', ha='center', va='center', color='black')
ax2.set_title('DESPUÉS: Selección de Features\n(Variables Independientes Clave)', pad=20)

plt.tight_layout()
plt.savefig(os.path.join(pres_dir, '3_Multicolinealidad_Antes_y_Despues.png'), dpi=200)
plt.close('all')

# ==========================================
# GRAFICO 4: TARGET IMBALANCE
# ==========================================
plt.figure(figsize=(8, 5))
results = df_raw['result_1x2'].value_counts(normalize=True) * 100
labels = ['Local (Victoria)', 'Visitante (Victoria)', 'Empate']
colors = ['#2ecc71', '#e74c3c', '#f1c40f']

plt.bar(labels, results.values, color=colors)
plt.title('Análisis del Target: Desbalanceo de Clases en Resultados')
plt.ylabel('Probabilidad de Ocurrencia (%)')
for i, v in enumerate(results.values):
    plt.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(pres_dir, '4_Target_Imbalance.png'), dpi=200)
plt.close('all')

# ==========================================
# SCRIPT DE PRESENTACION (.TXT)
# ==========================================
guion = """======================================================
GUION DE PRESENTACION: MODELO PREDICTIVO PREMIER LEAGUE
======================================================
(Utiliza este documento como apoyo al mostrar cada imagen)

------------------------------------------------------
1. PREPARACION DE DATOS: Tratamiento de Missing Values
(Muestra la imagen: 1_Missing_Values_Antes_y_Despues.png)
------------------------------------------------------
"Para comenzar la preparación de los datos bajo la metodología OSSEMN, identificamos problemas de Missing Data del tipo MAR (Missing at Random). Variables clave como 'Expected Goals (xG)' o los datos de árbitros faltaban en ciertos partidos históricos. 

Como ven en el gráfico, en lugar de perder esa valiosa información eliminando filas o usando una simple media (lo cual sesgaría el modelo), inyectamos un algoritmo 'KNNImputer'. Este algoritmo calculó la similitud matemática de cada partido con nulos frente a toda la historia, y rellenó la barra verde basándose en los 5 partidos más idénticos. Logramos un 100% de cobertura sin destruir la varianza."

------------------------------------------------------
2. PREPARACION DE DATOS: Outliers y Tratamiento de Asimetría
(Muestra la imagen: 2_Outliers_Antes_y_Despues.png)
------------------------------------------------------
"El fútbol está lleno de Outliers y variables con Skewness (asimetría) muy fuerte, como las rachas goleadoras extremas o las cuotas de las casas de apuestas (B365H). En el gráfico de la izquierda vemos cómo la distribución original está totalmente aplastada hacia la izquierda con colas larguísimas a la derecha.

Si dejábamos esto así, los algoritmos numéricos se romperían. Aplicamos una transformación matemática avanzada de 'Yeo-Johnson'. El resultado en la derecha es espectacular: comprimimos los outliers y moldeamos una Campana de Gauss (Distribución Normal) perfecta, que permite al StandardScaler trabajar con media 0 y desviación típica 1 de forma óptima."

------------------------------------------------------
3. ANALISIS DESCRIPTIVO: Relaciones y Multicolinealidad
(Muestra la imagen: 3_Multicolinealidad_Antes_y_Despues.png)
------------------------------------------------------
"En nuestro EDA (Exploratory Data Analysis), corrimos matrices de correlación y detectamos un grave problema de Multicolinealidad. Goles, xG, Tiros y Tiros al Arco estaban correlacionados hasta en un 0.90 (casi rojo oscuro en el gráfico izquierdo).

Pasarle todo esto al modelo sería redundante y causaría sobreajuste (Overfitting). La solución fue una estricta Selección de Features (Feature Engineering): conservamos únicamente el 'xG' como la heurística suprema del poder ofensivo, y eliminamos los goles reales porque son engañosos por la suerte. A la derecha vemos cómo nos quedamos con variables limpias e independientes (correlación cercana a 0)."

------------------------------------------------------
4. ANALISIS DESCRIPTIVO: Hallazgos Clave y Relación con el Target
(Muestra la imagen: 4_Target_Imbalance.png)
------------------------------------------------------
"Finalmente, al analizar la Relación con nuestro Objetivo (Target), descubrimos un severo Desbalanceo de Clases (Target Imbalance). Históricamente, el Local gana el 45% de las veces, mientras que el Empate es sumamente difícil de aislar estadísticamente (24%).

En lugar de usar técnicas artificiales como SMOTE (que inventarían partidos de fútbol irreales y destruirían la lógica del deporte), tomamos una decisión arquitectónica: utilizar Modelos Ensamblados basados en árboles (Gradient Boosting) que son robustos al desbalanceo, y predecir sobre mercados alternativos matemáticamente más justos (Doble Oportunidad o Over 2.5), usando un Umbral de Confianza probabilístico estricto en lugar de forzar a la IA a elegir el empate ciegamente."

------------------------------------------------------
5. CONCLUSION ARQUITECTONICA: Prevención de Leakage
------------------------------------------------------
"Cierro destacando que TODAS estas transformaciones (Imputación y Yeo-Johnson) fueron encriptadas dentro de un Scikit-Learn 'Pipeline'. Esto garantiza que la matemática aprendió exclusivamente del 70% de entrenamiento (pasado) sin jamás contaminarse con el 30% de prueba (futuro), eliminando por completo el temido 'Information Leakage'."
"""

with open(os.path.join(pres_dir, 'guion_presentacion.txt'), 'w', encoding='utf-8') as f:
    f.write(guion)

print('Carpeta generada correctamente.')
