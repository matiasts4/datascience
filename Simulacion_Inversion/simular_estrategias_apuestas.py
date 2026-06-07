import pandas as pd
import numpy as np
import os
import sys
import json
import warnings
import matplotlib.pyplot as plt
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator

# Configurar rutas para importar desde archive/pl-predictor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive', 'pl-predictor')))
from src.config import TARGETS, FEATURES, MODELS_DIR
from evaluar_comparativa_completa import create_pipeline, instantiate_classifier, prepare_targets

warnings.filterwarnings("ignore")

def run_single_simulation(sim_df, market_type, initial_bankroll=1000.0, edge_threshold=0.05, staking_strategy='quarter', cal_mode='uncal'):
    """
    Simula una estrategia de apuestas para un mercado específico (1x2, over, under, o portfolio)
    utilizando una configuración de calibración dada ('uncal', 'iso', 'sig').
    """
    bankroll = initial_bankroll
    history = [bankroll]
    
    bets_count = 0
    wins_count = 0
    wagered = 0.0
    profit = 0.0
    
    for idx, row in sim_df.iterrows():
        evs = {}
        
        # Obtener probabilidades correspondientes al modo de calibración
        if market_type == '1x2':
            p_home = row[f'p_home_{cal_mode}']
            p_draw = row[f'p_draw_{cal_mode}']
            p_away = row[f'p_away_{cal_mode}']
            
            ev_home = p_home * row['B365H'] - 1
            ev_draw = p_draw * row['B365D'] - 1
            ev_away = p_away * row['B365A'] - 1
            
            evs = {
                'home': {'ev': ev_home, 'odd': row['B365H'], 'prob': p_home, 'win': (row['target_1x2'] == 2)},
                'draw': {'ev': ev_draw, 'odd': row['B365D'], 'prob': p_draw, 'win': (row['target_1x2'] == 1)},
                'away': {'ev': ev_away, 'odd': row['B365A'], 'prob': p_away, 'win': (row['target_1x2'] == 0)}
            }
        elif market_type == 'over':
            p_over = row[f'p_over_{cal_mode}']
            ev_over = p_over * row['B365>2.5'] - 1
            evs = {
                'over': {'ev': ev_over, 'odd': row['B365>2.5'], 'prob': p_over, 'win': (row['target_over_2_5_goals'] == 1)}
            }
        elif market_type == 'under':
            p_under = row[f'p_under_{cal_mode}']
            ev_under = p_under * row['B365<2.5'] - 1
            evs = {
                'under': {'ev': ev_under, 'odd': row['B365<2.5'], 'prob': p_under, 'win': (row['target_under_2_5_goals'] == 1)}
            }
        elif market_type == 'portfolio':
            p_home = row[f'p_home_{cal_mode}']
            p_draw = row[f'p_draw_{cal_mode}']
            p_away = row[f'p_away_{cal_mode}']
            p_over = row[f'p_over_{cal_mode}']
            p_under = row[f'p_under_{cal_mode}']
            
            ev_home = p_home * row['B365H'] - 1
            ev_draw = p_draw * row['B365D'] - 1
            ev_away = p_away * row['B365A'] - 1
            ev_over = p_over * row['B365>2.5'] - 1
            ev_under = p_under * row['B365<2.5'] - 1
            
            evs = {
                'home': {'ev': ev_home, 'odd': row['B365H'], 'prob': p_home, 'win': (row['target_1x2'] == 2)},
                'draw': {'ev': ev_draw, 'odd': row['B365D'], 'prob': p_draw, 'win': (row['target_1x2'] == 1)},
                'away': {'ev': ev_away, 'odd': row['B365A'], 'prob': p_away, 'win': (row['target_1x2'] == 0)},
                'over': {'ev': ev_over, 'odd': row['B365>2.5'], 'prob': p_over, 'win': (row['target_over_2_5_goals'] == 1)},
                'under': {'ev': ev_under, 'odd': row['B365<2.5'], 'prob': p_under, 'win': (row['target_under_2_5_goals'] == 1)}
            }
            
        # Si no hay opciones, saltar
        if not evs:
            history.append(bankroll)
            continue
            
        # Seleccionar la opción de mayor EV
        best_bet_name = max(evs, key=lambda k: evs[k]['ev'])
        best_ev_info = evs[best_bet_name]
        
        if best_ev_info['ev'] >= edge_threshold and bankroll > 0:
            odd = best_ev_info['odd']
            prob = best_ev_info['prob']
            ev = best_ev_info['ev']
            win = best_ev_info['win']
            
            # Determinar stake según la estrategia de capital
            if staking_strategy == 'flat':
                stake = 10.0  # 1% de banca inicial ($1000)
            elif staking_strategy == 'kelly':
                f_star = ev / (odd - 1)
                f_star = min(max(f_star, 0.0), 0.10)  # Max 10%
                stake = f_star * bankroll
            elif staking_strategy == 'half':
                f_star = 0.5 * (ev / (odd - 1))
                f_star = min(max(f_star, 0.0), 0.05)  # Max 5%
                stake = f_star * bankroll
            elif staking_strategy == 'quarter':
                f_star = 0.25 * (ev / (odd - 1))
                f_star = min(max(f_star, 0.0), 0.025)  # Max 2.5%
                stake = f_star * bankroll
            elif staking_strategy == 'edge':
                f_star = 0.5 * ev
                f_star = min(max(f_star, 0.0), 0.05)  # Max 5%
                stake = f_star * bankroll
            else:
                stake = 10.0
                
            # Ejecutar apuesta
            if bankroll >= stake and stake > 0.10:
                bets_count += 1
                wagered += stake
                if win:
                    net_profit = stake * (odd - 1)
                    wins_count += 1
                else:
                    net_profit = -stake
                bankroll += net_profit
                profit += net_profit
                
        history.append(bankroll)
        
    # Calcular Max Drawdown
    h_arr = np.array(history)
    peaks = np.maximum.accumulate(h_arr)
    peaks = np.where(peaks == 0, 1.0, peaks)
    drawdowns = (peaks - h_arr) / peaks
    max_dd = float(np.max(drawdowns) * 100)
    
    roi = (profit / wagered * 100) if wagered > 0 else 0.0
    win_rate = (wins_count / bets_count * 100) if bets_count > 0 else 0.0
    
    return {
        'final_bankroll': bankroll,
        'wagered': wagered,
        'profit': profit,
        'roi': roi,
        'bets': bets_count,
        'win_rate': win_rate,
        'max_dd': max_dd,
        'history': history
    }

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_input_path = os.path.join(current_dir, "historical_with_ou_odds.csv")
    
    if not os.path.exists(csv_input_path):
        print(f"[Error] No se encontró el dataset con cuotas Over/Under en: {csv_input_path}")
        print("Por favor ejecuta obtener_cuotas_over_under.py primero.")
        return
        
    json_path = os.path.join(MODELS_DIR, "optimized_hyperparams.json")
    if not os.path.exists(json_path):
        print(f"[Error] No se encontró el archivo de hiperparámetros optimizados {json_path}")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        optimized_data = json.load(f)
        
    df = pd.read_csv(csv_input_path)
    df = df[df['game_id'].astype(str) != '0'].reset_index(drop=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = prepare_targets(df)
    
    X = df[FEATURES]
    tscv = TimeSeriesSplit(n_splits=5)
    
    # ─────────────────────────────────────────────────────────────────────────
    # 1. Obtener predicciones (Sin Calibrar, Isotónica, Sigmoide)
    # ─────────────────────────────────────────────────────────────────────────
    markets_to_simulate = {
        '1X2 (Match Winner)': {
            'target': 'target_1x2',
            'model_name': 'Logistic Regression (Elastic Net)',
            'use_tomek': True
        },
        'Over 2.5 Goals': {
            'target': 'target_over_2_5_goals',
            'model_name': 'XGBoost (L1/L2 Regularized)',
            'use_tomek': False
        },
        'Under 2.5 Goals': {
            'target': 'target_under_2_5_goals',
            'model_name': 'XGBoost (L1/L2 Regularized)',
            'use_tomek': False
        }
    }
    
    sim_df = df[['game_id', 'date', 'home_team', 'away_team', 'target_1x2', 'target_over_2_5_goals', 'target_under_2_5_goals', 'B365H', 'B365D', 'B365A', 'B365>2.5', 'B365<2.5']].copy()
    
    for market_name, m_info in markets_to_simulate.items():
        print(f"\nEntrenando y calibrando para {market_name}...")
        y = df[m_info['target']]
        
        opt_info = optimized_data[market_name][m_info['model_name']]
        opt_params = opt_info["best_params"]
        
        probs_uncal_all = []
        probs_iso_all = []
        probs_sig_all = []
        test_indices = []
        
        for split_idx, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # 1. Modelo base (Sin Calibrar): Entrenado en el 100% de X_train para el test fold
            pipe_uncal = create_pipeline(instantiate_classifier(m_info['model_name'], opt_params), use_tomek=m_info['use_tomek'])
            pipe_uncal.fit(X_train, y_train)
            probs_uncal = pipe_uncal.predict_proba(X_test)
            probs_uncal_all.append(probs_uncal)
            test_indices.extend(test_idx)
            
            # 2. Modelos Calibrados: División temporal (80% sub-train / 20% calibration)
            split_point = int(len(train_idx) * 0.8)
            sub_train_idx = train_idx[:split_point]
            cal_idx = train_idx[split_point:]
            
            X_tr, y_tr = X.iloc[sub_train_idx], y.iloc[sub_train_idx]
            X_cal, y_cal = X.iloc[cal_idx], y.iloc[cal_idx]
            
            classes_tr = np.unique(y_tr)
            classes_cal = np.unique(y_cal)
            
            if set(classes_tr) == set(classes_cal) and len(classes_tr) > 1:
                # Entrenar modelo base en 80%
                pipe_base = create_pipeline(instantiate_classifier(m_info['model_name'], opt_params), use_tomek=m_info['use_tomek'])
                pipe_base.fit(X_tr, y_tr)
                
                # Envolver en FrozenEstimator
                frozen_pipe = FrozenEstimator(pipe_base)
                
                # Crear CV manual para calibrar en toda la data de calibración sin splits internos
                cv_custom = [(np.arange(len(X_cal)), np.arange(len(X_cal)))]
                
                # Calibración Isotónica
                cal_iso = CalibratedClassifierCV(estimator=frozen_pipe, method='isotonic', cv=cv_custom)
                cal_iso.fit(X_cal, y_cal)
                probs_iso = cal_iso.predict_proba(X_test)
                
                # Calibración Sigmoide
                cal_sig = CalibratedClassifierCV(estimator=frozen_pipe, method='sigmoid', cv=cv_custom)
                cal_sig.fit(X_cal, y_cal)
                probs_sig = cal_sig.predict_proba(X_test)
            else:
                print(f"      [Aviso] Split {split_idx+1}: Clases inconsistentes en calibración ({classes_cal} vs {classes_tr}). Usando fallback no calibrado.")
                probs_iso = probs_uncal
                probs_sig = probs_uncal
                
            probs_iso_all.append(probs_iso)
            probs_sig_all.append(probs_sig)
            
        probs_uncal_all = np.vstack(probs_uncal_all)
        probs_iso_all = np.vstack(probs_iso_all)
        probs_sig_all = np.vstack(probs_sig_all)
        
        # Guardar predicciones alineadas
        if market_name == '1X2 (Match Winner)':
            sim_df.loc[test_indices, 'p_away_uncal'] = probs_uncal_all[:, 0]
            sim_df.loc[test_indices, 'p_draw_uncal'] = probs_uncal_all[:, 1]
            sim_df.loc[test_indices, 'p_home_uncal'] = probs_uncal_all[:, 2]
            
            sim_df.loc[test_indices, 'p_away_iso'] = probs_iso_all[:, 0]
            sim_df.loc[test_indices, 'p_draw_iso'] = probs_iso_all[:, 1]
            sim_df.loc[test_indices, 'p_home_iso'] = probs_iso_all[:, 2]
            
            sim_df.loc[test_indices, 'p_away_sig'] = probs_sig_all[:, 0]
            sim_df.loc[test_indices, 'p_draw_sig'] = probs_sig_all[:, 1]
            sim_df.loc[test_indices, 'p_home_sig'] = probs_sig_all[:, 2]
            
        elif market_name == 'Over 2.5 Goals':
            sim_df.loc[test_indices, 'p_over_uncal'] = probs_uncal_all[:, 1]
            sim_df.loc[test_indices, 'p_over_iso'] = probs_iso_all[:, 1]
            sim_df.loc[test_indices, 'p_over_sig'] = probs_sig_all[:, 1]
            
        elif market_name == 'Under 2.5 Goals':
            sim_df.loc[test_indices, 'p_under_uncal'] = probs_uncal_all[:, 1]
            sim_df.loc[test_indices, 'p_under_iso'] = probs_iso_all[:, 1]
            sim_df.loc[test_indices, 'p_under_sig'] = probs_sig_all[:, 1]

    # Filtrar nulos (eliminar observaciones que no cayeron en el test set de validación)
    sim_df = sim_df.dropna(subset=['p_home_uncal', 'p_over_uncal', 'p_under_uncal']).reset_index(drop=True)
    # Filtrar nulos en cuotas reales de Bet365
    sim_df = sim_df.dropna(subset=['B365H', 'B365D', 'B365A', 'B365>2.5', 'B365<2.5']).reset_index(drop=True)
    print(f"\n[OK] Partidos listos para simulación cronológica con calibración: {len(sim_df)}")
    
    # Guardar predicciones de prueba para inspección del usuario
    pred_path = os.path.join(current_dir, "predicciones_prueba_calibradas.csv")
    sim_df.to_csv(pred_path, index=False)
    print(f"[OK] Predicciones detalladas de prueba guardadas en: {pred_path}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 2. Correr Simulación sobre las 60 combinaciones posibles
    # ─────────────────────────────────────────────────────────────────────────
    edge_threshold = 0.05
    initial_bankroll = 1000.0
    
    cal_modes = ['uncal', 'iso', 'sig']
    staking_strategies = ['flat', 'kelly', 'half', 'quarter', 'edge']
    market_types = ['1x2', 'over', 'under', 'portfolio']
    
    report_rows = []
    all_runs_results = {}
    
    print("\nEjecutando simulaciones...")
    for c_mode in cal_modes:
        all_runs_results[c_mode] = {}
        for m_type in market_types:
            all_runs_results[c_mode][m_type] = {}
            for strategy in staking_strategies:
                res = run_single_simulation(sim_df, m_type, initial_bankroll, edge_threshold, strategy, c_mode)
                all_runs_results[c_mode][m_type][strategy] = res
                
                report_rows.append({
                    'Calibracion': c_mode.upper(),
                    'Mercado': m_type.upper(),
                    'Gestion Capital': strategy.upper(),
                    'Banca Final': f"${res['final_bankroll']:.2f}",
                    'Monto Apostado': f"${res['wagered']:.2f}",
                    'ROI': f"{res['roi']:.2f}%",
                    'Total Apuestas': res['bets'],
                    'Win Rate': f"{res['win_rate']:.2f}%",
                    'Max Drawdown': f"{res['max_dd']:.2f}%"
                })
                
    report_df = pd.DataFrame(report_rows)
    report_csv_path = os.path.join(current_dir, "reporte_simulacion_calibrada.csv")
    report_df.to_csv(report_csv_path, index=False)
    print(f"[OK] Reporte completo guardado en: {report_csv_path}")
    
    # Mostrar resumen por pantalla para Quarter Kelly (antes causaba ruina)
    print("\n==========================================================================================================")
    print("                IMPACTO DE LA CALIBRACIÓN BAJO ESTRATEGIA QUARTER KELLY (MAX 2.5%)")
    print("==========================================================================================================")
    print(f"{'Mercado':<12} | {'Calibración':<12} | {'Banca Final':<12} | {'ROI':<8} | {'Apuestas':<8} | {'Max Drawdown':<8}")
    print("-" * 106)
    for m_type in market_types:
        for c_mode in cal_modes:
            res = all_runs_results[c_mode][m_type]['quarter']
            c_name = 'Sin Calibrar' if c_mode == 'uncal' else ('Isotónica' if c_mode == 'iso' else 'Sigmoide')
            print(f"{m_type.upper():<12} | {c_name:<12} | ${res['final_bankroll']:<11.2f} | {res['roi']:>6.2f}% | {res['bets']:<8} | {res['max_dd']:>6.2f}%")
        print("-" * 106)
    print("==========================================================================================================")

    # Mostrar resumen para Flat Stake (el control)
    print("\n==========================================================================================================")
    print("                IMPACTO DE LA CALIBRACIÓN BAJO ESTRATEGIA FLAT STAKE (1% FIJO)")
    print("==========================================================================================================")
    print(f"{'Mercado':<12} | {'Calibración':<12} | {'Banca Final':<12} | {'ROI':<8} | {'Apuestas':<8} | {'Max Drawdown':<8}")
    print("-" * 106)
    for m_type in market_types:
        for c_mode in cal_modes:
            res = all_runs_results[c_mode][m_type]['flat']
            c_name = 'Sin Calibrar' if c_mode == 'uncal' else ('Isotónica' if c_mode == 'iso' else 'Sigmoide')
            print(f"{m_type.upper():<12} | {c_name:<12} | ${res['final_bankroll']:<11.2f} | {res['roi']:>6.2f}% | {res['bets']:<8} | {res['max_dd']:>6.2f}%")
        print("-" * 106)
    print("==========================================================================================================")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Generar Panel de Gráficos 2x2 para las curvas de capital
    # ─────────────────────────────────────────────────────────────────────────
    fig, axs = plt.subplots(2, 2, figsize=(16, 10))
    plt.rcParams['font.family'] = 'sans-serif'
    
    dates = [sim_df['date'].iloc[0]] + list(sim_df['date'])
    
    # Configuración de subplots
    plot_configs = [
        # (row, col, market, strategy, title)
        (0, 0, 'over', 'quarter', 'Over 2.5 Goals (Staking: Quarter Kelly)'),
        (0, 1, 'portfolio', 'quarter', 'Portfolio Combinado (Staking: Quarter Kelly)'),
        (1, 0, 'over', 'flat', 'Over 2.5 Goals (Staking: Flat Stake 1%)'),
        (1, 1, 'portfolio', 'flat', 'Portfolio Combinado (Staking: Flat Stake 1%)')
    ]
    
    colors = {
        'uncal': '#718096', # Slate (Sin calibración, peligro/línea base)
        'iso': '#3182CE',   # Sleek Blue (Calibración Isotónica)
        'sig': '#38A169'    # Forest Green (Calibración Sigmoide)
    }
    
    labels = {
        'uncal': 'Sin Calibrar (Baseline)',
        'iso': 'Calibración Isotónica',
        'sig': 'Calibración Sigmoide (Platt)'
    }
    
    for r, c, m_type, strat, title in plot_configs:
        ax = axs[r, c]
        for c_mode in cal_modes:
            history = all_runs_results[c_mode][m_type][strat]['history']
            ax.plot(dates, history, label=labels[c_mode], color=colors[c_mode], linewidth=1.5 if c_mode=='uncal' else 2.0)
            
        ax.axhline(y=1000.0, color='black', linestyle=':', alpha=0.6)
        ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
        ax.set_xlabel('Línea Temporal de Partidos', fontsize=9)
        ax.set_ylabel('Banca (USD)', fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.5, color='#CBD5E0')
        ax.legend(frameon=True, facecolor='white', edgecolor='#E2E8F0', loc='upper left', fontsize=8.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
    plt.suptitle('Comparativa de Curvas de Capital: Calibración vs. No Calibración\n(Simulación de Inversión Cronológica en BetAnalytics)', fontsize=14, fontweight='bold', y=0.98)
    
    fig_path = os.path.join(current_dir, "35_Simulacion_Rentabilidad_Apuestas.png")
    plt.tight_layout()
    plt.subplots_adjust(top=0.90)
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Copiar también a Carpeta_Presentacion para que esté listo en las diapositivas
    pres_fig_path = os.path.abspath(os.path.join(current_dir, "..", "Carpeta_Presentacion", "35_Simulacion_Rentabilidad_Apuestas.png"))
    try:
        import shutil
        shutil.copy(fig_path, pres_fig_path)
        print(f"[OK] Gráfico copiado a carpeta de presentación: {pres_fig_path}")
    except Exception as e:
        print(f"[Aviso] No se pudo copiar el gráfico a la carpeta de presentación: {e}")
        
    print(f"[OK] Panel comparativo 2x2 guardado exitosamente en: {fig_path}")

if __name__ == "__main__":
    main()
