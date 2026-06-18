import pandas as pd
import numpy as np
import os
import sys
import warnings
import matplotlib.pyplot as plt
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

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

def run_simulation_k_limits(df, mode='dual', edge_threshold=0.05, k_limit=1, sort_by='ev', initial_bankroll=1000.0, num_splits=5):
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
    
    # Definir exclusiones mutuas
    conflicts = {
        'home': ['draw', 'away', 'dc_X2'],
        'draw': ['home', 'away'],
        'away': ['home', 'draw', 'dc_1X'],
        'dc_1X': ['away', 'dc_X2'],
        'dc_X2': ['home', 'dc_1X'],
        'over': ['under'],
        'under': ['over']
    }
    
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
                
                meta_clf = SVC(C=1.0, kernel='rbf', probability=True, random_state=42)
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
            
            options_eval = []
            for name, opt in all_options.items():
                ev = opt['prob'] * opt['odd'] - 1
                options_eval.append({
                    'name': name,
                    'prob': opt['prob'],
                    'odd': opt['odd'],
                    'ev': ev,
                    'win': opt['win']
                })
            
            # 1. Filtrar las que tengan EV >= threshold
            candidate_options = []
            for opt in options_eval:
                if mode in ['dynamic_ev', 'dual']:
                    edge_req = edge_threshold * max(1.0, np.sqrt(opt['odd'] - 1))
                else:
                    edge_req = edge_threshold
                
                if opt['ev'] >= edge_req:
                    candidate_options.append(opt)
            
            # 2. Ordenar según estrategia
            if sort_by == 'prob':
                candidate_options = sorted(candidate_options, key=lambda x: x['prob'], reverse=True)
            else: # Ordenar por EV (defecto del sistema)
                candidate_options = sorted(candidate_options, key=lambda x: x['ev'], reverse=True)
            
            # 3. Colocar hasta K apuestas por partido respetando exclusiones mutuas
            bets_placed_in_match = 0
            blocked_names = set()
            
            for opt in candidate_options:
                if bets_placed_in_match >= k_limit:
                    break
                    
                if opt['name'] in blocked_names:
                    continue
                
                elo_diff, rest_diff = get_meta_features(row, opt['name'])
                
                authorized = True
                if meta_clf is not None:
                    feats = np.array([[opt['prob'], opt['odd'], opt['ev'], elo_diff, rest_diff]])
                    p_win = meta_clf.predict_proba(feats)[0, 1]
                    if p_win < 0.50:
                        authorized = False
                        bets_avoided += 1
                
                if authorized and bankroll > 0:
                    stake = 10.0
                    if bankroll >= stake:
                        bets_count += 1
                        wagered += stake
                        if opt['win']:
                            net_profit = stake * (opt['odd'] - 1)
                            wins_count += 1
                        else:
                            net_profit = -stake
                        bankroll += net_profit
                        profit += net_profit
                        bets_placed_in_match += 1
                        
                        if opt['name'] in conflicts:
                            for conflict_name in conflicts[opt['name']]:
                                blocked_names.add(conflict_name)
                                
                historical_bets.append({
                    'prob': opt['prob'],
                    'odd': opt['odd'],
                    'ev': opt['ev'],
                    'elo_diff': elo_diff,
                    'rest_diff': rest_diff,
                    'win': opt['win']
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
        'avoided': bets_avoided
    }

def main():
    sim_dir = "Simulacion_Inversion"
    csv_preds = os.path.join(sim_dir, "predicciones_prueba_calibradas.csv")
    csv_master = os.path.join(sim_dir, "historical_with_ou_odds.csv")
    
    df_preds = pd.read_csv(csv_preds)
    df_master = pd.read_csv(csv_master)
    
    df = pd.merge(df_preds, df_master[['game_id', 'home_elo', 'away_elo', 'home_rest', 'away_rest']], on='game_id', how='left')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    k_values = [1, 2, 3, 4]
    strategies = ['ev', 'prob']
    
    print("\n==========================================================================")
    print("      ESTUDIO COMPARATIVO DE LÍMITE K Y ESTRATEGIAS DE PRIORIZACIÓN")
    print("==========================================================================")
    
    results = []
    
    for strat in strategies:
        strat_name = "Priorización por EV (Valor)" if strat == 'ev' else "Priorización por Probabilidad (Confianza)"
        print(f"\n>>> Estrategia: {strat_name} <<<")
        print("-" * 75)
        for k in k_values:
            res_base = run_simulation_k_limits(df, mode='dynamic_ev', k_limit=k, sort_by=strat)
            res_dual = run_simulation_k_limits(df, mode='dual', k_limit=k, sort_by=strat)
            print(f"  K = {k} | Base EV: ${res_base['final_bankroll']:.2f} (ROI: {res_base['roi']:.2f}%) | Dual SVM: ${res_dual['final_bankroll']:.2f} (ROI: {res_dual['roi']:.2f}%, Bets: {res_dual['bets']})")
            results.append({
                'strat': strat,
                'k': k,
                'banca_base': res_base['final_bankroll'],
                'banca_dual': res_dual['final_bankroll'],
                'roi_dual': res_dual['roi'],
                'apuestas_dual': res_dual['bets']
            })
            
    # -------------------------------------------------------------------------
    # GENERAR GRÁFICO COMPARATIVO DUAL
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))
    
    x = np.arange(len(k_values))
    width = 0.35
    
    # Subplot 1: Priorización por EV
    ev_res = [r for r in results if r['strat'] == 'ev']
    ax1.bar(x - width/2, [r['banca_base'] for r in ev_res], width, label='Línea Base EV (Sin Meta)', color='#E53E3E')
    rects_ev = ax1.bar(x + width/2, [r['banca_dual'] for r in ev_res], width, label='Sistema Dual SVM (Capa 2)', color='#38A169')
    ax1.axhline(y=1000.0, color='#2D3748', linestyle='--', alpha=0.7)
    ax1.set_title('Priorización por EV (Valor Matemático)', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'K = {k}\n(Max {k})' for k in k_values])
    ax1.set_ylabel('Banca Final (USD)')
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.legend(loc='upper right')
    
    for rect in rects_ev:
        height = rect.get_height()
        ax1.annotate(f'${height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9.5)
        
    # Subplot 2: Priorización por Probabilidad
    prob_res = [r for r in results if r['strat'] == 'prob']
    ax2.bar(x - width/2, [r['banca_base'] for r in prob_res], width, label='Línea Base EV (Sin Meta)', color='#E53E3E')
    rects_prob = ax2.bar(x + width/2, [r['banca_dual'] for r in prob_res], width, label='Sistema Dual SVM (Capa 2)', color='#3182CE')
    ax2.axhline(y=1000.0, color='#2D3748', linestyle='--', alpha=0.7)
    ax2.set_title('Priorización por Probabilidad (Confianza)', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'K = {k}\n(Max {k})' for k in k_values])
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.legend(loc='upper right')
    
    for rect in rects_prob:
        height = rect.get_height()
        ax2.annotate(f'${height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9.5)
        
    plt.suptitle('Estudio de Sensibilidad del Límite K y Estrategias de Ordenamiento\n(Banca Inicial $1,000 | Flat Staking 1% | Con Restricciones de Exclusión Mutua)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.subplots_adjust(top=0.86)
    
    fig_path = "scratch/comparativa_limite_k.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    
    # Copiar a Carpeta_Presentacion
    pres_path = "Carpeta_Presentacion/comparativa_limite_k.png"
    try:
        import shutil
        shutil.copy(fig_path, pres_path)
        print(f"[OK] Gráfico copiado a presentación: {pres_path}")
    except Exception as e:
        print(f"[Aviso] No se pudo copiar: {e}")
        
    print(f"\n[OK] Simulación finalizada. Gráfico dual guardado en: {fig_path}")

if __name__ == '__main__':
    main()
