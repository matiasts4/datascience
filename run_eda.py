import pandas as pd
import numpy as np
import scipy.stats as stats
import warnings
warnings.filterwarnings('ignore')

# Use historical dataset for analysis
try:
    df = pd.read_csv("archive/pl-predictor/data/historical/all_match_features_v4_xg.csv")
    print("=== DATASET: all_match_features_v4_xg.csv (Historical Data) ===")
except:
    print("No se encontró el dataset. Prueba cambiando el path.")
    exit()

print("\n=== 1. ANALÍTICO EXPLORATORIO INICIAL (EDA) ===")
print(f"Dimensiones (Rows, Cols): {df.shape}")
print(f"Observaciones Duplicadas Absolutas: {df.duplicated().sum()}")

print("\n--- Valores Nulos (MCAR/MAR/MNAR) ---")
nulls = df.isnull().sum()
if nulls.sum() > 0:
    print(nulls[nulls > 0].to_string())
else:
    print("¡No hay valores nulos detectados!")

print("\n=== 2. DATOS INCORRECTOS (FORMATO Y OOR) ===")
print("Muestra de formatos en features claves:")
for c in ['date', 'time', 'score']:
    if c in df.columns:
        print(f"[{c}] -> {df[c].dropna().unique()[:3]}")

print("\n=== 3. DATOS INÚTILES (Varianza Cero & Multicolinealidad) ===")
zero_var = [col for col in df.columns if df[col].nunique() <= 1]
print(f"Constantes (Varianza Libre a eliminar): {zero_var if zero_var else 'Ninguna'}")

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

if num_cols:
    corr = df[num_cols].corr()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    high_corr = [column for column in upper.columns if any(upper[column] > 0.85)]
    print(f"Alta Multicolinealidad Numérica (>0.85): {high_corr if high_corr else 'Ninguna'}")

print("\n--- Fugas de Información (Leakage) ---")
if 'score' in df.columns:
    print("🚨 Peligro de Leakage: La columna 'score' y variables derivadas de partidos terminados conviven con features predictivos.")

print("\n=== 4. ASIMETRÍAS Y DISTRIBUCIONES (Skewness) ===")
if num_cols:
    skewness = df[num_cols].skew()
    highly_skewed = skewness[abs(skewness) > 1].index.tolist()
    print(f"Features asimétricos (candidatos a Log/Box-Cox/Yeo-Johnson): {highly_skewed if highly_skewed else 'Ninguno'}")

print("\n=== 5. OUTLIERS UNIDIMENSIONALES (IQR) ===")
for col in num_cols:
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    outliers = df[(df[col] < (q1 - 1.5 * iqr)) | (df[col] > (q3 + 1.5 * iqr))]
    if not outliers.empty:
        print(f"[{col}] -> {len(outliers)} outliers detectados.")
