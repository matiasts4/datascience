import pandas as pd
import numpy as np
import os
import sys
import json
import warnings
import matplotlib.pyplot as plt
from sklearn.model_selection import TimeSeriesSplit

# Configurar rutas para importar desde archive/pl-predictor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive', 'pl-predictor')))
from src.config import FEATURES_PATH, TARGETS, FEATURES, MODELS_DIR
from evaluar_comparativa_completa import create_pipeline, instantiate_classifier, prepare_targets

warnings.filterwarnings("ignore")

def run_simulation(sim_df, initial_bankroll=1000.0, edge_threshold=0.05):
    """
    Simula las estrategias de apuestas sobre el DataFrame de predicciones.
    """
    # Inicializar historiales de banca
    bankroll_flat = initial_bankroll
    bankroll_kelly = initial_bankroll
    bankroll_half = initial_bankroll
    bankroll_quarter = initial_bankroll
    bankroll_edge = initial_bankroll
    
    history_flat = [bankroll_flat]
    history_kelly = [bankroll_kelly]
    history_half = [bankroll_half]
    history_quarter = [bankroll_quarter]
    history_edge = [bankroll_edge]
    
    # Contadores de apuestas
    stats = {
        'flat': {'bets': 0, 'wins': 0, 'wagered': 0.0, 'profit': 0.0},
        'kelly': {'bets': 0, 'wins': 0, 'wagered': 0.0, 'profit': 0.0},
        'half': {'bets': 0, 'wins': 0, 'wagered': 0.0, 'profit': 0.0},
        'quarter': {'bets': 0, 'wins': 0, 'wagered': 0.0, 'profit': 0.0},
        'edge': {'bets': 0, 'wins': 0, 'wagered': 0.0, 'profit': 0.0}
    }
    
    for idx, row in sim_df.iterrows():
        # Calcular el valor esperado (EV) para cada opción
        # clases: 0 (Away), 1 (Draw), 2 (Home)
        ev_home = row['p_home'] * row['B365H'] - 1
        ev_draw = row['p_draw'] * row['B365D'] - 1
        ev_away = row['p_away'] * row['B365A'] - 1
        
        evs = {
            2: {'ev': ev_home, 'odd': row['B365H'], 'prob': row['p_home'], 'name': 'Home'},
            1: {'ev': ev_draw, 'odd': row['B365D'], 'prob': row['p_draw'], 'name': 'Draw'},
            0: {'ev': ev_away, 'odd': row['B365A'], 'prob': row['p_away'], 'name': 'Away'}
        }
        
        # Encontrar la mejor opción de apuesta (la de mayor EV)
        best_class = max(evs, key=lambda k: evs[k]['ev'])
        best_ev_info = evs[best_class]
        
        placed_bet = False
        if best_ev_info['ev'] >= edge_threshold:
            placed_bet = True
            odd = best_ev_info['odd']
            prob = best_ev_info['prob']
            ev = best_ev_info['ev']
            win = (row['target_1x2'] == best_class)
            
            # --- 1. ESTRATEGIA STAKE FIJO (FLAT STAKE) ---
            if bankroll_flat > 0:
                stake = 10.0  # 1% de la banca inicial ($1000)
                if bankroll_flat >= stake:
                    stats['flat']['bets'] += 1
                    stats['flat']['wagered'] += stake
                    if win:
                        profit = stake * (odd - 1)
                        stats['flat']['wins'] += 1
                    else:
                        profit = -stake
                    bankroll_flat += profit
                    stats['flat']['profit'] += profit
            
            # --- 2. ESTRATEGIA KELLY CRITERION (FULL KELLY) ---
            if bankroll_kelly > 0:
                f_star = ev / (odd - 1)
                f_star = min(max(f_star, 0.0), 0.10)  # Max 10% de la banca actual por seguridad
                stake = f_star * bankroll_kelly
                if stake > 0.10:
                    stats['kelly']['bets'] += 1
                    stats['kelly']['wagered'] += stake
                    if win:
                        profit = stake * (odd - 1)
                        stats['kelly']['wins'] += 1
                    else:
                        profit = -stake
                    bankroll_kelly += profit
                    stats['kelly']['profit'] += profit
            
            # --- 3. ESTRATEGIA HALF KELLY (0.5 KELLY) ---
            if bankroll_half > 0:
                f_star = 0.5 * (ev / (odd - 1))
                f_star = min(max(f_star, 0.0), 0.05)  # Max 5% de la banca actual
                stake = f_star * bankroll_half
                if stake > 0.10:
                    stats['half']['bets'] += 1
                    stats['half']['wagered'] += stake
                    if win:
                        profit = stake * (odd - 1)
                        stats['half']['wins'] += 1
                    else:
                        profit = -stake
                    bankroll_half += profit
                    stats['half']['profit'] += profit
            
            # --- 4. ESTRATEGIA QUARTER KELLY (0.25 KELLY) ---
            if bankroll_quarter > 0:
                f_star = 0.25 * (ev / (odd - 1))
                f_star = min(max(f_star, 0.0), 0.025)  # Max 2.5% de la banca actual
                stake = f_star * bankroll_quarter
                if stake > 0.10:
                    stats['quarter']['bets'] += 1
                    stats['quarter']['wagered'] += stake
                    if win:
                        profit = stake * (odd - 1)
                        stats['quarter']['wins'] += 1
                    else:
                        profit = -stake
                    bankroll_quarter += profit
                    stats['quarter']['profit'] += profit
            
            # --- 5. ESTRATEGIA PROPORCIONAL AL EDGE ---
            if bankroll_edge > 0:
                f_star = 0.5 * ev  # Si el EV es del 10%, apostamos 5%
                f_star = min(max(f_star, 0.0), 0.05)  # Max 5%
                stake = f_star * bankroll_edge
                if stake > 0.10:
                    stats['edge']['bets'] += 1
                    stats['edge']['wagered'] += stake
                    if win:
                        profit = stake * (odd - 1)
                        stats['edge']['wins'] += 1
                    else:
                        profit = -stake
                    bankroll_edge += profit
                    stats['edge']['profit'] += profit

        # Guardar en el historial (se mantiene constante si no se apostó)
        history_flat.append(bankroll_flat)
        history_kelly.append(bankroll_kelly)
        history_half.append(bankroll_half)
        history_quarter.append(bankroll_quarter)
        history_edge.append(bankroll_edge)

    def get_max_drawdown(history):
        history = np.array(history)
        peaks = np.maximum.accumulate(history)
        peaks = np.where(peaks == 0, 1.0, peaks)
        drawdowns = (peaks - history) / peaks
        return float(np.max(drawdowns) * 100)

    results = {}
    for strat, name in [('flat', 'Stake Fijo (1%)'), ('kelly', 'Kelly Completo (Max 10%)'), 
                        ('half', 'Half Kelly (Max 5%)'), ('quarter', 'Quarter Kelly (Max 2.5%)'),
                        ('edge', 'Proporcional al Edge (Max 5%)')]:
        b_hist = eval(f"history_{strat}")
        final_b = b_hist[-1]
        roi = (stats[strat]['profit'] / stats[strat]['wagered'] * 100) if stats[strat]['wagered'] > 0 else 0.0
        win_rate = (stats[strat]['wins'] / stats[strat]['bets'] * 100) if stats[strat]['bets'] > 0 else 0.0
        
        results[strat] = {
            'name': name,
            'final_bankroll': final_b,
            'wagered': stats[strat]['wagered'],
            'profit': stats[strat]['profit'],
            'roi': roi,
            'bets': stats[strat]['bets'],
            'win_rate': win_rate,
            'max_dd': get_max_drawdown(b_hist),
            'history': b_hist
        }
    return results

