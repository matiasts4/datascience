import pandas as pd
import numpy as np
import os
import sys

def simulate_chronological(sim_df, market_type, staking_strategy='flat', cal_mode='iso', edge_threshold=0.10):
    bankroll = 1000.0
    bets_count = 0
    wins_count = 0
    wagered = 0.0
    profit = 0.0
    
    bet_returns = []
    
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
        
        if best_ev_info['ev'] >= edge_threshold and bankroll > 0:
            odd = best_ev_info['odd']
            win = best_ev_info['win']
            
            if staking_strategy == 'flat':
                stake = 10.0
            elif staking_strategy == 'quarter':
                f_star = best_ev_info['ev'] / (odd - 1)
                f_star = min(max(0.25 * f_star, 0.0), 0.025)
                stake = f_star * bankroll
                
            if bankroll >= stake and stake > 0.10:
                bets_count += 1
                wagered += stake
                if win:
                    net_profit = stake * (odd - 1)
                    wins_count += 1
                    bet_returns.append(odd - 1)
                else:
                    net_profit = -stake
                    bet_returns.append(-1.0)
                bankroll += net_profit
                profit += net_profit
                
    return bankroll, profit, wagered, bets_count, wins_count, bet_returns

def run_monte_carlo(sim_df, market_type, staking_strategy='flat', cal_mode='iso', edge_threshold=0.10, num_simulations=1000):
    # Primero obtenemos el set de apuestas reales que se realizaron cronológicamente
    # Para la simulación Monte Carlo de permutación, extraeremos las apuestas válidas y barajaremos su orden.
    # Nota: para Kelly, como el stake depende de la banca actual, barajar el orden de los partidos
    # altera dinámicamente la secuencia de stakes y la banca.
    
    # 1. Extraer los datos de las apuestas elegibles
    eligible_bets = []
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
        
        if best_ev_info['ev'] >= edge_threshold:
            eligible_bets.append({
                'ev': best_ev_info['ev'],
                'odd': best_ev_info['odd'],
                'win': best_ev_info['win']
            })
            
    # Si no hay apuestas, retornar vació
    if not eligible_bets:
        return 0.0, 0.0, [1000.0], [0.0]
        
    import random
    
    final_bankrolls = []
    max_drawdowns = []
    ruin_count = 0
    
    # Simular permutaciones aleatorias
    for _ in range(num_simulations):
        # Desordenar la lista de apuestas usando random.shuffle de forma segura en una copia
        shuffled_bets = list(eligible_bets)
        random.shuffle(shuffled_bets)
        
        bankroll = 1000.0
        history = [bankroll]
        
        for bet in shuffled_bets:
            if bankroll < 10.0:  # Umbral de quiebra
                bankroll = 0.0
                history.append(0.0)
                continue
                
            odd = bet['odd']
            win = bet['win']
            ev = bet['ev']
            
            if staking_strategy == 'flat':
                stake = 10.0
            elif staking_strategy == 'quarter':
                f_star = ev / (odd - 1)
                f_star = min(max(0.25 * f_star, 0.0), 0.025)
                stake = f_star * bankroll
                
            if bankroll >= stake and stake > 0.10:
                if win:
                    net_profit = stake * (odd - 1)
                else:
                    net_profit = -stake
                bankroll += net_profit
            history.append(bankroll)
            
        final_bankrolls.append(bankroll)
        if bankroll <= 10.0:
            ruin_count += 1
            
        # Calcular Max Drawdown de esta corrida
        h_arr = np.array(history)
        peaks = np.maximum.accumulate(h_arr)
        peaks = np.where(peaks == 0, 1.0, peaks)
        drawdowns = (peaks - h_arr) / peaks
        max_drawdowns.append(np.max(drawdowns) * 100)
        
    ruin_prob = (ruin_count / num_simulations) * 100
    mean_max_dd = np.mean(max_drawdowns)
    
    return ruin_prob, mean_max_dd, final_bankrolls, max_drawdowns

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "predicciones_prueba_calibradas.csv")
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Calcular cantidad de años en el dataset
    years = (df['date'].max() - df['date'].min()).days / 365.25
    
    scenarios = [
        ('1x2', '1X2 Match Winner', 'flat', 'Flat Stake (1%)', 0.10),
        ('1x2', '1X2 Match Winner', 'quarter', 'Quarter Kelly', 0.10),
        ('portfolio_real', 'Portfolio Real Combinado', 'flat', 'Flat Stake (1%)', 0.10),
        ('portfolio_real', 'Portfolio Real Combinado', 'quarter', 'Quarter Kelly', 0.10)
    ]
    
    print("EJECUTANDO SIMULACIONES MONTE CARLO (1,000 ITERACIONES POR ESCENARIO)...")
    print("=========================================================================\n")
    
    output_rows = []
    
    for m_type, m_name, strat, strat_name, threshold in scenarios:
        print(f"Analizando escenario: {m_name} | {strat_name} | Umbral {threshold:.2f}...")
        
        # 1. Simulación Cronológica Baseline
        bankroll, profit, wagered, bets, wins, bet_returns = simulate_chronological(df, m_type, strat, 'iso', threshold)
        roi = (profit / wagered * 100) if wagered > 0 else 0.0
        
        # 2. Sharpe Ratio de las apuestas
        if len(bet_returns) > 0:
            mean_ret = np.mean(bet_returns)
            std_ret = np.std(bet_returns)
            sharpe_bet = mean_ret / std_ret if std_ret > 0 else 0.0
            
            # Anualizar el Sharpe
            bets_per_year = len(bet_returns) / years
            sharpe_annual = sharpe_bet * np.sqrt(bets_per_year)
        else:
            sharpe_bet = 0.0
            sharpe_annual = 0.0
            
        # 3. Monte Carlo
        ruin_prob, expected_max_dd, final_bankrolls, max_drawdowns = run_monte_carlo(df, m_type, strat, 'iso', threshold, num_simulations=1000)
        
        # 4. Intervalos de confianza del 95% para la banca final
        lower_bank = np.percentile(final_bankrolls, 2.5)
        upper_bank = np.percentile(final_bankrolls, 97.5)
        mean_bank = np.mean(final_bankrolls)
        
        # Intervalo de confianza de 95% para el ROI (especialmente variable en Kelly)
        # Para Flat, el ROI final es siempre el mismo porque sum(win) y sum(lose) es constante independientemente de la permutación,
        # pero bajo Kelly el ROI cambia en cada iteración.
        rois_mc = []
        for fb in final_bankrolls:
            p_mc = fb - 1000.0
            # ROI = (profit / wagered) * 100. Bajo Flat es constante. Bajo Kelly aproximamos:
            rois_mc.append((p_mc / wagered * 100) if wagered > 0 else 0.0)
            
        lower_roi = np.percentile(rois_mc, 2.5)
        upper_roi = np.percentile(rois_mc, 97.5)
        
        output_rows.append({
            'Market': m_name,
            'Staking': strat_name,
            'Bets': bets,
            'Cron_Bankroll': f"${bankroll:.2f}",
            'Cron_ROI': f"{roi:.2f}%",
            'Sharpe_Bet': f"{sharpe_bet:.4f}",
            'Sharpe_Annual': f"{sharpe_annual:.2f}",
            'Ruin_Prob': f"{ruin_prob:.2f}%",
            'MC_Max_DD': f"{expected_max_dd:.2f}%",
            'MC_Bank_CI': f"[${lower_bank:.2f}, ${upper_bank:.2f}]",
            'MC_ROI_CI': f"[{lower_roi:.2f}%, {upper_roi:.2f}%]"
        })
        
    # Crear e imprimir la tabla final en formato Markdown
    markdown_table = []
    markdown_table.append("| Mercado | Gestión de Capital | Apuestas | Banca Cronológica | ROI Cronológico | Sharpe (Bet) | Sharpe (Anual) | Prob. Quiebra (MC) | Max Drawdown Medio (MC) | Intervalo Banca 95% (MC) | Intervalo ROI 95% (MC) |")
    markdown_table.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for r in output_rows:
        markdown_table.append(f"| **{r['Market']}** | {r['Staking']} | {r['Bets']} | {r['Cron_Bankroll']} | {r['Cron_ROI']} | {r['Sharpe_Bet']} | {r['Sharpe_Annual']} | **{r['Ruin_Prob']}** | {r['MC_Max_DD']} | {r['MC_Bank_CI']} | {r['MC_ROI_CI']} |")
        
    print("\nTABLA DE RESULTADOS MONTE CARLO Y SHARPE RATIO:")
    print("==============================================")
    for line in markdown_table:
        print(line)
        
    # Guardar en un archivo de documentación en la carpeta de simulación
    report_file_path = os.path.join(current_dir, "analisis_montecarlo_sharpe.md")
    with open(report_file_path, 'w', encoding='utf-8') as f:
        f.write("# Informe Avanzado: Simulación de Monte Carlo y Sharpe Ratio en Mercados Reales\n\n")
        f.write("Este informe documenta la simulación de Monte Carlo (1,000 iteraciones por escenario) y el análisis de Sharpe Ratio para evaluar la resiliencia y el comportamiento del riesgo de nuestros modelos de Machine Learning (Calibración Isotónica, Umbral óptimo del 10%) en cuotas 100% reales de Bet365.\n\n")
        f.write("## 📊 Resultados de las Simulaciones\n\n")
        for line in markdown_table:
            f.write(line + "\n")
        f.write("\n---\n\n")
        f.write("## 🔬 Glosario y Definición de Métricas para la Defensa de Tesis\n\n")
        f.write("### A. Sharpe Ratio (Bet-by-Bet & Anualizado)\n")
        f.write("El **Sharpe Ratio** mide la rentabilidad ajustada al riesgo. En finanzas, indica cuánta rentabilidad excedente se obtiene por cada unidad de volatilidad.\n")
        f.write("* **Sharpe Ratio por Apuesta ($Sharpe_{\\text{bet}}$):** Se calcula como el valor medio del retorno de las apuestas ($R_i = \\text{Ganancia}/\\text{Stake}$) dividido por su desviación estándar: $SR_{\\text{bet}} = \\frac{\\mu_R}{\\sigma_R}$.\n")
        f.write("* **Sharpe Ratio Anualizado:** Se anualiza multiplicando por la raíz cuadrada del número medio de apuestas colocadas por año: $SR_{\\text{anual}} = SR_{\\text{bet}} \\times \\sqrt{N_{\\text{anual}}}$. Esto permite comparar directamente el portafolio deportivo con activos financieros tradicionales (donde un Sharpe > 1.0 se considera excelente, y > 2.0 es sobresaliente).\n\n")
        f.write("### B. Probabilidad de Quiebra (Ruin Probability)\n")
        f.write("Porcentaje de las 1,000 simulaciones aleatorias de Monte Carlo donde la banca cayó por debajo de **$10 USD** (1% del capital inicial), lo que representa la ruina práctica del inversor.\n\n")
        f.write("### C. Máximo Drawdown Medio (MC Max Drawdown)\n")
        f.write("La caída máxima de capital desde el pico más alto hasta el valle más bajo registrada en promedio a lo largo de las 1,000 simulaciones. Permite entender la racha de pérdidas que el inversor debe tolerar psicológicamente.\n\n")
        f.write("### D. Intervalos de Confianza del 95% (CI)\n")
        f.write("Indica los percentiles $2.5\\%$ y $97.5\\%$ de la banca y del ROI tras simular 1,000 caminos posibles alternativos (permutando aleatoriamente el orden de los partidos). Esto demuestra el rango real de varianza al que está expuesto el capital.\n")
        
    print(f"\n[OK] Informe de Monte Carlo guardado con éxito en: {report_file_path}")
    
    # Copiar a Carpeta_Presentacion para que esté disponible para las diapositivas
    pres_path = os.path.abspath(os.path.join(current_dir, "..", "Carpeta_Presentacion", "analisis_montecarlo_sharpe.md"))
    try:
        import shutil
        shutil.copy(report_file_path, pres_path)
        print(f"[OK] Copiado a la carpeta de presentación: {pres_path}")
    except Exception as e:
        print(f"[Aviso] No se pudo copiar a Carpeta_Presentacion: {e}")

if __name__ == "__main__":
    main()
