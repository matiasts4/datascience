import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

plt.style.use('default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pres_dir = os.path.abspath(os.path.join(current_dir, "..", "Carpeta_Presentacion"))
    csv_preds = os.path.abspath(os.path.join(current_dir, "..", "Simulacion_Inversion", "predicciones_prueba_calibradas.csv"))
    
    if not os.path.exists(csv_preds):
        print(f"❌ Error: No se encontró {csv_preds}")
        return
        
    df = pd.read_csv(csv_preds)
    
    # -------------------------------------------------------------------------
    # GRÁFICO 1: SIMULACIÓN DE THRESHOLDS (Banca final y ROI vs. Threshold)
    # -------------------------------------------------------------------------
    grid = np.linspace(0.00, 0.30, 31)
    bancas = []
    rois = []
    bets = []
    
    for t in grid:
        b_count, bank, roi, _ = run_simulation_with_threshold(df, 'portfolio_real', t)
        bancas.append(bank)
        rois.append(roi)
        bets.append(b_count)
        
    bancas = np.array(bancas)
    rois = np.array(rois)
    bets = np.array(bets)
    
    # Encontrar óptimo basado en banca final
    idx_opt = np.argmax(bancas)
    t_opt = grid[idx_opt]
    banca_opt = bancas[idx_opt]
    roi_opt = rois[idx_opt]
    bets_opt = bets[idx_opt]
    
    fig, ax1 = plt.subplots(figsize=(11, 6.5))
    
    color_banca = '#1abc9c'
    ax1.set_xlabel('Threshold de Valor Esperado (EV)', fontweight='bold', fontsize=11, labelpad=10)
    ax1.set_ylabel('Banca Final ($)', color=color_banca, fontweight='bold', fontsize=11)
    line1 = ax1.plot(grid, bancas, 'o-', color=color_banca, linewidth=2.5, markersize=5, label='Banca Final ($)')
    ax1.tick_params(axis='y', labelcolor=color_banca)
    ax1.set_ylim(950, max(bancas) + 100)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Añadir segundo eje para el ROI
    ax2 = ax1.twinx()  
    color_roi = '#e74c3c'
    ax2.set_ylabel('ROI Neto (%)', color=color_roi, fontweight='bold', fontsize=11)
    line2 = ax2.plot(grid, rois, 's--', color=color_roi, linewidth=2, markersize=5, label='ROI (%)')
    ax2.tick_params(axis='y', labelcolor=color_roi)
    
    # Punto óptimo destacado
    ax1.axvline(t_opt, color='#c0392b', linestyle=':', linewidth=2, label=f'Threshold Óptimo: {t_opt:.2f}')
    ax1.scatter([t_opt], [banca_opt], color='#c0392b', s=150, zorder=5, marker='*')
    
    # Leyendas unificadas
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    
    plt.title(f'Optimización de Regla de Decisión (Capa 1)\nBanca Final y ROI vs. Threshold de EV (Banca Inicial: $1000)', 
              fontsize=13, fontweight='bold', pad=15)
    
    # Cuadro informativo
    textstr = '\n'.join((
        r'$\bf{Óptimo\ Seleccionado:}$',
        f'Threshold: {t_opt:.2f}',
        f'Banca Final: ${banca_opt:.2f}',
        f'ROI Neto: {roi_opt:.2f}%',
        f'Apuestas Realizadas: {bets_opt}'
    ))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax1.text(0.02, 0.95, textstr, transform=ax1.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    g1_path = os.path.join(pres_dir, "48_Simulacion_Banca_y_ROI_vs_Threshold.png")
    plt.savefig(g1_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Gráfico de simulación de thresholds guardado en: {g1_path}")
    
    # -------------------------------------------------------------------------
    # GRÁFICO 2: CURVA DEL THRESHOLD DINÁMICO VS. CUOTAS
    # -------------------------------------------------------------------------
    odds_grid = np.linspace(1.10, 6.00, 100)
    edge_req = 0.05 * np.maximum(1.0, np.sqrt(odds_grid - 1.0))
    
    plt.figure(figsize=(10, 6))
    plt.plot(odds_grid, edge_req * 100, color='#3498db', linewidth=3, label='Filtro Dinámico de EV')
    plt.fill_between(odds_grid, edge_req * 100, alpha=0.15, color='#3498db')
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # Añadir líneas de referencia explicativas
    plt.axhline(5.0, color='gray', linestyle=':', alpha=0.7)
    plt.text(1.2, 5.3, 'Mínimo base de ventaja: 5%', color='gray', fontsize=9, fontweight='bold')
    
    # Destacar algunos puntos específicos
    destacados = [1.50, 2.00, 3.00, 5.00]
    colores_dest = ['#2ecc71', '#f39c12', '#d35400', '#c0392b']
    for idx, odd in enumerate(destacados):
        req = 0.05 * max(1.0, np.sqrt(odd - 1.0))
        plt.scatter([odd], [req * 100], color=colores_dest[idx], s=100, zorder=5)
        plt.text(odd + 0.08, req * 100 - 0.3, f'Cuota {odd:.2f}: {req*100:.1f}% EV', 
                 color=colores_dest[idx], fontweight='bold', fontsize=9.5)
                 
    plt.title('Curva del Threshold Dinámico (Edge Requerido vs. Cuota)\nLa exigencia de ventaja crece con el riesgo de la cuota', 
              fontsize=12, fontweight='bold', pad=15)
    plt.xlabel('Cuota de la Casa de Apuestas (Decimal)', fontweight='bold', labelpad=10)
    plt.ylabel('EV Mínimo Exigido (%)', fontweight='bold', labelpad=10)
    plt.xlim(1.0, 6.2)
    plt.ylim(0, 15)
    plt.legend(loc='lower right')
    plt.tight_layout()
    
    g2_path = os.path.join(pres_dir, "49_Curva_Threshold_Dinamico.png")
    plt.savefig(g2_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Gráfico de curva de threshold dinámico guardado en: {g2_path}")

if __name__ == '__main__':
    main()
