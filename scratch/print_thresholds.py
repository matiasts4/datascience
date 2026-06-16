import pandas as pd
import numpy as np

def run_simulation_with_threshold(sim_df, market_type, edge_threshold, staking_strategy='flat', cal_mode='iso'):
    bankroll = 1000.0
    bets_count = 0
    wins_count = 0
    wagered = 0.0
    profit = 0.0
    
    for idx, row in sim_df.iterrows():
        evs = {}
        if market_type == '1x2':
            p_home = row[f'p_home_{cal_mode}']
            p_draw = row[f'p_draw_{cal_mode}']
            p_away = row[f'p_away_{cal_mode}']
            evs = {
                'home': {'ev': p_home * row['B365H'] - 1, 'odd': row['B365H'], 'win': (row['target_1x2'] == 2)},
                'draw': {'ev': p_draw * row['B365D'] - 1, 'odd': row['B365D'], 'win': (row['target_1x2'] == 1)},
                'away': {'ev': p_away * row['B365A'] - 1, 'odd': row['B365A'], 'win': (row['target_1x2'] == 0)}
            }
        elif market_type == 'portfolio_real':
            p_home = row[f'p_home_{cal_mode}']
            p_draw = row[f'p_draw_{cal_mode}']
            p_away = row[f'p_away_{cal_mode}']
            p_dc1X = row[f'p_dc1X_{cal_mode}']
            p_dcX2 = row[f'p_dcX2_{cal_mode}']
            p_over = row[f'p_over_{cal_mode}']
            p_under = row[f'p_under_{cal_mode}']
            
            evs = {
                'home': {'ev': p_home * row['B365H'] - 1, 'odd': row['B365H'], 'win': (row['target_1x2'] == 2)},
                'draw': {'ev': p_draw * row['B365D'] - 1, 'odd': row['B365D'], 'win': (row['target_1x2'] == 1)},
                'away': {'ev': p_away * row['B365A'] - 1, 'odd': row['B365A'], 'win': (row['target_1x2'] == 0)},
                'dc_1X': {'ev': p_dc1X * row['B365_1X'] - 1, 'odd': row['B365_1X'], 'win': (row['target_dc_1X'] == 1)},
                'dc_X2': {'ev': p_dcX2 * row['B365_X2'] - 1, 'odd': row['B365_X2'], 'win': (row['target_dc_X2'] == 1)},
                'over': {'ev': p_over * row['B365>2.5'] - 1, 'odd': row['B365>2.5'], 'win': (row['target_over_2_5_goals'] == 1)},
                'under': {'ev': p_under * row['B365<2.5'] - 1, 'odd': row['B365<2.5'], 'win': (row['target_under_2_5_goals'] == 1)}
            }
            
        if not evs:
            continue
            
        best_bet_name = max(evs, key=lambda k: evs[k]['ev'])
        best_ev_info = evs[best_bet_name]
        
        # Filtro de EV estático
        if best_ev_info['ev'] >= edge_threshold and bankroll > 0:
            odd = best_ev_info['odd']
            win = best_ev_info['win']
            stake = 10.0  # Flat Staking
            
            if bankroll >= stake:
                bets_count += 1
                wagered += stake
                if win:
                    net_profit = stake * (odd - 1)
                    wins_count += 1
                else:
                    net_profit = -stake
                bankroll += net_profit
                profit += net_profit
                
    roi = (profit / wagered * 100) if wagered > 0 else 0.0
    win_rate = (wins_count / bets_count * 100) if bets_count > 0 else 0.0
    return bets_count, bankroll, roi, win_rate

def main():
    df = pd.read_csv('Simulacion_Inversion/predicciones_prueba_calibradas.csv')
    grid = np.linspace(0.00, 0.30, 16)
    for t in grid:
        bets, bank, roi, wr = run_simulation_with_threshold(df, 'portfolio_real', t)
        print(f"Threshold: {t:.2f} | Bets: {bets:4d} | Bankroll: ${bank:7.2f} | ROI: {roi:5.2f}% | Win Rate: {wr:5.2f}%")

if __name__ == '__main__':
    main()
