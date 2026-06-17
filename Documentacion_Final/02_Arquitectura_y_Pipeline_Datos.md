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

# Parte B — Pipeline de datos

## B.1 Flujo ETL

```
FBRef (archive/pl-scraper/) → CSV por temporada
    → all_match_features_v4_xg.csv  (3.420 filas, RAW — no entrenar)
    → sanitizer_pipeline.py + sanitizacion.md
    → historical_sanitized_v8.csv     (limpio, sin escalar globalmente)
    → Pipeline sklearn en entrenamiento (imputer + scaler + clasificador)
```

## B.2 Sanitización (6 fases)

| Paso | Acción |
|------|--------|
| 1 | Carga; `game_id` como string |
| 2 | Drop varianza cero (`league`, `notes`, `match_report`) |
| 3 | Drop fila única MCAR en `attendance` |
| 4 | Drop leakage: goles, tarjetas, `score`, vars post-partido |
| 5 | Drop Pinnacle (`PSH/D/A`); conservar Bet365 para simulación |
| 6 | Features EWMA Last-5 (xG, goles, tiros, puntos) |

Documentación de apoyo: `Carpeta_Presentacion/17_*`, `18_*`, `sanitizacion.md`

## B.3 Prevención de leakage

| Riesgo | Mitigación |
|--------|------------|
| Cuotas bookmaker en train | Bet365 **excluidas** de `FEATURES` |
| Escalado global | Transformaciones **dentro** del Pipeline por fold |
| Partidos futuros | `dropna(subset=['result_1x2'])` para train |
| Resampling pre-split | Tomek Links **solo** en train fold |
| Validación aleatoria | **Prohibida** — solo `TimeSeriesSplit` |

## B.4 Matriz de 27 features (`config.py`)

**Jerarquía (6):** `home_elo`, `away_elo`, `home_rest`, `away_rest`, `is_derby`, `relegation_pressure`

**Árbitro (1):** `referee_avg_cards_history`

**Local L5 (10):** `h_l5_pts`, `h_l5_sh`, `h_l5_sot`, `h_l5_sot_c`, `h_l5_gf`, `h_l5_ga`, `h_l5_fls`, `h_l5_conv`, `h_l5_xg`, `h_l5_xga`

**Visitante L5 (10):** `a_l5_*` (espejo)

## B.5 Preprocesamiento en entrenamiento

- Skewed → `KNNImputer` + `PowerTransformer(Yeo-Johnson)`
- Estándar → `KNNImputer` + `StandardScaler`
- xG 2017/18 faltante → imputación KNN (MAR)

## B.6 Distribución de clases

| Mercado | Proporción destacada |
|---------|---------------------|
| 1X2 Empate | 23.22% |
| DC 1X positivo | 67.36% |
| HCS positivo | 29.80% |
| O/U, BTTS | ~50/50 |

Fuente: `Carpeta_Presentacion/23_Estudio_Desbalance_Resampling.md`

## B.7 Gráficos EDA

`Carpeta_Presentacion/1_*` a `5_*` — missing, outliers, multicolinealidad, desbalance, boxplots.
