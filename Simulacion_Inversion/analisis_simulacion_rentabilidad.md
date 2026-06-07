# Análisis Científico: Simulación de Rentabilidad Económica e Inversión (1X2)

Este informe documenta el diseño, la ejecución y los hallazgos de la simulación de inversión cronológica realizada sobre el mercado **1X2 (Match Winner)** para verificar la viabilidad económica del proyecto **BetAnalytics**. 

---

## 🎯 1. Contexto Metodológico y Prevención de Leakage

Para garantizar la validez científica y evitar cualquier tipo de **data leakage (fuga de información)**, la simulación se diseñó bajo las siguientes reglas estrictas:
1.  **Datos no vistos:** Se recopilaron únicamente las predicciones realizadas sobre los conjuntos de prueba (*test sets*) de la validación cruzada temporal (`TimeSeriesSplit` con 5 splits). El modelo fue entrenado de forma incremental y evaluado en "el futuro" de cada split.
2.  **Alineación cronológica:** Las predicciones se consolidaron y ordenaron por fecha, simulando la colocación diaria de apuestas en tiempo real sobre una línea temporal real de **2,666 partidos** (excluyendo observaciones con cuotas incompletas).
3.  **Cuotas reales de mercado:** Se utilizaron las cuotas de cierre reales registradas por la casa de apuestas Bet365 (`B365H` para victoria local, `B365D` para empate, `B365A` para victoria visitante).

---

## ⚙️ 2. Especificación Técnica de la Simulación

*   **Mercado evaluado:** **1X2 (Match Winner)** (único mercado con cuotas completas en el dataset histórico).
*   **Modelo de predicción:** **Regresión Logística con Elastic Net** (sintonizado por Optuna).
    *   *Hiperparámetros:* `C: 0.0602`, `l1_ratio: 0.9993`
*   **Técnica de resampling aplicada:** **Tomek Links** (aplicada estrictamente sobre la data de entrenamiento para limpiar fronteras de decisión difusas).
*   **Banca inicial:** \$1,000 USD.
*   **Umbral de ventaja (Edge Threshold):** Se definió un umbral del $5\%$ ($EV \ge 0.05$). Solo se coloca una apuesta en el resultado de un partido si su valor esperado teórico supera el 5%:
    $$EV = p_{\text{modelo}} \cdot \text{Cuota}_{\text{casa}} - 1 \ge 0.05$$
    *Si más de un resultado en un partido supera el umbral, se selecciona el que tenga mayor EV para evitar redundancia.*

---

## 📊 3. Resultados de las Estrategias de Capital

Se evaluaron 5 estrategias clásicas de gestión de riesgo (*staking*):

| Estrategia | Descripción | Banca Final | ROI | Apuestas Colocadas | Tasa de Acierto (Win Rate) | Máximo Drawdown |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Stake Fijo (1%)** | Apostar \$10 USD constantes. | **\$3.60** | -6.58% | 1,515 | 29.90% | 99.70% |
| **Kelly Completo** | Apostar fracción óptima de Kelly (Max 10% del total). | **\$0.91** | -9.91% | 419 | 27.92% | 99.97% |
| **Half Kelly (0.5)** | Apostar 50% de la fracción de Kelly (Max 5% total). | **\$1.92** | -11.94% | 1,131 | 30.24% | 99.90% |
| **Quarter Kelly (0.25)** | Apostar 25% de la fracción de Kelly (Max 2.5% total). | **\$63.52** | -10.64% | 2,020 | 30.59% | 98.42% |
| **Proporcional al Edge** | Apostar fracción proporcional al EV ($0.5 \times EV$, Max 5%). | **\$1.94** | -13.48% | 989 | 29.83% | 99.89% |

*Las bancas finales inferiores a \$10 representan un estado de ruina práctica (bancarrota), donde el capital no es suficiente para colocar una apuesta mínima estandarizada.*

---

## 🔬 4. Análisis Teórico para Defensa de Tesis (¿Por qué se perdió dinero?)

