import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression

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

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pres_dir = os.path.abspath(os.path.join(current_dir, "..", "Carpeta_Presentacion"))
    sim_dir = os.path.abspath(os.path.join(current_dir, "..", "Simulacion_Inversion"))
    
    csv_preds = os.path.join(sim_dir, "predicciones_prueba_calibradas.csv")
    csv_master = os.path.join(sim_dir, "historical_with_ou_odds.csv")
    
    if not os.path.exists(csv_preds) or not os.path.exists(csv_master):
        print("❌ Error: Faltan archivos de simulación.")
        return
        
    df_preds = pd.read_csv(csv_preds)
    df_master = pd.read_csv(csv_master)
    df_sim = pd.merge(df_preds, df_master[['game_id', 'home_elo', 'away_elo', 'home_rest', 'away_rest']], on='game_id', how='left')
    df_sim['date'] = pd.to_datetime(df_sim['date'])
    df_sim = df_sim.sort_values('date').reset_index(drop=True)
    
    historical_records = []
    
    for idx, row in df_sim.iterrows():
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
        
        evs = {name: opt['prob'] * opt['odd'] - 1 for name, opt in all_options.items()}
        best_bet_name = max(evs, key=evs.get)
        best_bet = all_options[best_bet_name]
        best_ev = evs[best_bet_name]
        
        # Filtro de EV inicial
        edge_req = 0.05 * max(1.0, np.sqrt(best_bet['odd'] - 1))
        
        if best_ev >= edge_req:
            elo_diff, rest_diff = get_meta_features(row, best_bet_name)
            historical_records.append({
                'prob': best_bet['prob'],
                'odd': best_bet['odd'],
                'ev': best_ev,
                'elo_diff': elo_diff,
                'rest_diff': rest_diff,
                'win': int(best_bet['win'])
            })
            
    meta_df = pd.DataFrame(historical_records)
    print(f"Total registros: {len(meta_df)}")
    
    # Usamos Logistic Regression por su linealidad e interpretabilidad visual
    meta_clf = LogisticRegression(C=0.5, random_state=42)
    X_meta = meta_df[['prob', 'odd', 'ev', 'elo_diff', 'rest_diff']]
    y_meta = meta_df['win']
    meta_clf.fit(X_meta, y_meta)
    
    # Calcular predicciones para pintar los puntos reales
    meta_df['p_win_meta'] = meta_clf.predict_proba(X_meta)[:, 1]
    meta_df['approved'] = (meta_df['p_win_meta'] >= 0.50).astype(int)
    
    # Obtener promedios de las variables que fijaremos
    mean_prob = X_meta['prob'].mean()
    mean_odd = X_meta['odd'].mean()
    mean_elo = X_meta['elo_diff'].mean()
    
    # Generar rejilla en 2D (EV vs rest_diff)
    ev_range = np.linspace(0.04, 0.35, 100)
    rest_range = np.linspace(-6, 6, 100)
    EV, REST = np.meshgrid(ev_range, rest_range)
    
    # Aplanar para predecir
    flat_EV = EV.ravel()
    flat_REST = REST.ravel()
    
    # Crear matriz de entrada fijando prob, odd, elo en sus promedios
    grid_X = pd.DataFrame({
        'prob': np.full_like(flat_EV, mean_prob),
        'odd': np.full_like(flat_EV, mean_odd),
        'ev': flat_EV,
        'elo_diff': np.full_like(flat_EV, mean_elo),
        'rest_diff': flat_REST
    })
    
    grid_probs = meta_clf.predict_proba(grid_X)[:, 1].reshape(EV.shape)
    
    # Graficar
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    
    # Pintar las regiones de decisión
    contour_fill = ax.contourf(EV * 100, REST, grid_probs, levels=[0.0, 0.5, 1.0], alpha=0.15, colors=['#e74c3c', '#2ecc71'])
    
    # Dibujar la línea de la frontera de decisión (P = 0.5)
    boundary = ax.contour(EV * 100, REST, grid_probs, levels=[0.5], colors=['#2c3e50'], linewidths=[2.5], linestyles=['-'])
    
    # Pintar los puntos reales (Aprobados vs Evitados)
    approved_bets = meta_df[meta_df['approved'] == 1]
    avoided_bets = meta_df[meta_df['approved'] == 0]
    
    ax.scatter(avoided_bets['ev'] * 100, avoided_bets['rest_diff'], color='#e74c3c', alpha=0.5, s=25, label='Apuestas Evitadas (Filtro Rojo)', edgecolors='none')
    ax.scatter(approved_bets['ev'] * 100, approved_bets['rest_diff'], color='#2ecc71', alpha=0.6, s=30, label='Apuestas Colocadas (Luz Verde)', edgecolors='none')
    
    # Formatear gráfico
    ax.set_title('Frontera de Decisión Multidimensional del Meta-Modelo (Logistic Regression)\n¿Cómo se comporta el Meta-Modelo como Threshold Inteligente?', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel('Valor Esperado predicho por Capa 1 (EV %)', fontweight='bold', labelpad=10)
    ax.set_ylabel('Diferencia de Descanso en Días (Fatiga)', fontweight='bold', labelpad=10)
    ax.set_xlim(4, 35)
    ax.set_ylim(-6.5, 6.5)
    ax.grid(True, linestyle='--', alpha=0.4)
    
    # Añadir leyenda
    ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    
    # Añadir notas explicativas en el gráfico
    ax.text(20, 4.0, "Zona de Apuestas Aprobadas\n(Alta ventaja deportiva y descanso)", color='#27ae60', fontsize=10, fontweight='bold', ha='center', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='none'))
    ax.text(8.0, -4.5, "Zona de Apuestas Evitadas\n(Fatiga y bajo EV)", color='#c0392b', fontsize=10, fontweight='bold', ha='center', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='none'))
    
    # Explicar la línea de la frontera
    plt.clabel(boundary, inline=True, fmt={0.5: 'Frontera de Aprobación (P=0.50)'}, fontsize=10, colors='black')
    
    plt.tight_layout()
    save_path = os.path.join(pres_dir, "50_Frontera_Decision_Metamodelo.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Gráfico de frontera de decisión guardado en: {save_path}")

if __name__ == '__main__':
    main()
