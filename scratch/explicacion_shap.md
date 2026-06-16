# Explicabilidad e Interpretación de los Modelos (Framework SHAP)

Este documento detalla la interpretación global de los modelos de Capa 1 (todos los mercados) y la Capa 2 (Meta-Modelo de decisión) mediante valores SHAP (Shapley Additive exPlanations).

## 1. Gráficos Generados en Carpeta Presentación:

### ── Capa 1: Modelos de Goles y Resultados ──
* **1X2 (Match Winner) - Clase Local:** [shap_capa1_1x2_match_winner.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa1_1x2_match_winner.png)
* **Double Chance 1X (Home or Draw):** [shap_capa1_double_chance_1x.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa1_double_chance_1x.png)
* **Double Chance X2 (Away or Draw):** [shap_capa1_double_chance_x2.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa1_double_chance_x2.png)
* **Over 2.5 Goals:** [shap_capa1_over_2_5_goals.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa1_over_2_5_goals.png)
* **Under 2.5 Goals:** [shap_capa1_under_2_5_goals.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa1_under_2_5_goals.png)
* **BTTS (Both Teams To Score):** [shap_capa1_btts_yes.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa1_btts_yes.png)
* **BTTS - No:** [shap_capa1_btts_no.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa1_btts_no.png)
* **Home Clean Sheet:** [shap_capa1_home_clean_sheet.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa1_home_clean_sheet.png)

### ── Capa 2: Meta-Modelo de Filtro ──
* **Meta-Modelo Random Forest (Decisión):** [shap_capa2_metamodelo.png](file:///C:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/shap_capa2_metamodelo.png)

## 2. Interpretación de Patrones de la Capa 1:
* **Mercados de Goles (Over/Under 2.5):** La variable `h_l5_xg` y `a_l5_xg` son las más relevantes. Goles esperados históricos altos (rojo) empujan la probabilidad del Over hacia la derecha, y viceversa para el Under.
* **Doble Oportunidad y 1X2:** El diferencial de ELO y las cuotas de Bet365 dominan la predicción. Cuotas locales bajas (favoritismo implícito fuerte) empujan la predicción de victoria local positivamente.
* **BTTS y Goles en Contra:** Las métricas de tiros a puerta concedidos y goles concedidos recientes (`h_l5_ga`, `a_l5_ga`) influyen directamente en la predicción del BTTS.
* **Variables Arbitrales:** En todos los mercados, el árbitro (`referee_avg_cards_history`) se encuentra al final de la importancia, indicando nulo o bajísimo impacto en los resultados del partido.

## 3. Interpretación del Meta-Modelo (Filtro Capa 2):
* **Valor Esperado (`ev`):** Es la variable más relevante. Valores de EV altos (rojos) empujan la decisión del Meta-Modelo a aprobar la apuesta.
* **Fatiga (`rest_diff`):** Cuando el diferencial de descanso del equipo candidato es muy desfavorable (puntos azules en valores negativos), la probabilidad de acierto cae significativamente, y el Meta-Modelo bloquea la apuesta.
* **Cuota (`odd`):** Funciona como regulador de riesgo. Cuotas muy altas se asocian con mayor tasa de error, provocando una penalización preventiva del modelo.
