"""
integrar_momentum.py
--------------------
Fase 4: Añade métricas de 'Momentum Psicológico' (Rachas).

Para cada equipo, calcula secuencialmente:
  - win_streak  : Cantidad de victorias consecutivas actuales
  - loss_streak : Cantidad de derrotas consecutivas actuales
  - unbeaten_streak: Cantidad de partidos sin perder

Fusiona con all_match_features_v6.csv → all_match_features_v7.csv
"""

import pandas as pd
import os

BASE_DIR       = os.path.abspath(os.path.dirname(__file__))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
INPUT_PATH     = os.path.join(HISTORICAL_DIR, "all_match_features_v6.csv")
OUTPUT_PATH    = os.path.join(HISTORICAL_DIR, "all_match_features_v7.csv")

def calculate_streaks(df):
    """Calcula rachas iterando por fecha para asegurar causalidad."""
    df = df.sort_values("date").reset_index(drop=True)
    
    # Llevar cuenta del estado actual por equipo
    streaks = {}
    
    h_win_streak = []
    h_loss_streak = []
    h_unbeaten_streak = []
    
    a_win_streak = []
    a_loss_streak = []
    a_unbeaten_streak = []
    
    for idx, row in df.iterrows():
        ht = row['home_team']
        at = row['away_team']
        
        if ht not in streaks:
            streaks[ht] = {'w': 0, 'l': 0, 'u': 0}
        if at not in streaks:
            streaks[at] = {'w': 0, 'l': 0, 'u': 0}
            
        # Registrar el estado ANTES del partido
        h_win_streak.append(streaks[ht]['w'])
        h_loss_streak.append(streaks[ht]['l'])
        h_unbeaten_streak.append(streaks[ht]['u'])
        
        a_win_streak.append(streaks[at]['w'])
        a_loss_streak.append(streaks[at]['l'])
        a_unbeaten_streak.append(streaks[at]['u'])
        
        # Determinar resultado
        hg = row['home_goals']
        ag = row['away_goals']
        
        # Actualizar rachas LOCAL
        if hg > ag: # Home Win
            streaks[ht]['w'] += 1
            streaks[ht]['l'] = 0
            streaks[ht]['u'] += 1
        elif hg == ag: # Draw
            streaks[ht]['w'] = 0
            streaks[ht]['l'] = 0
            streaks[ht]['u'] += 1
        else: # Away Win
            streaks[ht]['w'] = 0
            streaks[ht]['l'] += 1
            streaks[ht]['u'] = 0
            
        # Actualizar rachas VISITA
        if ag > hg: # Away Win
            streaks[at]['w'] += 1
            streaks[at]['l'] = 0
            streaks[at]['u'] += 1
        elif ag == hg: # Draw
            streaks[at]['w'] = 0
            streaks[at]['l'] = 0
            streaks[at]['u'] += 1
        else: # Home Win
            streaks[at]['w'] = 0
            streaks[at]['l'] += 1
            streaks[at]['u'] = 0
            
    df['h_win_streak'] = h_win_streak
    df['h_loss_streak'] = h_loss_streak
    df['h_unbeaten_streak'] = h_unbeaten_streak
    
    df['a_win_streak'] = a_win_streak
    df['a_loss_streak'] = a_loss_streak
    df['a_unbeaten_streak'] = a_unbeaten_streak
    
    return df

def main():
    print("=" * 60)
    print("Fase 4: Integrando Momentum Psicológico (Rachas)")
    print("=" * 60)

    print(f"\n[1/2] Cargando {INPUT_PATH}...")
    df = pd.read_csv(INPUT_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Calcular rachas
    print("\n[2/2] Calculando rachas históricas por equipo...")
    df = calculate_streaks(df)
    
    print(f"\n✅ Guardando → all_match_features_v7.csv...")
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"   Total partidos: {len(df)}")
    print("   Nuevas columnas de rachas agregadas.")

if __name__ == "__main__":
    main()
