import pandas as pd
import numpy as np
import os
import sys
import warnings
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import xgboost as xgb

warnings.filterwarnings("ignore")

# Configurar ruta para poder importar desde archive/pl-predictor si es necesario
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive', 'pl-predictor')))

def get_meta_features(row, bet_type):
    h_elo = row['home_elo']
    a_elo = row['away_elo']
    h_rest = row['home_rest']
    a_rest = row['away_rest']
    
    if bet_type == 'home':
        elo_diff = h_elo - a_elo
        rest_diff = h_rest - a_rest
    elif bet_type == 'away':
        elo_diff = a_elo - h_elo
        rest_diff = a_rest - h_rest
    elif bet_type == 'draw':
        elo_diff = -abs(h_elo - a_elo)
        rest_diff = abs(h_rest - a_rest)
    elif bet_type == 'dc_1X':
        elo_diff = h_elo - a_elo
        rest_diff = h_rest - a_rest
    elif bet_type == 'dc_X2':
        elo_diff = a_elo - h_elo
        rest_diff = a_rest - h_rest
    elif bet_type in ['over', 'under']:
        elo_diff = abs(h_elo - a_elo)
        rest_diff = h_rest + a_rest
    else:
        elo_diff = 0.0
        rest_diff = 0.0
        
    return elo_diff, rest_diff

def instantiate_meta_classifier(model_type):
    if model_type == 'Random Forest':
        return RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
    elif model_type == 'Logistic Regression':
        return LogisticRegression(C=0.5, random_state=42)
    elif model_type == 'SVM':
        # probability=True es necesario para predict_proba
        return SVC(C=1.0, kernel='rbf', probability=True, random_state=42)
    elif model_type == 'XGBoost':
        return xgb.XGBClassifier(n_estimators=100, max_depth=3, eval_metric='logloss', random_state=42)
    else:
        raise ValueError(f"Modelo desconocido: {model_type}")