def main():
    # Obtener el directorio donde reside este script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    json_path = os.path.join(MODELS_DIR, "optimized_hyperparams.json")
    if not os.path.exists(json_path):
        print(f"[Error] No se encontró el archivo de hiperparámetros optimizados {json_path}")
        return
        
    if not os.path.exists(FEATURES_PATH):
        print(f"[Error] No se encontró el dataset {FEATURES_PATH}")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        optimized_data = json.load(f)
        
    df = pd.read_csv(FEATURES_PATH)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = prepare_targets(df)
    
    # El mercado a simular es exclusivamente 1X2 Match Winner
    target_name = "1X2 (Match Winner)"
    target_col = TARGETS[target_name]
    y = df[target_col]
    X = df[FEATURES]
    
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Cargar mejor modelo
    opt_info = optimized_data[target_name]["Logistic Regression (Elastic Net)"]
    opt_params = opt_info["best_params"]
    
    print(f"[OK] Cargados parámetros de Logistic Regression para {target_name}: {opt_params}")
    
    clf = instantiate_classifier("Logistic Regression (Elastic Net)", opt_params)
    pipe = create_pipeline(clf, use_tomek=True) # Utiliza Tomek Links
    
    all_test_predictions = []
    
    print("\nGenerando predicciones out-of-fold para el conjunto de prueba (TimeSeriesSplit)...")
    for split_idx, (train_idx, test_idx) in enumerate(tscv.split(X)):
        print(f"  > Procesando Split {split_idx + 1}/5...")
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Entrenar en entrenamiento y predecir en prueba (libres de leakage)
        pipe.fit(X_train, y_train)
        probs = pipe.predict_proba(X_test)
        
        test_df = df.iloc[test_idx].copy()
        test_df['p_away'] = probs[:, 0]
        test_df['p_draw'] = probs[:, 1]
        test_df['p_home'] = probs[:, 2]
        
        cols = ['game_id', 'date', 'home_team', 'away_team', 'B365H', 'B365D', 'B365A', 'target_1x2', 'p_home', 'p_draw', 'p_away']
        all_test_predictions.append(test_df[cols])
        
    sim_df = pd.concat(all_test_predictions).sort_values('date').reset_index(drop=True)
    
    # Filtrar partidos sin cuotas reales de Bet365
    initial_matches = len(sim_df)
    sim_df = sim_df.dropna(subset=['B365H', 'B365D', 'B365A']).reset_index(drop=True)
    print(f"[OK] Consolidados {len(sim_df)} partidos de prueba cronológicos (de {initial_matches} iniciales, tras eliminar nulos en cuotas).")
    
    # Guardar las predicciones out-of-fold para auditoría
    pred_csv_path = os.path.join(current_dir, "predicciones_prueba_1x2.csv")
    sim_df.to_csv(pred_csv_path, index=False)
    print(f"[OK] Guardadas predicciones out-of-fold en: {pred_csv_path}")
    
    # Ejecutar simulación
    initial_bankroll = 1000.0
    edge_threshold = 0.05 # 5% de ventaja mínima requerida para apostar
    
    print(f"\nCorriendo simulador de apuestas (Banca Inicial: ${initial_bankroll:.2f}, Ventaja Mínima: {edge_threshold:.1%})...")
    results = run_simulation(sim_df, initial_bankroll, edge_threshold)
    
    # Guardar reporte en CSV
    report_data = []
    print("\n==========================================================================================")
    print("                      RESULTADOS DE LA SIMULACIÓN DE APUESTAS (1X2)")
    print("==========================================================================================")
    print(f"{'Estrategia':<32} | {'Banca Final':<12} | {'ROI':<8} | {'Apuestas':<8} | {'Win Rate':<10} | {'Max DD':<8}")
    print("-" * 90)
    for strat, data in results.items():
        print(f"{data['name']:<32} | ${data['final_bankroll']:<11.2f} | {data['roi']:>6.2f}% | {data['bets']:<8} | {data['win_rate']:>7.2f}% | {data['max_dd']:>6.2f}%")
        report_data.append({
            'Estrategia': data['name'],
            'Banca Final': data['final_bankroll'],
            'Monto Total Apostado': data['wagered'],
            'Ganancia Neta': data['profit'],
            'ROI': f"{data['roi']:.2f}%",
            'Total Apuestas': data['bets'],
            'Tasa de Acierto': f"{data['win_rate']:.2f}%",
            'Max Drawdown': f"{data['max_dd']:.2f}%"
        })
    print("==========================================================================================")
    
    report_csv_path = os.path.join(current_dir, "reporte_simulacion_apuestas.csv")
    pd.DataFrame(report_data).to_csv(report_csv_path, index=False)
    print(f"[OK] Guardado reporte tabular en: {report_csv_path}")
    
    # Generar gráfico comparativo
    plt.figure(figsize=(12, 6))
    plt.rcParams['font.family'] = 'sans-serif'
    
    dates = [sim_df['date'].iloc[0]] + list(sim_df['date'])
    
    colors = {
        'flat': '#4A5568',     # Slate Gray
        'kelly': '#E53E3E',    # Red
        'half': '#DD6B20',     # Orange
        'quarter': '#38A169',  # Green
        'edge': '#3182CE'      # Royal Blue
    }
    
    for strat, data in results.items():
        plt.plot(dates, data['history'], label=f"{data['name']} (ROI: {data['roi']:.1f}%, DD: {data['max_dd']:.1f}%)", 
                 color=colors[strat], linewidth=1.5 if strat != 'quarter' else 2.0)
                 
    plt.title('Simulación de Rentabilidad Económica: Curvas de Crecimiento de Capital (Banca Inicial: $1,000)\n(Estrategias de Inversión sobre Predicciones Out-Of-Fold de Validación Cruzada)', fontsize=13, fontweight='bold', pad=15)
    plt.xlabel('Línea Temporal de Partidos de Prueba (Temporadas 2018 - 2025)', fontsize=10)
    plt.ylabel('Banca Consolidada (USD)', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5, color='#CBD5E0')
    plt.legend(frameon=True, facecolor='white', edgecolor='#E2E8F0', loc='upper left')
    
    # Quitar bordes innecesarios
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    fig_path = os.path.join(current_dir, "35_Simulacion_Rentabilidad_Apuestas.png")
    
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n[OK] Gráfico de simulación guardado exitosamente en: {fig_path}")

if __name__ == "__main__":
    main()
