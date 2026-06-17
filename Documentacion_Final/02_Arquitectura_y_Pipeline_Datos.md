# 02 — Arquitectura del Sistema y Pipeline de Datos

---

# Parte A — Arquitectura técnica

## A.1 Diagrama de flujo

```
FBRef → all_match_features_v4_xg → sanitizer_pipeline → historical_sanitized_v8
    ↓
CAPA 1: 8 modelos ML (27 features, sin cuotas en train) → prob raw
    ↓
CAPA 2: Calibración isotónica → prob calibrada p̂
    ↓
CAPA 3: Filtro EV dinámico → edge_req = 0.05 × max(1, √(cuota−1))
    ↓
META-LABELING: RandomForest(max_depth=3) walk-forward → ejecutar / filtrar
```

## A.2 Responsabilidad por capa

| Capa | Pregunta | Impacto clave |
|------|----------|---------------|
| **1 — Predicción** | ¿Qué probabilidad tiene el evento? | Accuracy CV 52.8%–71.0%; AUC ~0.52–0.55 |
| **2 — Calibración** | ¿Las probs son honestas? | Portfolio 8 mkts: $8.77 → $1.334 (+1.44% ROI) |
| **3 — EV dinámico** | ¿El edge justifica la cuota? | Real: −1.85% → −1.65% ROI |
| **Meta-Labeling** | ¿Apostamos esta candidata? | **−1.85% → +9.96% ROI**; DD 77% → 19% |

## A.3 Fórmulas clave

**Valor esperado:** $EV = \hat{p} \times c - 1$

**Edge dinámico:** $\text{edge\_req}(c) = 0.05 \times \max(1,\ \sqrt{c-1})$

## A.4 Scripts por capa

| Capa | Scripts |
|------|---------|
| Datos | `sanitizer_pipeline.py` |
| Capa 1 | `aplicar_hiperparametros.py`, `evaluar_modelos_optimos.py` |
| Capa 2–3 | `Simulacion_Inversion/simular_estrategias_apuestas.py` |
| Meta | `Simulacion_Inversion/simular_meta_decision.py`, `scratch/comparar_metamodelos.py` |
| Live | `archive/pl-predictor/src/models/selector.py` |

**Artefactos serializados:** `archive/pl-predictor/models/model_*.pkl`, `optimized_hyperparams.json`

---

# Parte B — Visión general del pipeline de datos