def run_simulation_with_clf(df, mode='meta_model', model_type='Random Forest', edge_threshold=0.05, initial_bankroll=1000.0, num_splits=5):
    n_records = len(df)
    split_size = n_records // num_splits
    
    bankroll = initial_bankroll
    history = [bankroll]
    
    bets_count = 0
    wins_count = 0
    wagered = 0.0
    profit = 0.0
    bets_avoided = 0
    
    historical_bets = []
    
    for s_idx in range(num_splits):
        start_idx = s_idx * split_size
        end_idx = (s_idx + 1) * split_size if s_idx < num_splits - 1 else n_records
        
        df_split = df.iloc[start_idx:end_idx]
        
        meta_clf = None
        if s_idx > 0 and mode in ['meta_model', 'dual']:
            train_records = []
            for b in historical_bets:
                train_records.append({
                    'prob': b['prob'],
                    'odd': b['odd'],
                    'ev': b['ev'],
                    'elo_diff': b['elo_diff'],
                    'rest_diff': b['rest_diff'],
                    'win': int(b['win'])
                })
            
            if len(train_records) >= 30:
                train_df = pd.DataFrame(train_records)
                X_meta = train_df[['prob', 'odd', 'ev', 'elo_diff', 'rest_diff']]
                y_meta = train_df['win']
                
                meta_clf = instantiate_meta_classifier(model_type)
                meta_clf.fit(X_meta, y_meta)
        
        for idx, row in df_split.iterrows():
            cal_mode = 'iso'
            all_options = {
                'home': {'prob': row[f'p_home_{cal_mode}'], 'odd': row['B365H'], 'win': (row['target_1x2'] == 2)},
                'draw': {'prob': row[f'p_draw_{cal_mode}'], 'odd': row['B365D'], 'win': (row['target_1x2'] == 1)},
                'away': {'prob': row[f'p_away_{cal_mode}'], 'odd': row['B365A'], 'win': (row['target_1x2'] == 0)},
                'dc_1X': {'prob': row[f'p_dc1X_{cal_mode}'], 'odd': row['B365_1X'], 'win': (row['target_dc_1X'] == 1)},
                'dc_X2': {'prob': row[f'p_dcX2_{cal_mode}'], 'odd': row['B365_X2'], 'win': (row['target_dc_X2'] == 1)},
                'over': {'prob': row[f'p_over_{cal_mode}'], 'odd': row['B365>2.5'], 'win': (row['target_over_2_5_goals'] == 1)},
                'under': {'prob': row[f'p_under_{cal_mode}'], 'odd': row['B365<2.5'], 'win': (row['target_under_2_5_goals'] == 1)}
            }
            
            evs = {}
            for name, opt in all_options.items():
                evs[name] = {
                    'ev': opt['prob'] * opt['odd'] - 1,
                    'odd': opt['odd'],
                    'prob': opt['prob'],
                    'win': opt['win']
                }
                
            best_bet_name = max(evs, key=lambda k: evs[k]['ev'])
            best_bet = evs[best_bet_name]
            
            elo_diff, rest_diff = get_meta_features(row, best_bet_name)
            
            if mode in ['dynamic_ev', 'dual']:
                edge_req = edge_threshold * max(1.0, np.sqrt(best_bet['odd'] - 1))
            else:
                edge_req = edge_threshold
                
            passes_ev = best_bet['ev'] >= edge_req
            
            placed_bet = False
            if passes_ev and bankroll > 0:
                autorized = True
                
                if meta_clf is not None:
                    feats = np.array([[best_bet['prob'], best_bet['odd'], best_bet['ev'], elo_diff, rest_diff]])
                    p_win = meta_clf.predict_proba(feats)[0, 1]
                    
                    if p_win < 0.50:
                        autorized = False
                        bets_avoided += 1
                        
                if autorized:
                    stake = 10.0  # Flat Staking 1%
                    if bankroll >= stake:
                        bets_count += 1
                        wagered += stake
                        if best_bet['win']:
                            net_profit = stake * (best_bet['odd'] - 1)
                            wins_count += 1
                        else:
                            net_profit = -stake
                        bankroll += net_profit
                        profit += net_profit
                        placed_bet = True
                        
            if passes_ev:
                historical_bets.append({
                    'prob': best_bet['prob'],
                    'odd': best_bet['odd'],
                    'ev': best_bet['ev'],
                    'elo_diff': elo_diff,
                    'rest_diff': rest_diff,
                    'win': best_bet['win']
                })
                
            history.append(bankroll)
            
    h_arr = np.array(history)
    peaks = np.maximum.accumulate(h_arr)
    peaks = np.where(peaks == 0, 1.0, peaks)
    drawdowns = (peaks - h_arr) / peaks
    max_dd = float(np.max(drawdowns) * 100)
    
    roi = (profit / wagered * 100) if wagered > 0 else 0.0
    win_rate = (wins_count / bets_count * 100) if bets_count > 0 else 0.0
    
    return {
        'final_bankroll': bankroll,
        'roi': roi,
        'bets': bets_count,
        'win_rate': win_rate,
        'max_dd': max_dd,
        'avoided': bets_avoided,
        'history': history
    }

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sim_dir = os.path.join(current_dir, "..", "Simulacion_Inversion")
    csv_preds = os.path.join(sim_dir, "predicciones_prueba_calibradas.csv")
    csv_master = os.path.join(sim_dir, "historical_with_ou_odds.csv")
    
    if not os.path.exists(csv_preds) or not os.path.exists(csv_master):
        print("❌ Error: Faltan archivos de simulación en la carpeta Simulacion_Inversion")
        return
        
    df_preds = pd.read_csv(csv_preds)
    df_master = pd.read_csv(csv_master)
    
    df = pd.merge(df_preds, df_master[['game_id', 'home_elo', 'away_elo', 'home_rest', 'away_rest']], on='game_id', how='left')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    meta_models = ['Random Forest', 'Logistic Regression', 'SVM', 'XGBoost']
    modes = ['meta_model', 'dual']
    
    print("\n==========================================================================")
    print("      ESTUDIO COMPARATIVO DE ALGORITMOS DE META-DECISION (META-LABELING)")
    print("==========================================================================")
    
    results = []
    # Estructura para almacenar historiales para graficar
    plot_data = {mode: {} for mode in modes}
    
    for mode in modes:
        mode_label = "Solo Meta-Modelo" if mode == 'meta_model' else "Sistema Dual (EV + Meta)"
        print(f"\nModo de Operación: {mode_label}")
        print(f"{'Algoritmo Meta-Modelo':<25} | {'Banca Final':<12} | {'ROI':<8} | {'Apuestas':<8} | {'Evitadas':<8} | {'Max Drawdown':<8}")
        print("-" * 85)
        for model in meta_models:
            res = run_simulation_with_clf(df, mode=mode, model_type=model)
            print(f"{model:<25} | ${res['final_bankroll']:<11.2f} | {res['roi']:>6.2f}% | {res['bets']:<8} | {res['avoided']:<8} | {res['max_dd']:>6.2f}%")
            results.append({
                'modo': mode_label,
                'algoritmo': model,
                'banca_final': res['final_bankroll'],
                'roi': res['roi'],
                'apuestas': res['bets'],
                'evitadas': res['avoided'],
                'max_dd': res['max_dd']
            })
            plot_data[mode][model] = res['history']
        print("-" * 85)
        
    # Guardar reporte de comparación
    report_df = pd.DataFrame(results)
    out_md = os.path.join(current_dir, "comparacion_algoritmos_metamodelo.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Comparativa de Algoritmos para el Meta-Modelo (Meta-Labeling)\n\n")
        f.write("Este reporte compara el desempeño de las 4 opciones de algoritmos evaluados para actuar como Meta-Modelo.\n\n")
        
        for mode in ["Solo Meta-Modelo", "Sistema Dual (EV + Meta)"]:
            f.write(f"## {mode}\n\n")
            f.write("| Algoritmo Meta-Modelo | Banca Final | ROI | Apuestas | Evitadas (Falsos Positivos) | Max Drawdown |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
            mode_rows = report_df[report_df['modo'] == mode]
            for _, r in mode_rows.iterrows():
                f.write(f"| {r['algoritmo']} | ${r['banca_final']:.2f} | {r['roi']:.2f}% | {r['apuestas']} | {r['evitadas']} | {r['max_dd']:.2f}% |\n")
            f.write("\n")
            
    # -------------------------------------------------------------------------
    # GENERAR GRÁFICO COMPARATIVO
    # -------------------------------------------------------------------------
    dates = [df['date'].iloc[0] - pd.Timedelta(days=1)] + list(df['date'])
    colors = {
        'Random Forest': '#3182CE',       # Azul
        'Logistic Regression': '#48BB78', # Verde
        'SVM': '#ED8936',                 # Naranja
        'XGBoost': '#E53E3E'              # Rojo
    }
    
    fig, axs = plt.subplots(1, 2, figsize=(20, 8.5))
    
    for idx, mode in enumerate(modes):
        ax = axs[idx]
        mode_label = "Solo Meta-Modelo" if mode == 'meta_model' else "Sistema Dual (EV + Meta)"
        ax.set_title(f"Estrategias bajo: {mode_label}", fontsize=13, fontweight='bold', pad=12)
        
        # Graficar la línea base original (sin metamodelo) para comparar
        if mode == 'meta_model':
            base_res = run_simulation_with_clf(df, mode='baseline')
            ax.plot(dates, base_res['history'], label='Línea Base Original (Sin Meta)', color='#718096', linestyle=':', linewidth=2.0)
        else:
            base_res = run_simulation_with_clf(df, mode='dynamic_ev')
            ax.plot(dates, base_res['history'], label='Línea Base EV Dinámico (Sin Meta)', color='#718096', linestyle=':', linewidth=2.0)
            
        for model in meta_models:
            history = plot_data[mode][model]
            ax.plot(dates, history, label=model, color=colors[model], linewidth=2.0)
            
        ax.axhline(y=1000.0, color='#2D3748', linestyle=':', alpha=0.5)
        ax.set_xlabel('Línea Temporal de Partidos', fontsize=10)
        ax.set_ylabel('Banca (USD)', fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.4, color='#CBD5E0')
        ax.legend(frameon=True, facecolor='white', edgecolor='#E2E8F0', loc='upper left', fontsize=9.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        def dollar_format(x, pos):
            return f"${x:.0f}"
        ax.yaxis.set_major_formatter(FuncFormatter(dollar_format))
        
    plt.suptitle("Estudio Comparativo: Curvas de Capital de Diferentes Algoritmos para Meta-Labeling\n(Banca Inicial $1,000 USD | Flat Staking 1% | Validación Walk-Forward sin Leakage)", fontsize=16, fontweight='bold', y=0.97)
    plt.tight_layout()
    plt.subplots_adjust(top=0.88)
    
    # Guardar en local
    fig_path = os.path.join(current_dir, "comparativa_algoritmos_metamodelo.png")
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Guardar copia en la carpeta de presentación para las diapositivas
    pres_fig_path = os.path.abspath(os.path.join(current_dir, "..", "Carpeta_Presentacion", "comparativa_algoritmos_metamodelo.png"))
    try:
        import shutil
        shutil.copy(fig_path, pres_fig_path)
        print(f"[OK] Gráfico copiado a carpeta de presentación: {pres_fig_path}")
    except Exception as e:
        print(f"[Aviso] No se pudo copiar el gráfico a la carpeta de presentación: {e}")
        
    print(f"\n[OK] Comparativa finalizada. Reporte Markdown guardado en: {out_md}")
    print(f"[OK] Gráfico guardado en: {fig_path}")

if __name__ == '__main__':
    main()
