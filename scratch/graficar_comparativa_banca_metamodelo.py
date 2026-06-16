import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# Agregar la carpeta scratch al path para poder importar
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from comparar_metamodelos import run_simulation_with_clf

def main():
    pres_dir = os.path.abspath(os.path.join(current_dir, "..", "Carpeta_Presentacion"))
    sim_dir = os.path.abspath(os.path.join(current_dir, "..", "Simulacion_Inversion"))
    
    csv_preds = os.path.join(sim_dir, "predicciones_prueba_calibradas.csv")
    csv_master = os.path.join(sim_dir, "historical_with_ou_odds.csv")
    
    if not os.path.exists(csv_preds) or not os.path.exists(csv_master):
        print("❌ Error: Faltan archivos de simulación.")
        return
        
    df_preds = pd.read_csv(csv_preds)
    df_master = pd.read_csv(csv_master)
    df = pd.merge(df_preds, df_master[['game_id', 'home_elo', 'away_elo', 'home_rest', 'away_rest']], on='game_id', how='left')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Grid de thresholds a evaluar
    grid = np.linspace(0.00, 0.20, 11)
    
    bancas_sin_meta = []
    rois_sin_meta = []
    
    bancas_con_meta = []
    rois_con_meta = []
    
    print("Corriendo simulaciones con y sin Meta-Modelo para cada threshold...")
    for t in grid:
        # 1. Sin Meta-Modelo (Línea Base)
        res_base = run_simulation_with_clf(df, mode='dynamic_ev', edge_threshold=t)
        bancas_sin_meta.append(res_base['final_bankroll'])
        rois_sin_meta.append(res_base['roi'])
        
        # 2. Con Meta-Modelo (Logistic Regression)
        res_meta = run_simulation_with_clf(df, mode='dual', model_type='Logistic Regression', edge_threshold=t)
        bancas_con_meta.append(res_meta['final_bankroll'])
        rois_con_meta.append(res_meta['roi'])
        
    bancas_sin_meta = np.array(bancas_sin_meta)
    rois_sin_meta = np.array(rois_sin_meta)
    bancas_con_meta = np.array(bancas_con_meta)
    rois_con_meta = np.array(rois_con_meta)
    
    # Buscar óptimo para el caso CON Meta-Modelo
    idx_opt = np.argmax(bancas_con_meta)
    t_opt = grid[idx_opt]
    banca_opt = bancas_con_meta[idx_opt]
    roi_opt = rois_con_meta[idx_opt]
    
    # Crear gráfico comparativo
    fig, ax1 = plt.subplots(figsize=(12, 7.5), dpi=300)
    
    # Eje 1: Banca Final (USD)
    ax1.set_xlabel('Threshold de Valor Esperado (EV)', fontweight='bold', fontsize=11, labelpad=10)
    ax1.set_ylabel('Banca Final ($)', fontweight='bold', fontsize=11)
    
    # Curva CON Meta-Modelo (Línea verde continua)
    line1 = ax1.plot(grid, bancas_con_meta, 'o-', color='#2ecc71', linewidth=3.0, markersize=7, 
                     label='Sistema Dual (Capa 1 + Meta-Modelo)')
    
    # Curva SIN Meta-Modelo (Línea roja discontinua)
    line2 = ax1.plot(grid, bancas_sin_meta, 'x--', color='#e74c3c', linewidth=2.0, markersize=7, 
                     label='Línea Base (Solo Capa 1)')
    
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.axhline(1000.0, color='gray', linestyle=':', label='Banca Inicial ($1000)')
    
    # Marcar el óptimo destacado de $1,845.69
    ax1.scatter([t_opt], [banca_opt], color='#9b59b6', s=250, zorder=5, marker='*', label=f'Pico Óptimo (Banca: ${banca_opt:.2f})')
    
    # Eje 2: ROI Neto (%)
    ax2 = ax1.twinx()
    ax2.set_ylabel('ROI Neto (%)', fontweight='bold', fontsize=11, labelpad=10)
    
    # Pintamos solo el ROI del sistema dual para no sobrecargar el gráfico
    line_roi = ax2.plot(grid, rois_con_meta, '^:', color='#3498db', linewidth=1.5, markersize=5, 
                        label='ROI Sistema Dual (%)')
    ax2.tick_params(axis='y', labelcolor='#3498db')
    
    # Unificar leyendas
    lines = line1 + line2 + line_roi
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    
    plt.title('Brecha de Rendimiento Económico: Con vs. Sin Meta-Modelo (Capa 2)\nBanca Final y ROI vs. Threshold de EV (Banca Inicial: $1,000 USD)', 
              fontsize=13, fontweight='bold', pad=15)
    
    # Cuadro informativo de la diferencia
    textstr = '\n'.join((
        r'$\bf{Comparativa\ Óptima\ (EV=0.05):}$',
        f'Banca Con Meta: ${banca_opt:.2f}',
        f'Banca Sin Meta: ${bancas_sin_meta[idx_opt]:.2f}',
        f'Ganancia Neta Adicional: ${banca_opt - bancas_sin_meta[idx_opt]:.2f} USD',
        f'ROI Sistema Dual: {roi_opt:.2f}%',
    ))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax1.text(0.02, 0.95, textstr, transform=ax1.transAxes, fontsize=10.5,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    
    # Sobrescribir el gráfico 48 para que muestre la comparativa completa
    g1_path = os.path.join(pres_dir, "48_Simulacion_Banca_y_ROI_vs_Threshold.png")
    plt.savefig(g1_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] Gráfico comparativo de Banca guardado con éxito en: {g1_path}")

if __name__ == '__main__':
    main()
