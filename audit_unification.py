import pandas as pd
import os
import glob

v4_path = 'archive/pl-predictor/data/historical/all_match_features_v4_xg.csv'
df_v4 = pd.read_csv(v4_path)

# Normalizar temporada extrayendo el año de la fecha para poder cruzar
df_v4['year_from_date'] = pd.to_datetime(df_v4['date']).dt.year

print("======== AUDITORIA MASIVA DE INTEGRIDAD (RAW vs V4_XG) ========")
print(f"Total de Partidos V4_XG: {len(df_v4)}")

raw_base_dir = 'archive/pl-scraper/data/processed'
if not os.path.exists(raw_base_dir):
    print("No se encontró el directorio crudo.")
    exit()

directories = sorted(os.listdir(raw_base_dir))

total_raw_rows = 0
global_raw_cols = set()

print("\n--- Conteo Temporada por Temporada ---")
for d in directories:
    path = os.path.join(raw_base_dir, d, 'matches.csv')
    if os.path.isfile(path):
        raw = pd.read_csv(path)
        raw_len = len(raw)
        total_raw_rows += raw_len
        global_raw_cols.update(raw.columns)
        
        # Evaluar cómo la temporada fue nombrada
        # Para hacer el cruce, miramos la temporada nominal
        v4_season_count = len(df_v4[df_v4['season'].astype(str) == d])
        
        if v4_season_count == 0:
            # Quizas fue transformada a int (ej. 2122 -> 2021/2022)
            try:
                v4_season_count = len(df_v4[df_v4['season'] == int(d)])
            except:
                pass
                
        print(f"Directorio Crudo [{d}]: {raw_len} partidos | Partidos en V4: {v4_season_count}")

print(f"\n--- Sumas Totales ---")
print(f"Suma Total de Partidos en crudo: {total_raw_rows}")
print(f"Diferencia con V4: {len(df_v4) - total_raw_rows}")

print(f"\n--- Pérdida de Columnas ---")
missing_in_v4 = global_raw_cols - set(df_v4.columns)
if missing_in_v4:
    print(f"ALERTA: Se perdieron variables del Raw al unificar: {missing_in_v4}")
else:
    print("ÉXITO: Cero columnas perdidas. El V4 contiene todas las features crudas base.")

print("\n--- Auditoría de Nulos Críticos por Temporada en V4 ---")
# Agrupar por 'season' que tiene en V4 para ver de donde vienen los vacios
for col in ['home_xg', 'B365H', 'PSH', 'home_match_fouls']:
    if col in df_v4.columns:
        nulos = df_v4[df_v4[col].isnull()]
        if not nulos.empty:
            res = nulos.groupby('season').size()
            print(f"> Vacíos en '{col}' provienen de las temporadas:\n{res.to_string()}\n")
        else:
            print(f"> Vacíos en '{col}': 0")
