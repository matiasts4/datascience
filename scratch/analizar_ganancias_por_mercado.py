import pandas as pd
import numpy as np
import os
import sys
import warnings
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

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
    else:
        raise ValueError(f"Modelo desconocido: {model_type}")

def run_detailed_simulation(df, mode='dual', model_type='Random Forest', edge_threshold=0.05, initial_bankroll=1000.0, num_splits=5):
    n_records = len(df)
    split_size = n_records // num_splits
    
    bankroll = initial_bankroll
    
    historical_bets = []
    detailed_bets = []
    
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
                'home': {'prob': row[f'p_home_{cal_mode}'], 'odd': row['B365H'], 'win': (row['target_1x2'] == 2), 'market': '1X2 (Home/Draw/Away)'},
                'draw': {'prob': row[f'p_draw_{cal_mode}'], 'odd': row['B365D'], 'win': (row['target_1x2'] == 1), 'market': '1X2 (Home/Draw/Away)'},
                'away': {'prob': row[f'p_away_{cal_mode}'], 'odd': row['B365A'], 'win': (row['target_1x2'] == 0), 'market': '1X2 (Home/Draw/Away)'},
                'dc_1X': {'prob': row[f'p_dc1X_{cal_mode}'], 'odd': row['B365_1X'], 'win': (row['target_dc_1X'] == 1), 'market': 'Double Chance 1X'},
                'dc_X2': {'prob': row[f'p_dcX2_{cal_mode}'], 'odd': row['B365_X2'], 'win': (row['target_dc_X2'] == 1), 'market': 'Double Chance X2'},
                'over': {'prob': row[f'p_over_{cal_mode}'], 'odd': row['B365>2.5'], 'win': (row['target_over_2_5_goals'] == 1), 'market': 'Over 2.5 Goals'},
                'under': {'prob': row[f'p_under_{cal_mode}'], 'odd': row['B365<2.5'], 'win': (row['target_under_2_5_goals'] == 1), 'market': 'Under 2.5 Goals'}
            }
            
            evs = {}
            for name, opt in all_options.items():
                evs[name] = {
                    'ev': opt['prob'] * opt['odd'] - 1,
                    'odd': opt['odd'],
                    'prob': opt['prob'],
                    'win': opt['win'],
                    'market': opt['market']
                }
                
            best_bet_name = max(evs, key=lambda k: evs[k]['ev'])
            best_bet = evs[best_bet_name]
            
            elo_diff, rest_diff = get_meta_features(row, best_bet_name)
            
            if mode in ['dynamic_ev', 'dual']:
                edge_req = edge_threshold * max(1.0, np.sqrt(best_bet['odd'] - 1))
            else:
                edge_req = edge_threshold
                
            passes_ev = best_bet['ev'] >= edge_req
            
            if passes_ev and bankroll > 0:
                autorized = True
                
                if meta_clf is not None:
                    feats = np.array([[best_bet['prob'], best_bet['odd'], best_bet['ev'], elo_diff, rest_diff]])
                    p_win = meta_clf.predict_proba(feats)[0, 1]
                    
                    if p_win < 0.50:
                        autorized = False
                        detailed_bets.append({
                            'market': best_bet['market'],
                            'win': best_bet['win'],
                            'net_profit': 0.0,
                            'status': 'Evitada (Falso Positivo)',
                            'stake': 10.0
                        })
                        
                if autorized:
                    stake = 10.0
                    if bankroll >= stake:
                        if best_bet['win']:
                            net_profit = stake * (best_bet['odd'] - 1)
                            status = 'Ganada'
                        else:
                            net_profit = -stake
                            status = 'Perdida'
                        
                        bankroll += net_profit
                        
                        detailed_bets.append({
                            'market': best_bet['market'],
                            'win': best_bet['win'],
                            'net_profit': net_profit,
                            'status': status,
                            'stake': stake
                        })
                        
            if passes_ev:
                historical_bets.append({
                    'prob': best_bet['prob'],
                    'odd': best_bet['odd'],
                    'ev': best_bet['ev'],
                    'elo_diff': elo_diff,
                    'rest_diff': rest_diff,
                    'win': best_bet['win']
                })
                
    return pd.DataFrame(detailed_bets)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sim_dir = os.path.join(current_dir, "..", "Simulacion_Inversion")
    csv_preds = os.path.join(sim_dir, "predicciones_prueba_calibradas.csv")
    csv_master = os.path.join(sim_dir, "historical_with_ou_odds.csv")
    
    if not os.path.exists(csv_preds) or not os.path.exists(csv_master):
        print("❌ Error: Faltan archivos de simulación")
        return
        
    df_preds = pd.read_csv(csv_preds)
    df_master = pd.read_csv(csv_master)
    
    df = pd.merge(df_preds, df_master[['game_id', 'home_elo', 'away_elo', 'home_rest', 'away_rest']], on='game_id', how='left')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Analizar para los dos mejores metamodelos en modo dual
    models = ['Random Forest', 'Logistic Regression']
    
    out_md = os.path.join(current_dir, "ganancias_por_mercado_metamodelo.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Analisis de Desempeño y Ganancias por Mercado del Meta-Modelo\n\n")
        f.write("Este reporte desglosa los resultados financieros de la simulación de segunda capa, agrupados por mercado de apuestas, para evaluar dónde genera mayor valor el Meta-Modelo.\n\n")
        
        for model in models:
            print(f"\nAnalizando rendimiento por mercado para: {model}")
            bets_df = run_detailed_simulation(df, mode='dual', model_type=model)
            
            # Agrupar estadísticas por mercado
            stats = []
            for name, group in bets_df.groupby('market'):
                total_candidates = len(group)
                placed_group = group[group['status'] != 'Evitada (Falso Positivo)']
                avoided_group = group[group['status'] == 'Evitada (Falso Positivo)']
                
                placed_count = len(placed_group)
                avoided_count = len(avoided_group)
                
                wins = len(placed_group[placed_group['status'] == 'Ganada'])
                losses = len(placed_group[placed_group['status'] == 'Perdida'])
                
                total_wagered = placed_group['stake'].sum()
                total_profit = placed_group['net_profit'].sum()
                
                win_rate = (wins / placed_count * 100) if placed_count > 0 else 0.0
                roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0.0
                
                stats.append({
                    'market': name,
                    'candidates': total_candidates,
                    'placed': placed_count,
                    'avoided': avoided_count,
                    'wins': wins,
                    'losses': losses,
                    'profit': total_profit,
                    'roi': roi,
                    'win_rate': win_rate
                })
                
            stats_df = pd.DataFrame(stats)
            
            # Escribir reporte markdown
            f.write(f"## Meta-Modelo: {model} (Sistema Dual)\n\n")
            f.write("| Mercado | Apuestas Candidatas | Apuestas Colocadas | Evitadas (Falsos Positivos) | Ganadas | Perdidas | ROI Neto | Ganancia Neta (USD) | Tasa de Acierto |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for _, r in stats_df.iterrows():
                f.write(f"| {r['market']} | {r['candidates']} | {r['placed']} | {r['avoided']} | {r['wins']} | {r['losses']} | {r['roi']:.2f}% | ${r['profit']:.2f} | {r['win_rate']:.2f}% |\n")
            
            # Totales del modelo
            tot_cand = stats_df['candidates'].sum()
            tot_plac = stats_df['placed'].sum()
            tot_avoi = stats_df['avoided'].sum()
            tot_wins = stats_df['wins'].sum()
            tot_loss = stats_df['losses'].sum()
            tot_prof = stats_df['profit'].sum()
            tot_wag = tot_plac * 10.0
            tot_roi = (tot_prof / tot_wag * 100) if tot_wag > 0 else 0.0
            tot_wr = (tot_wins / tot_plac * 100) if tot_plac > 0 else 0.0
            
            f.write(f"| **TOTAL PORTAFOLIO** | **{tot_cand}** | **{tot_plac}** | **{tot_avoi}** | **{tot_wins}** | **{tot_loss}** | **{tot_roi:.2f}%** | **${tot_prof:.2f}** | **{tot_wr:.2f}%** |\n\n")
            
            print(f"Rendimiento por mercado guardado en reporte.")
            
    print(f"\n[OK] Análisis por mercado completado. Reporte guardado en: {out_md}")

if __name__ == '__main__':
    main()
