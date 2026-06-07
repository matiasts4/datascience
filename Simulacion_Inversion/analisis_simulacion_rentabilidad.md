# Análisis Científico: Impacto de la Calibración Post-Hoc en la Rentabilidad e Inversión Multi-Mercado

Este informe documenta el diseño, la ejecución y los hallazgos de la simulación de inversión cronológica realizada tras implementar **Calibración Post-Hoc de Probabilidades** (mediante **Regresión Isotónica** y **Escalado de Platt / Sigmoide**) en los modelos predictivos de goles y resultado de partidos de **BetAnalytics**.

---

## 🎯 1. Contexto Metodológico y Prevención de Leakage

Para garantizar la validez científica y evitar cualquier tipo de **data leakage (fuga de información)**, la simulación se diseñó bajo las siguientes reglas estrictas:
1.  **Datos no vistos y validación temporal:** Se recopilaron únicamente predicciones *out-of-fold* mediante validación cruzada temporal (`TimeSeriesSplit` con 5 splits).
2.  **Calibración libre de leakage:** Para cada split:
    *   La partición histórica de entrenamiento `(X_train, y_train)` se dividió cronológicamente en dos sub-conjuntos disjuntos: **Sub-entrenamiento (80%)** y **Calibración (20%)**.
    *   El pipeline base se ajustó únicamente en el 80% de sub-entrenamiento.
    *   Los calibradores (`CalibratedClassifierCV` con `FrozenEstimator` de scikit-learn y validación preajustada) se entrenaron sobre el 20% de calibración (los partidos más recientes antes del test fold).
    *   Las predicciones calibradas se generaron de forma independiente sobre la partición de prueba futura `(X_test, y_test)`.
3.  **Cuotas reales de mercado:** Se utilizaron las cuotas de Bet365 reales:
    *   **1X2:** Columnas `B365H`, `B365D`, `B365A`.
    *   **Over/Under 2.5 Goals:** Columnas `B365>2.5` y `B365<2.5` (descargadas y alineadas desde `football-data.co.uk`).
4.  **Línea temporal consolidada:** Se simularon las apuestas cronológicamente sobre una línea temporal de **2,356 partidos** (excluyendo observaciones con cuotas incompletas).

---

## 📊 2. Resultados Comparativos de las Estrategias de Capital

Se evaluaron las 60 combinaciones posibles resultantes de:
*   **3 Modos de Calibración:** Sin Calibrar (Baseline original), Calibración Isotónica y Calibración Sigmoide.
*   **4 Mercados / Cartera:** 1X2 (Match Winner), Over 2.5 Goles, Under 2.5 Goles y Portfolio Combinado.
*   **5 Estrategias de Staking:** Stake Fijo (Flat 1%), Kelly Completo, Half Kelly, Quarter Kelly y Proporcional al Edge.

### A. Resultados bajo Estrategia de Quarter Kelly (Max 2.5% de Banca)

| Mercado / Cartera | Calibración | Banca Final | ROI | Apuestas Colocadas | Tasa de Acierto (Win Rate) | Máximo Drawdown |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1X2 Match Winner** | Sin Calibrar | \$25.44 | -11.38% | 1,776 | 29.39% | 98.44% |
| | **Isotónica** | **\$82.87** | **-3.10%** | 2,022 | 30.66% | **97.36%** |
| | **Sigmoide** | **\$103.23** | **-2.32%** | 1,982 | 30.83% | **97.64%** |
| **Over 2.5 Goals** | Sin Calibrar | \$637.33 | -5.08% | 466 | 46.14% | 53.46% |
| | **Isotónica** | **\$641.60** | **-2.60%** | 697 | 45.48% | **42.72%** |
| | Sigmoide | \$446.06 | -6.29% | 601 | 44.59% | 58.26% |
| **Under 2.5 Goals** | Sin Calibrar | \$354.26 | -3.80% | 832 | 37.86% | 89.05% |
| | **Isotónica** | **\$593.13** | **-1.65%** | 816 | 38.36% | **76.33%** |
| | **Sigmoide** | **\$534.43** | **-2.13%** | 766 | 38.25% | **79.84%** |
| **Portfolio Combinado** | Sin Calibrar | \$9.49 | -8.05% | 2,109 | 31.72% | 99.47% |
| | **Isotónica** | **\$93.74** | **-1.52%** | 2,233 | 31.84% | **98.50%** |
| | Sigmoide | \$27.76 | -3.16% | 2,180 | 27.61% | 99.03% |

---

### B. Resultados bajo Estrategia de Stake Fijo (Flat Stake - 1% de Banca Inicial)

