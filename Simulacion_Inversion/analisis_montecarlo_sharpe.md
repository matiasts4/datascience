# Informe Avanzado: Simulación de Monte Carlo y Sharpe Ratio en Mercados Reales

Este informe documenta la simulación de Monte Carlo (1,000 iteraciones por escenario) y el análisis de Sharpe Ratio para evaluar la resiliencia y el comportamiento del riesgo de nuestros modelos de Machine Learning (Calibración Isotónica, Umbral óptimo del 10%) en cuotas 100% reales de Bet365.

## 📊 Resultados de las Simulaciones

| Mercado | Gestión de Capital | Apuestas | Banca Cronológica | ROI Cronológico | Sharpe (Bet) | Sharpe (Anual) | Prob. Quiebra (MC) | Max Drawdown Medio (MC) | Intervalo Banca 95% (MC) | Intervalo ROI 95% (MC) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1X2 Match Winner** | Flat Stake (1%) | 1780 | $1001.40 | 0.01% | 0.0000 | 0.00 | **6.10%** | 66.64% | [$0.00, $1001.40] | [-5.62%, 0.01%] |
| **1X2 Match Winner** | Quarter Kelly | 1780 | $87.21 | -2.93% | 0.0000 | 0.00 | **0.40%** | 96.00% | [$87.21, $87.21] | [-2.93%, -2.93%] |
| **Portfolio Real Combinado** | Flat Stake (1%) | 2110 | $829.87 | -0.81% | -0.0043 | -0.08 | **9.00%** | 71.12% | [$0.00, $829.87] | [-4.74%, -0.81%] |
| **Portfolio Real Combinado** | Quarter Kelly | 2110 | $89.71 | -1.73% | -0.0043 | -0.08 | **0.10%** | 96.10% | [$89.71, $89.71] | [-1.73%, -1.73%] |

---

## 🔬 Glosario y Definición de Métricas para la Defensa de Tesis

### A. Sharpe Ratio (Bet-by-Bet & Anualizado)
El **Sharpe Ratio** mide la rentabilidad ajustada al riesgo. En finanzas, indica cuánta rentabilidad excedente se obtiene por cada unidad de volatilidad.
* **Sharpe Ratio por Apuesta ($Sharpe_{\text{bet}}$):** Se calcula como el valor medio del retorno de las apuestas ($R_i = \text{Ganancia}/\text{Stake}$) dividido por su desviación estándar: $SR_{\text{bet}} = \frac{\mu_R}{\sigma_R}$.
* **Sharpe Ratio Anualizado:** Se anualiza multiplicando por la raíz cuadrada del número medio de apuestas colocadas por año: $SR_{\text{anual}} = SR_{\text{bet}} \times \sqrt{N_{\text{anual}}}$. Esto permite comparar directamente el portafolio deportivo con activos financieros tradicionales (donde un Sharpe > 1.0 se considera excelente, y > 2.0 es sobresaliente).

### B. Probabilidad de Quiebra (Ruin Probability)
Porcentaje de las 1,000 simulaciones aleatorias de Monte Carlo donde la banca cayó por debajo de **$10 USD** (1% del capital inicial), lo que representa la ruina práctica del inversor.

### C. Máximo Drawdown Medio (MC Max Drawdown)
La caída máxima de capital desde el pico más alto hasta el valle más bajo registrada en promedio a lo largo de las 1,000 simulaciones. Permite entender la racha de pérdidas que el inversor debe tolerar psicológicamente.

### D. Intervalos de Confianza del 95% (CI)
Indica los percentiles $2.5\%$ y $97.5\%$ de la banca y del ROI tras simular 1,000 caminos posibles alternativos (permutando aleatoriamente el orden de los partidos). Esto demuestra el rango real de varianza al que está expuesto el capital.
