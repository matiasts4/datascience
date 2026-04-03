import pandas as pd
import joblib
import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
HISTORICAL_DIR = os.path.join(BASE_DIR, "data", "historical")
MODELS_DIR = os.path.join(BASE_DIR, "models")
FEATURES_PATH = os.path.join(HISTORICAL_DIR, "all_match_features_v7.csv")

def run_oracle():
    print("="*60)
    print("🔮 ORÁCULO DE APUESTAS PREMIER LEAGUE 🔮")
    print("="*60)
    print("Cargando cerebro algorítmico...")
    
    try:
        df = pd.read_csv(FEATURES_PATH)
        scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
        m_1x2 = joblib.load(os.path.join(MODELS_DIR, 'model_1X2_Match_Winner.pkl'))
        m_dc1x = joblib.load(os.path.join(MODELS_DIR, 'model_Double_Chance_1X_Home_or_Draw.pkl'))
        m_dcx2 = joblib.load(os.path.join(MODELS_DIR, 'model_Double_Chance_X2_Away_or_Draw.pkl'))
        m_btts = joblib.load(os.path.join(MODELS_DIR, 'model_BTTS_Both_Teams_To_Score.pkl'))
    except Exception as e:
        print(f"Error cargando el modelo: {e}")
        return

    teams = sorted(list(df['home_team'].dropna().unique()))
    
    print("\nEquipos Disponibles:")
    for i in range(0, len(teams), 3):
        row = teams[i:i+3]
        print(" | ".join([t.ljust(20) for t in row]))

    home = input("\n⚽ Escribe el equipo LOCAL (ej. Arsenal): ").strip()
    away = input("⚽ Escribe el equipo VISITA (ej. Chelsea): ").strip()
    
    if home not in teams or away not in teams:
        print("❌ Error: Verifica que escribiste los nombres exactamente como arriba.")
        return
        
    print("\n💰 (Opcional pero Recomendado) Ingresa las cuotas actuales de Bet365/Betano para mayor precisión:")
    print("Si no las tienes, solo presiona ENTER reiteradas veces.")
    in_h = input(f"   Cuota {home} (Local): ")
    in_d = input(f"   Cuota Empate: ")
    in_a = input(f"   Cuota {away} (Visita): ")
    
    odds_h = float(in_h) if in_h.strip() else 2.5
    odds_d = float(in_d) if in_d.strip() else 3.2
    odds_a = float(in_a) if in_a.strip() else 2.5
    
    print(f"\n🔍 Analizando {home} vs {away}...\n")
    
    # Extraer últimas estadísticas conocidas de ambos
    h_stats = df[df['home_team'] == home].iloc[-1]
    a_stats = df[df['away_team'] == away].iloc[-1]
    
    # Construir el vector de features simulado
    from src.config import FEATURES
    sim = {}
    for f in FEATURES:
        if f.startswith('h_'): sim[f] = h_stats[f]
        elif f.startswith('a_'): sim[f] = a_stats[f]
        elif f == 'home_elo': sim[f] = h_stats['home_elo']
        elif f == 'away_elo': sim[f] = a_stats['away_elo']
        elif f == 'team_home_win_pct': sim[f] = h_stats['team_home_win_pct']
        elif f == 'team_away_win_pct': sim[f] = a_stats['team_away_win_pct']
        elif f == 'h2h_home_pts_avg':
            h2h = df[(df['home_team'] == home) & (df['away_team'] == away)]
            sim[f] = h2h['h2h_home_pts_avg'].iloc[-1] if not h2h.empty else 1.5
        elif f == 'B365H': sim[f] = odds_h
        elif f == 'B365D': sim[f] = odds_d
        elif f == 'B365A': sim[f] = odds_a
        elif f == 'precipitation_mm':
            sim[f] = 0.0 # Will be updated via LIVE api below
        elif f == 'temp_max_c':
            sim[f] = 15.0 # Will be updated via LIVE api below
        elif f == 'is_raining':
            sim[f] = 0
        elif f == 'is_cold':
            sim[f] = 0
        else:
            sim[f] = h_stats.get(f, 0)
            
    # ── LIVE WEATHER INJECTION ──
    from integrar_clima import STADIUM_COORDS
    import requests
    if home in STADIUM_COORDS:
        lat, lon = STADIUM_COORDS[home]
        try:
            w_url = 'https://api.open-meteo.com/v1/forecast'
            r = requests.get(w_url, params={'latitude': lat, 'longitude': lon, 'daily': 'precipitation_sum,temperature_2m_max', 'timezone': 'Europe/London', 'forecast_days': 3}, timeout=5).json()
            tomorrow_rain = r['daily']['precipitation_sum'][1]
            tomorrow_temp = r['daily']['temperature_2m_max'][1]
            sim['precipitation_mm'] = tomorrow_rain
            sim['temp_max_c'] = tomorrow_temp
            sim['is_raining'] = 1 if tomorrow_rain > 1.0 else 0
            sim['is_cold'] = 1 if tomorrow_temp < 8.0 else 0
            print(f"🌦  CLIMA EN VIVO: Se detectó {tomorrow_temp}°C y {tomorrow_rain}mm de lluvia para el partido.")
        except:
            print("🌦  CLIMA EN VIVO: No se pudo conectar a OpenMeteo, usando promedios históricos.")
    # ─────────────────────────────
            
    X = pd.DataFrame([sim])[FEATURES]
    X_sc = scaler.transform(X)
    
    # Predictions
    p_1x2 = m_1x2.predict_proba(X_sc)[0]
    p_dc1x = m_dc1x.predict_proba(X_sc)[0][1]
    p_dcx2 = m_dcx2.predict_proba(X_sc)[0][1]
    p_btts = m_btts.predict_proba(X_sc)[0][1]
    
    print("--------------------------------------------------")
    print("📊 MATRIZ DE PROBABILIDADES IA:")
    print(f"   Victoria Local ({home}):  {p_1x2[0]*100:.1f}%")
    print(f"   Empate:                   {p_1x2[1]*100:.1f}%")
    print(f"   Victoria Visita ({away}): {p_1x2[2]*100:.1f}%")
    print("--------------------------------------------------")
    print(f"   🛡 Mercado Seguro 1 (1X): {p_dc1x*100:.1f}% probabil. de acierto.")
    print(f"   🛡 Mercado Seguro 2 (X2): {p_dcx2*100:.1f}% probabil. de acierto.")
    print(f"   ⚡ Ambos Marcan (BTTS):   {p_btts*100:.1f}% probabil. de acierto.")
    print("--------------------------------------------------")
    
    print("\n💰 RECOMENDACIÓN DEL TRADER (BOT):")
    if p_dc1x > 0.73:
        print(f"   👉 APUESTA ESTRELLA: Doble Oportunidad 'Local o Empate' (Confianza extrema: {p_dc1x*100:.1f}%).")
        print("      *Ideal para construir bankroll conservador este fin de semana.*")
    elif p_1x2[2] > 0.50:
        print(f"   👉 APUESTA DE VALOR: El visitante ({away}) tiene mucho momentum. Apuesta 'Visita' Directo o X2.")
    else:
        print("   ⚠️ PARTIDO CAÓTICO: Las estadísticas chocan. Recomendable EVITAR apostar dinero aquí.")
        
    print("\n============================================================")

if __name__ == "__main__":
    run_oracle()