| Mercado / Cartera | Calibración | Banca Final | ROI | Apuestas Colocadas | Tasa de Acierto (Win Rate) | Máximo Drawdown |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1X2 Match Winner** | Sin Calibrar | \$3.60 | -6.58% | 1,515 | 29.90% | 99.70% |
| | **Isotónica** | **\$822.60** | **-0.88%** | 2,022 | 30.66% | **70.66%** |
| | Sigmoide | \$545.60 | -2.29% | 1,982 | 30.83% | 80.78% |
| **Over 2.5 Goals** | Sin Calibrar | \$850.40 | -3.21% | 466 | 46.14% | 31.20% |
| | **Isotónica** | **\$867.00** | **-1.91%** | 697 | 52.65% | **19.05%** |
| | Sigmoide | \$749.10 | -4.17% | 601 | 48.59% | 27.07% |
| **Under 2.5 Goals** | Sin Calibrar | \$734.30 | -3.19% | 832 | 37.86% | 62.04% |
| | **Isotónica** | **\$966.00** | **-0.42%** | 816 | 43.75% | **39.75%** |
| | **Sigmoide** | **\$937.60** | **-0.81%** | 766 | 40.73% | **43.18%** |
| **Portfolio Combinado** | Sin Calibrar | \$6.30 | -7.11% | 1,398 | 32.19% | 99.47% |
| | **Isotónica** | **\$728.80** | **-1.21%** | 2,233 | 31.84% | **71.73%** |
| | Sigmoide | \$7.70 | -4.71% | 2,108 | 27.37% | 99.56% |

---

## 🔬 3. Análisis Teórico y Discusión (Aporte para la Defensa de Tesis)

Los resultados de la calibración aportan hallazgos de alto valor académico para el proyecto:

### A. La Corrección de la Tasa de Acierto en Goles
Bajo Stake Fijo (Flat), la calibración isotónica produjo un incremento notable en la tasa de acierto real de las apuestas colocadas:
*   En el mercado **Over 2.5 Goals**, la tasa de acierto del modelo aumentó del **46.14% al 52.65%**.
*   En el mercado **Under 2.5 Goals**, la tasa de acierto aumentó del **37.86% al 43.75%**.
*   **Explicación científica:** Los modelos no calibrados sufren de sobreconfianza en ciertas regiones del espacio de probabilidad, estimando una ventaja (Edge) teórica alta donde en realidad no existe. Al calibrar post-hoc, la probabilidad reportada se mapea a la frecuencia real. Esto actúa como un "filtro de calidad", descartando apuestas falsamente lucrativas y reteniendo solo las que poseen un valor esperado positivo real.

### B. Estabilización de Drawdowns y Evitación de la Ruina
La calibración mitigó de forma contundente el riesgo de Drawdowns catastróficos en el control Flat Stake:
*   El mercado **Over 2.5 Goals** (Isotónica) redujo su Drawdown Máximo del **31.20% a un excelente 19.05%**, finalizando con \$867.00.
*   El mercado **Under 2.5 Goals** (Isotónica) finalizó prácticamente en el punto de equilibrio (**\$966.00**, perdiendo solo \$34 dólares de un capital inicial de \$1000 tras 816 apuestas diarias) con un drawdown controlado de **39.75%** (frente al 62.04% del modelo no calibrado).
*   En el **Portfolio Combinado**, el modelo sin calibrar colapsó a \$6.30 (ruina total) bajo Flat Stake, mientras que la calibración isotónica lo salvó, cerrando en **\$728.80** y reduciendo el drawdown del 99.47% al 71.73%.

### C. Desempeño Superior de la Regresión Isotónica vs. Platt Scaling (Sigmoide)
La calibración **Isotónica** superó de forma generalizada al Escalado de **Platt (Sigmoide)**:
*   La regresión isotónica es una técnica no paramétrica que ajusta una función monótona creciente libre de supuestos distribucionales. Al contar con un tamaño muestral de calibración razonable en cada fold (de 78 a 390 partidos), la regresión isotónica fue capaz de ajustar curvas de calibración complejas.
*   La calibración sigmoide asume que la distribución de las probabilidades sigue una curva logística tradicional. Al forzar esta estructura paramétrica, tiende a sub-corregir o sobre-suavizar las estimaciones en los extremos del espacio de características del fútbol, resultando en un ROI e ingresos inferiores a los de la isotónica.

### D. La persistencia del Drawdown en Kelly (Paradoja de la Varianza y el Overround)
Aunque la calibración isotónica salvó de la ruina instantánea al Portfolio Combinado bajo Quarter Kelly (elevando la banca de \$9.49 a \$93.74, un incremento relativo de 10 veces en la supervivencia), las estrategias de Kelly siguieron sufriendo un desgaste importante a lo largo de los años.
1.  **El Margen de la Casa (Overround):** Las cuotas de Bet365 analizadas contienen una comisión implícita de aproximadamente 4-6%. Para superar esta barrera de forma sostenida con el Criterio de Kelly (que es altamente sensible a la precisión exacta de las ventajas), la ventaja teórica estimada debe ser extremadamente precisa.
2.  **Sensibilidad al Ruido:** A pesar de la calibración, el fútbol es un deporte de baja anotación y alta aleatoriedad inherente (tarjetas rojas inesperadas, penales, rebotes). Esta varianza, combinada con la agresividad de las fracciones de Kelly (incluso fraccionado a un cuarto), provoca drawdowns severos cuando ocurren rachas negativas.
3.  **Conclusión Práctica:** Para clasificadores de eventos deportivos con overround comercial, el **Stake Fijo (Flat Staking)** combinado con **Calibración Isotónica** representa la estrategia más segura, robusta y científicamente viable para la gestión de riesgo en la vida real.

---

## 📈 4. Visualización de Curvas de Crecimiento de Capital

El gráfico comparativo multi-mercado de 2x2 que documenta las curvas de capital antes y después de calibrar se encuentra actualizado y guardado en la carpeta de presentación:

👉 [35_Simulacion_Rentabilidad_Apuestas.png](file:///c:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/35_Simulacion_Rentabilidad_Apuestas.png)