El hecho de que todas las estrategias hayan erosionado el capital hasta la ruina es un **resultado sumamente enriquecedor** desde el punto de vista académico y científico. Provee dos justificaciones teóricas de machine learning críticas para tu presentación:

### A. La Paradoja de la Exactitud (Accuracy vs. Rentabilidad)
Tu modelo ostenta una exactitud del **52.84%** en validación cruzada. Sin embargo, para maximizar el porcentaje de aciertos globales, el clasificador tiende a asignar probabilidades elevadas a los eventos mayoritarios (victorias de equipos muy favoritos de local o visitante), mientras colapsa la clase "Empate" a predicciones casi nulas. 
Cuando el algoritmo de inversión calcula el valor esperado en cuotas decimales:
$$\text{EV} = p \cdot \text{Cuota} - 1$$
El simulador suele encontrar "oportunidades" (EV+) en cuotas altas (empates de 3.60 o visitantes de 5.0) donde el modelo predice una probabilidad moderada (ej. 30%), la cual es ligeramente superior a la implícita en la cuota de la casa (ej. 20%). A pesar de que el modelo detecta teóricamente "valor", en la práctica **la tasa de acierto real de estas apuestas de cuotas altas fue de sólo ~30%**, generando pérdidas acumuladas sistemáticas debido al sesgo de estimación.

### B. El Problema de la Falta de Calibración de Probabilidades
Los clasificadores de machine learning (como la regresión logística o las redes neuronales) se optimizan para definir fronteras de decisión nítidas o minimizar el cross-entropy promedio. Sus puntuaciones de salida (`predict_proba`) **no representan probabilidades calibradas empíricamente**.
*   **Definición de Calibración:** Un modelo está perfectamente calibrado si, de todos los partidos donde predice un $40\%$ de probabilidad de ganar, el equipo gana exactamente el $40\%$ de las veces.
*   **Consecuencia de la No-Calibración:** Si el modelo estima una probabilidad del $40\%$ pero la frecuencia real de éxito en esos escenarios es del $25\%$, las fórmulas como el Criterio de Kelly (que dependen directamente del valor numérico de la probabilidad) sobreestiman drásticamente la ventaja, arriesgando un porcentaje excesivo de la banca en una apuesta con EV real negativo. Esto acelera la trayectoria de la banca hacia \$0 USD.

### C. El Margen Comercial (Overround) de las Casas de Apuestas
Bet365 cobra una comisión implícita en sus cuotas (overround) de aproximadamente el $4\%$ al $6\%$. Para vencer a la varianza y a la comisión en el largo plazo, el modelo no solo debe ser mejor que el azar, sino que sus probabilidades numéricas estimadas deben ser extremadamente exactas y estar perfectamente calibradas.

---

## 💡 5. Propuestas de Trabajo Futuro (Siguientes Pasos Académicos)

Para lograr viabilidad económica en una fase posterior del proyecto, se proponen dos soluciones metodológicas claras:
1.  **Calibración Post-Hoc de los Clasificadores:**
    Aplicar técnicas de calibración como **Regresión Isotónica (Isotonic Regression)** o **Escalado de Platt (Platt Scaling)** sobre las salidas probabilísticas de los modelos entrenados. Esto corregirá la sobreconfianza de las probabilidades numéricas en los extremos.
2.  **Optimización Directa de Métricas de Calibración (Log-Loss):**
    En lugar de sintonizar hiperparámetros maximizando la exactitud (Accuracy) mediante Optuna, re-enfocar la sintonización bayesiana para **minimizar el Log-Loss (entropía cruzada binaria)**, una métrica de error que penaliza severamente las predicciones seguras pero erróneas, obligando al modelo a entregar probabilidades más realistas.

---

*El gráfico de curvas de bankroll que documenta estas trayectorias de simulación está guardado en tu carpeta de diapositivas como:*
👉 [35_Simulacion_Rentabilidad_Apuestas.png](file:///c:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/35_Simulacion_Rentabilidad_Apuestas.png)
