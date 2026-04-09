# Plan Integral para la Mejora de Modelos Predictivos (Apuestas Deportivas)

Este documento detalla la ruta crítica (Roadmap) para evolucionar el sistema predictivo actual de la Premier League desde un modelo predictivo estándar a un sistema de apuestas de grado profesional y cuantitativo.

---

## 1. Ingeniería de Datos Avanzada (Feature Engineering)
El mayor salto de calidad en cualquier modelo predictivo deportivo no proviene del algoritmo, sino de la calidad de los datos.

*   **Métricas Subyacentes (Expected Metrics):** Incluir **xG**, **xGA**, y **xPTS**.
*   **Impacto de Jugadores (Player Ratings & Lineups):** Crear un "Índice de Fuerza del XI Inicial".
*   **Contexto y Fatiga:** Calcular días exactos de descanso, kilómetros viajados e "Índice de Motivación".
*   **Cuotas y Líneas de Cierre Reales (CLV):** Integrar cuotas de cierre históricas de casas *sharp* (como Pinnacle o casas Asiáticas) en lugar de usar cuotas simuladas teóricas.

---

## Roadmap de Ejecución y Progreso

### Fase 1 (Corto Plazo - 2 a 3 Semanas) ✅ COMPLETADA
**Objetivo:** Datos avanzados y Calibración inicial.

- [x] **1.1. Obtener Histórico de xG y Métricas Avanzadas:** Descarga de Understat mediante `understat_scraper.py`.
  - *Progreso:* API interna de Understat descubierta (`/getLeagueData/EPL/{year}` + header `x-requested-with`). Se descargaron 3,040 partidos (temporadas 2017/18–2024/25) guardados en `data/historical/understat_xg.csv`. Integrados al dataset mediante `merge_xg.py` con un 85.8% de match rate, generando `all_match_features_v4_xg.csv`.
- [x] **1.2. Descargar Histórico de Cuotas Reales (Pinnacle/Betfair):** Evaluar correctamente la rentabilidad histórica.
  - *Progreso:* Descarga mediante `download_historical_odds.py` finalizada. Se generó y fusionó en `data/historical/all_match_features_v3_odds.csv` → base para V4.
- [x] **1.3. Aplicar Brier Score (Base):** Calibración inicial **antes** de los cambios.
  - *Resultados PRE-FASE 1 (17 features, V2 dataset):*
    - Avg Accuracy: **56.3%** | Brier Over 2.5: **0.2440** | Brier BTTS: **0.2453**
- [x] **1.4. Re-entrenamiento y Validación Final (Fase 1):**
  - Nuevas features añadidas: `home_xg`, `away_xg` (total: 19 features). Dataset: `all_match_features_v4_xg.csv`.
  - *Resultados POST-FASE 1 (19 features, V4 dataset):*
    - Avg Accuracy: **66.1%** (+9.8%) | Brier Over 2.5: **0.2056** (-15.7%) | Brier BTTS: **0.2106** (-14.2%)
    - 1X2 Accuracy: **61.0%** | Over 2.5 Accuracy: **68.6%** | BTTS Accuracy: **68.6%**

### ✅ Fase 1 Lograda — Mejora validada por comparación directa Antes/Después.

---

### Fase 2 (Medio Plazo - 1 a 2 Meses)
**Objetivo:** Gestión de Riesgo y Modelos de Distribución.

- [ ] **2.1. Gestión de Bankroll:** Reescribir el simulador para usar Fractional Kelly dinámico.
- [ ] **2.2. Mercados Ineficientes:** Moverse hacia Asian Handicaps en lugar de mercados altamente eficientes.
- [ ] **2.3. Modelos Dixon-Coles/Poisson:** Desarrollo y entrenamiento para distribuciones de goles cruzadas entre mercados.

### Fase 3 (Largo Plazo)
**Objetivo:** Modelamiento de XI Iniciales.

- [ ] **3.1. Scraping de Alineaciones en Tiempo Real:** Obtener el Starting XI automatizado (ej. WhoScored o similares) una hora antes del partido para modificar características temporalmente.

---
*Progreso actualizado 2026-03-27 por el Asistente AI.*