## B.1 Flujo ETL completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│ EXTRACCIÓN (Obtain)                                                     │
│   FBRef vía soccerdata + Selenium → CSV por temporada                   │
│   archive/pl-scraper/data/processed/{2017…2025}/                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ TRANSFORMACIÓN / UNIFICACIÓN                                            │
│   Agregación de features (Elo, L5, xG, cuotas, árbitro, descanso…)      │
│   → all_match_features_v4_xg.csv  (3.420 filas, RAW — no entrenar)      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ LIMPIEZA (Scrub) — sanitizer_pipeline.py + sanitizacion.md              │
│   Drop leakage · multicol · varianza cero · EWMA xG · integridad IDs    │
│   → historical_sanitized_v8.csv  (limpio, sin escalar globalmente)      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ MODELADO (Explore / Model) — train_models.py / aplicar_hiperparametros  │
│   KNNImputer + PowerTransformer/StandardScaler DENTRO del Pipeline CV   │
└─────────────────────────────────────────────────────────────────────────┘
```

## B.2 Datasets clave

| Dataset | Ruta | Filas | Estado | Uso |
|---------|------|-------|--------|-----|
| **RAW maestro** | `all_match_features_v4_xg.csv` | 3.420 | Materia prima con leakage | Solo input del sanitizador |
| **Sanitizado v8** | `historical_sanitized_v8.csv` | 3.420 | Limpio, nulos permitidos | Input oficial de ML |
| **Train efectivo** | Subconjunto `result_1x2` no nulo | ~3.389 | Partidos ya jugados | Entrenamiento / CV |
| **Fixtures futuros** | `game_id == '0'` o targets nulos | ~31 | Calendario sin resultado | Inferencia upcoming |

**Principio rector:** el dataset v8 se exporta *crudo pero limpio* — sin imputación ni escalado global. Las transformaciones numéricas se aprenden **solo dentro del fold de entrenamiento** del `sklearn.pipeline.Pipeline`.

---

# Parte C — Extracción: scraping FBRef

## C.1 Módulo y fuente

| Elemento | Detalle |
|----------|---------|
| **Carpeta** | `archive/pl-scraper/` |
| **Fuente web** | [FBRef](https://fbref.com) — estadísticas públicas Premier League |
| **Cliente** | `scraper/fbref_client.py` (wrapper sobre `soccerdata`) |
| **Orquestador** | `pipeline.py` · `run_all_seasons.py` |
| **Resiliencia** | `checkpoint/manager.py` + JSON por temporada (`checkpoint_2017.json`, …) |
| **Rate limit** | Pausa configurable entre requests (`config.py` → `RATE_LIMIT_SECONDS`) |

## C.2 Fases del scraper por temporada

El pipeline ejecuta **tres fases secuenciales** con reanudación por checkpoint:

| Fase | Acción | Output |
|------|--------|--------|
| **1 — Schedule** | Calendario completo de la temporada | `matches.csv` (~380 filas × 16 cols) |
| **2 — Por partido** | Alineaciones, eventos minuto a minuto | `lineups.csv`, `match_events.csv` |
| **3 — Stats jugadores** | Resumen y porteros | `player_stats_summary.csv`, `player_stats_keepers.csv` |

Cada fase marca progreso en el checkpoint; si el proceso se interrumpe, retoma desde el último `game_id` pendiente.

## C.3 Archivos garantizados por temporada

Bajo `archive/pl-scraper/data/processed/{season}/`:

| Archivo | Contenido aproximado | Uso downstream |
|---------|---------------------|----------------|
| `matches.csv` | 380 partidos · fecha, equipos, marcador, xG, cuotas | Tabla maestra de unificación |
| `lineups.csv` | 13k–30k filas (crece post-COVID por bancos ampliados) | Contexto plantillas |
| `match_events.csv` | 4k–11k eventos (goles, tarjetas, cambios) | Reconstrucción cronológica |
| `player_stats_summary.csv` | ~10k filas · pases, goles, minutos | Agregados por jugador |
| `player_stats_keepers.csv` | ~760 filas · 2 porteros × 380 partidos | Métricas de arco |

## C.4 Temporadas cubiertas y correcciones de extracción

| Temporada | Estado | Notas |
|-----------|--------|-------|
| 2017–2024 | Completas | Datos validados en `DATA_DICTIONARY.md` |
| 2021/22 | Corregida | Carpeta legacy `2122` tenía **760 filas duplicadas**; normalizada a 380 partidos únicos |
| 2025/26 | Parcial / en curso | Incluye fixtures futuros (`game_id == '0'`) |

### Limitación conocida: shot events

FBRef cambió la estructura de tablas avanzadas de tiros. El módulo `soccerdata` devuelve **datos vacíos** para `shot_events`. El pipeline **no depende** de ese archivo; las features de tiros provienen de agregados ya presentes en `matches.csv` y stats de jugadores.

## C.5 Errores corregidos en la capa extractiva

| Problema | Impacto | Corrección |
|----------|---------|------------|
| Temporada 2122 duplicada | Doble conteo en unificación, llaves repetidas | Deduplicación a 380 partidos |
| Checkpoints inconsistentes | Re-scrapeo innecesario o saltos | Migración a `CheckpointManager` unificado |
| Rate limiting / bloqueos | Pérdida de filas parciales | Reintentos por partido + logs por temporada (`logs/scraper_{season}.log`) |
| Shots vacíos | Pipeline colgado esperando archivo inexistente | Flag `shots_done` omitido; módulo deshabilitado |

---

# Parte D — Unificación al maestro `all_match_features_v4_xg`

## D.1 Evolución de versiones

El dataset maestro pasó por iteraciones sucesivas (`v2` → unificación con Kaggle 2024/25 → `v4_xg`). La versión **v4_xg** es la materia prima definitiva porque incorpora:

- **Expected Goals (xG)** por equipo por partido
- **Ratings Elo** dinámicos (`home_elo`, `away_elo`)
- **Forma Last-5** (puntos, tiros, goles, faltas, conversión)
- **Contexto** (`home_rest`, `away_rest`, `is_derby`, `relegation_pressure`)
- **Árbitro** agregado (`referee_avg_cards_history`)
- **Cuotas** Bet365 y Pinnacle históricas
- **Targets derivados** (`result_1x2`, `btts`, `total_goals`, etc.)

## D.2 Reglas de unificación

| Regla | Motivo |
|-------|--------|
| Orden cronológico estricto por `date` | Series temporales; features L5 y Elo dependen del pasado |
| Continuidad Elo entre temporadas | El rating de cierre de 2023/24 alimenta el inicio de 2024/25 |
| Cero pérdida de columnas al merge | Columnas ausentes en subset reciente → `NaN` explícito |
| Fixtures futuros conservados | Permiten predicción upcoming con `result_1x2` nulo |

## D.3 Por qué v4_xg no es entrenable directamente

Contiene simultáneamente:

1. **Variables post-partido** (`score`, `total_cards`, faltas del encuentro) → leakage.
2. **Cuotas duplicadas** (Bet365 + Pinnacle, $r \approx 0.99$) → multicolinealidad extrema.
3. **Columnas constantes** (`league` = "Premier League" siempre) → varianza cero.
4. **Identificadores de alta cardinalidad** sin transformar (`home_team`, `referee`) → riesgo de overfitting.
5. **Asimetrías severas** y outliers genuinos sin transformar → gradientes inestables.

Por eso existe la capa intermedia `sanitizer_pipeline.py`.

---

# Parte E — Metodología formal: checklist OSSEMN

La limpieza sigue el checklist de `sanitizacion.md`, alineado con el marco **OSSEMN**:

| Fase OSSEMN | Checklist `sanitizacion.md` | Implementación en el proyecto |
|-------------|----------------------------|-------------------------------|
| **Obtain** | — | Scraping FBRef (Parte C) |
| **Scrub** | §1 EDA · §2 incorrectos · §3 inútiles · §4 missing · §5 outliers · §6 distribución · §7 feature eng. | `sanitizer_pipeline.py` + Pipeline sklearn |
| **Explore** | §1 correlaciones, Chi-cuadrado, K-S | `run_eda.py`, gráficos `Carpeta_Presentacion/1_*`–`5_*` |
| **Model** | §7 normalización dentro del split | `train_models.py`, `aplicar_hiperparametros.py` |
| **iNterpret** | — | SHAP (`scratch/generar_shap.py`) |

Documentación de apoyo detallada (fuera de esta carpeta, referenciada):

- `Carpeta_Presentacion/17_Tratamiento_Problemas_Datos.md` — justificación metodológica por problema
- `Carpeta_Presentacion/18_Auditoria_Calidad_Datos.md` — auditoría de nulos y test K-S post-imputación

---

# Parte F — `sanitizer_pipeline.py`: seis fases y correcciones

Script: `sanitizer_pipeline.py` · Input: `all_match_features_v4_xg.csv` · Output: `historical_sanitized_v8.csv`

## F.1 Fase 1 — Carga e integridad de identificadores

```python
df['game_id'] = df['game_id'].astype(str)
df['game_id'] = df['game_id'].apply(lambda x: x[:-2] if str(x).endswith('.0') else str(x))
```

| Corrección | Problema | Impacto si no se corrige |
|------------|----------|--------------------------|
| **`game_id` → string** | Pandas lee `"0"` como `0.0` float | Fixtures futuros indistinguibles de IDs válidos |
| Sufijo `.0` eliminado | Conversión float→string deja `"12345.0"` | Joins y filtros fallan en producción |

## F.2 Fase 2 — Depuración estructural (varianza cero, MCAR, formato)

| Acción | Columnas / registros | Tipo de problema |
|--------|---------------------|------------------|
| Drop columnas | `league`, `notes`, `match_report` | Varianza cero / ruido / URLs únicas |
| Drop 1 fila | `attendance` nulo | MCAR — único registro faltante |
| Parse datetime | `date` → `month`, `day_of_week` | Formato inconsistente |
| Drop columnas | `referee` (nombre crudo), `time` | Alta cardinalidad / ruido OOR |

## F.3 Fase 3 — Leakage y multicolinealidad

**Leakage eliminado** (información post-silbato inicial):

| Columna | Por qué es fuga |
|---------|-----------------|
| `score` | Marcador final |
| `home_match_fouls`, `away_match_fouls` | Faltas del partido en curso |
| `total_cards` | Tarjetas finales del encuentro |

**Multicolinealidad resuelta por eliminación:**

| Eliminadas | Conservadas | Correlación |
|------------|-------------|-------------|
| `PSH`, `PSD`, `PSA` (Pinnacle) | `B365H`, `B365D`, `B365A` (Bet365) | $r \approx 0.99$ |

> Bet365 se conserva en el CSV para **simulación financiera**, pero queda **excluida** de `FEATURES` en `config.py` durante entrenamiento.

**Targets aislados:** `home_goals`, `away_goals`, `total_goals`, `btts`, `result_1x2` se extraen a `targets_df` y **nunca se imputan ni transforman**.

## F.4 Fase 4 — Feature engineering: EWMA xG Last-5

Se reconstruye historial por equipo (vista local + visitante apilada), orden cronológico, y se calcula:

$$\text{EWMA}_t = \text{EWM}(\text{xG}, \text{span}=5, \text{shift}(1))$$

| Feature nueva | Significado |
|---------------|-------------|
| `h_l5_xg`, `h_l5_xga` | xG a favor/en contra — media móvil local (sin incluir partido actual) |
| `a_l5_xg`, `a_l5_xga` | Idem visitante |

- `shift(1)` garantiza que **no hay leakage temporal** dentro del partido.
- NaN en primeros partidos de temporada → imputados en entrenamiento (MAR), no en export.

## F.5 Fase 5 — Ensamblado y exportación

Se concatenan metadatos (`game_id`, `date`, equipos, `venue`), targets y features pulidos. **Sin** `StandardScaler`, **sin** `KNNImputer` global.

## F.6 Fase 6 — Validación post-export

| Check | Resultado esperado |
|-------|-------------------|
| Shape | 3.420 × ~51 columnas |
| `game_id` tipo string | `"0"` identifica fixtures |
| Nulos en Elo, rest, derby | 0% |
| Nulos en xG / L5 / cuotas | Presentes (MAR) — OK |

---

# Parte G — Nueve problemas de calidad y su tratamiento

Resumen metodológico (detalle en `17_Tratamiento_Problemas_Datos.md`):

## G.1 Varianza cero

Columnas constantes (`league`) o casi constantes (`notes` ≈ "0" al 99.97%) → **eliminación física**.

## G.2 Outliers deportivos — conservación deliberada

En fútbol de élite, valores extremos (xG = 6.67, Elo > 1800) son **señal real**, no ruido.

| Decisión | Alternativa descartada | Motivo |
|----------|------------------------|--------|
| **Conservar** filas | IQR / Isolation Forest | Perdería patrones de equipos dominantes |
| **Yeo-Johnson** + StandardScaler | MinMaxScaler | MinMax comprime el 99% de datos si hay un outlier extremo |
| No eliminar | Winsorización | Distorsiona probabilidades de cola |

## G.3 Asimetría (skewed features)

Variables con cola larga: cuotas Bet365, `referee_avg_cards_history`, `h_l5_xg`, faltas L5.

- **Yeo-Johnson** preferido sobre Box-Cox porque acepta **ceros** (xG = 0, tarjetas = 0).
- Aplicado dentro de `ColumnTransformer` en entrenamiento, no en export v8.

## G.4 Multicolinealidad

| Tipo | Ejemplo | Solución |
|------|---------|----------|
| **Datos** | Pinnacle vs Bet365 | Drop Pinnacle (`sanitizer_pipeline.py`) |
| **Estructural** | Interacciones / escalas distintas | Centrado vía `StandardScaler` |
| **Residual en árboles** | Tiros vs tiros al arco | **Elastic Net** penaliza redundancia en LogReg |

## G.5 Leakage

Ver Parte J. Incluye fugas post-partido, cuotas en train, escalado global y CV aleatoria.

## G.6 Variables categóricas → cuantitativas

| Original | Transformación | Evita |
|----------|----------------|-------|
| `home_team`, `away_team` | `home_elo`, `away_elo` | One-Hot de 40+ columnas |
| `referee` | `referee_avg_cards_history` | Alta cardinalidad sin señal estable |
| `venue` | Implícito en split `home_*` / `away_*` | Redundancia |
| `is_derby` | Binario nativo (0/1) | — |

## G.7 Construcción de targets (8 mercados)

Targets derivados de goles reales. **~3.389 partidos etiquetados** tras excluir fixtures futuros. Desbalance moderado (ej. HCS 70/30) — **sin SMOTE** para preservar calibración de probabilidades.

## G.8 Feature engineering ad-hoc ("sea su propio jefe")

| Feature | Lógica de dominio |
|---------|-------------------|
| EWMA L5 xG | Racha reciente ponderada |
| `home_rest`, `away_rest` | Fatiga — días desde último partido |
| `relegation_pressure` | Proximidad matemática a zona de descenso |
| L5 pts/sh/sot/gf/ga/fls/conv | Forma ofensiva/defensiva rolling |

## G.9 Matriz resumen: columna → problema → tratamiento

| Problema | Variable(s) | Tratamiento | Dónde |
|----------|-------------|-------------|-------|
| Varianza cero | `league`, `notes`, `match_report` | Drop | `sanitizer_pipeline.py` L31 |
| Leakage | `score`, fouls, `total_cards` | Drop | L56–57 |
| Multicol | `PSH/D/A` | Drop (conservar B365) | L59–61 |
| MCAR | `attendance` (1 fila) | Drop fila | L35–36 |
| Formato | `game_id` | String + fix `.0` | L23–27 |
| MAR | xG, L5, B365 | KNN k=5 en CV | `train_models.py` |
| MNAR | targets futuros | Filtro `game_id != '0'` | Entrenamiento |
| Outliers | xG, Elo | Conservar + Yeo-Johnson | Pipeline sklearn |
| Skew | cuotas, tarjetas | PowerTransformer | Pipeline sklearn |
| Leakage temporal | todos los features | TimeSeriesSplit(5) | `train_models.py` |

---

# Parte H — Datos faltantes: MCAR, MAR y MNAR

Auditoría sobre **3.420 partidos**, **51 columnas** — de las cuales **42 variables críticas tienen 0% nulos** (`18_Auditoria_Calidad_Datos.md`).

## H.1 MCAR — Missing Completely at Random

| Variable | Casos | Diagnóstico | Tratamiento |
|----------|-------|-------------|-------------|
| `attendance` | 1 fila | Olvido aislado de registro | `dropna` — impacto despreciable |

## H.2 MAR — Missing at Random

| Variables | % nulos aprox. | Causa | Tratamiento |
|-----------|----------------|-------|-------------|
| `home_xg`, `away_xg` | ~14.4% en xG local | Temporadas 2017/18 sin tracking óptico estandarizado | KNNImputer ($k=5$, `weights='distance'`) **dentro del fold** |
| `h_l5_*`, `a_l5_*` | Inicio de cada temporada | Sin historial previo para promediar | Idem — no se borran filas |
| `B365H/D/A` | Esporádico | Cuotas no publicadas en partidos antiguos | Idem |

**Validación post-imputación (`home_xg`, 494 registros imputados):**

| Métrica | Antes | Después | Δ |
|---------|-------|---------|---|
| Media μ | 1.6141 | 1.6214 | +0.0073 |
| Desv. σ | 0.9492 | 0.8981 | −0.0511 |
| Min / Max | 0.00 / 6.67 | 0.00 / 6.67 | Conservados |

**Test Kolmogorov-Smirnov:** $D = 0.03371$, $p = 0.05393 > 0.05$ → no se rechaza $H_0$ (misma distribución). Gráfico: `Carpeta_Presentacion/19_Comparacion_Antes_Despues_Imputacion.png`.

## H.3 MNAR — Missing Not at Random

| Variables | Causa sistemática | Tratamiento |
|-----------|-------------------|-------------|
| `result_1x2`, goles | Partidos **no jugados aún** | `dropna(subset=['result_1x2'])` en train; nulos reservados para inferencia |

## H.4 Variables certificadas 0% nulos post-sanitización

`game_id` · `date` · `home_elo` / `away_elo` · `home_rest` / `away_rest` · `is_derby` · `relegation_pressure` · `result_1x2` (en partidos jugados)

Gráfico de matriz de nulos: `Carpeta_Presentacion/18_Auditoria_Nulos_Matriz.png`

---

# Parte I — Prevención de leakage (consolidado)

| Riesgo | Mitigación |
|--------|------------|
| Stats post-partido en features | Drop en sanitizador (Parte F.3) |
| Cuotas bookmaker en train | Bet365 **excluidas** de `FEATURES` en `config.py` |
| EWMA incluye partido actual | `shift(1)` antes del EWM |
| Escalado / imputación global | Transformaciones **dentro** del Pipeline por fold |
| Partidos futuros en train | `dropna(subset=['result_1x2'])` |
| Resampling pre-split | Tomek Links **solo** en train fold |
| Validación aleatoria | **Prohibida** — solo `TimeSeriesSplit(n_splits=5)` |

---

# Parte J — Matriz de 27 features (`config.py`)

**Jerarquía (6):** `home_elo`, `away_elo`, `home_rest`, `away_rest`, `is_derby`, `relegation_pressure`

**Árbitro (1):** `referee_avg_cards_history`

**Local L5 (10):** `h_l5_pts`, `h_l5_sh`, `h_l5_sot`, `h_l5_sot_c`, `h_l5_gf`, `h_l5_ga`, `h_l5_fls`, `h_l5_conv`, `h_l5_xg`, `h_l5_xga`

**Visitante L5 (10):** `a_l5_*` (espejo)

Cuotas Bet365, nombres de equipos y árbitro crudo **no** entran en esta matriz.

---

# Parte K — Preprocesamiento en entrenamiento (post-v8)

Ejecutado en `train_models.py` / `aplicar_hiperparametros.py` vía `ColumnTransformer`:

| Grupo de features | Pipeline |
|-------------------|----------|
| Asimétricas (cuotas, tarjetas, xG L5) | `KNNImputer(5)` → `PowerTransformer(yeo-johnson)` |
| Estándar (Elo, rest, derby, L5 pts/sh…) | `KNNImputer(5)` → `StandardScaler` |

- Imputación **nunca** sobre targets.
- Parámetros aprendidos solo del bloque train de cada split temporal.

## K.1 Distribución de clases (targets)

| Mercado | Proporción destacada |
|---------|---------------------|
| 1X2 Empate | 23.22% |
| DC 1X positivo | 67.36% |
| HCS positivo | 29.80% |
| O/U, BTTS | ~50/50 |

Fuente: `Carpeta_Presentacion/23_Estudio_Desbalance_Resampling.md`

## K.2 Gráficos EDA de soporte

| # | Tema | Archivo |
|---|------|---------|
| 1–2 | Missing values, outliers | `Carpeta_Presentacion/1_*`, `2_*` |
| 3–4 | Multicolinealidad, desbalance | `3_*`, `4_*` |
| 5 | Boxplots por feature | `5_*` |
| 18–19 | Auditoría nulos, K-S imputación | `18_*`, `19_*` |

---

# Parte L — Orden de ejecución recomendado

```
1. archive/pl-scraper/run_all_seasons.py     (si hay temporadas pendientes)
2. [unificación → all_match_features_v4_xg.csv]
3. python sanitizer_pipeline.py              → historical_sanitized_v8.csv
4. python archive/pl-predictor/aplicar_hiperparametros.py
5. Simulacion_Inversion/…                    (calibración, meta-labeling)
```

Ver inventario completo en `08_Inventario_Scripts_y_Artefactos.md`.
