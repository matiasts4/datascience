import pandas as pd
import numpy as np
import os
import sys
import warnings
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import xgboost as xgb

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

def instantiate_meta_classifier(model_type):
    if model_type == 'Random Forest':
        return RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
    elif model_type == 'Logistic Regression':
        return LogisticRegression(C=0.5, random_state=42)
    elif model_type == 'SVM':
        return SVC(C=1.0, kernel='rbf', probability=True, random_state=42)
    elif model_type == 'XGBoost':
        return xgb.XGBClassifier(n_estimators=100, max_depth=3, eval_metric='logloss', random_state=42)
    else:
        raise ValueError(f"Modelo desconocido: {model_type}")

def run_simulation_multi_bets(df, mode='meta_model', model_type='Random Forest', edge_threshold=0.05, initial_bankroll=1000.0, num_splits=5):
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
            
            # Evaluar TODAS las opciones para este partido
            for opt_name, opt in all_options.items():
                ev = opt['prob'] * opt['odd'] - 1
                elo_diff, rest_diff = get_meta_features(row, opt_name)
                
                if mode in ['dynamic_ev', 'dual']:
                    edge_req = edge_threshold * max(1.0, np.sqrt(opt['odd'] - 1))
                else:
                    edge_req = edge_threshold
                    
                passes_ev = ev >= edge_req
                
                if passes_ev and bankroll > 0:
                    authorized = True
                    
                    if meta_clf is not None:
                        feats = np.array([[opt['prob'], opt['odd'], ev, elo_diff, rest_diff]])
                        p_win = meta_clf.predict_proba(feats)[0, 1]
                        
                        if p_win < 0.50:
                            authorized = False
                            bets_avoided += 1
                            
                    if authorized:
                        stake = 10.0  # Flat Staking 1%
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
                            
                if passes_ev:
                    historical_bets.append({
                        'prob': opt['prob'],
                        'odd': opt['odd'],
                        'ev': ev,
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
    
    print("\n==========================================================================")
    print("  SIMULACION CON APUESTAS MULTIPLES POR PARTIDO (Habilitando todo el Portafolio)")
    print("==========================================================================")
    
    # Línea base sin metamodelo
    res_base = run_simulation_multi_bets(df, mode='baseline')
    print(f"Línea Base (Sin Meta) : Banca = ${res_base['final_bankroll']:.2f} | ROI = {res_base['roi']:.2f}% | Apuestas = {res_base['bets']} | Drawdown = {res_base['max_dd']:.2f}%")
    
    res_dyn = run_simulation_multi_bets(df, mode='dynamic_ev')
    print(f"Solo EV Dinámico      : Banca = ${res_dyn['final_bankroll']:.2f} | ROI = {res_dyn['roi']:.2f}% | Apuestas = {res_dyn['bets']} | Drawdown = {res_dyn['max_dd']:.2f}%")
    
    print("\nEvaluando con Meta-Modelos (Modo Solo Meta-Modelo):")
    print("-" * 80)
    for model in ['Random Forest', 'Logistic Regression', 'SVM']:
        res = run_simulation_multi_bets(df, mode='meta_model', model_type=model)
        print(f"Meta ({model:<19}) : Banca = ${res['final_bankroll']:<8.2f} | ROI = {res['roi']:>5.2f}% | Apuestas = {res['bets']:<4} | Evitadas = {res['avoided']:<4} | Drawdown = {res['max_dd']:.2f}%")
        
    print("\nEvaluando con Meta-Modelos (Modo Sistema Dual EV + Meta):")
    print("-" * 80)
    for model in ['Random Forest', 'Logistic Regression', 'SVM']:
        res = run_simulation_multi_bets(df, mode='dual', model_type=model)
        print(f"Dual ({model:<19}) : Banca = ${res['final_bankroll']:<8.2f} | ROI = {res['roi']:>5.2f}% | Apuestas = {res['bets']:<4} | Evitadas = {res['avoided']:<4} | Drawdown = {res['max_dd']:.2f}%")

if __name__ == '__main__':
    main()
