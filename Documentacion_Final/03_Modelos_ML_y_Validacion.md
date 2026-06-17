# 03 — Modelos de Machine Learning y Validación

---

# Parte A — Algoritmos y modelos de producción

## A.1 Cinco arquitecturas evaluadas (× 8 mercados = 40 combos)

| Algoritmo | Implementación |
|-----------|----------------|
| Logistic Regression (Elastic Net) | `sklearn`, solver `saga` |
| Random Forest | `sklearn.ensemble` |
| HistGradientBoosting | `sklearn`, early stopping |
| XGBoost | `xgboost`, reg L1/L2 |
| Neural Network MLP | `PyTorchMLPClassifier` en `models_neural.py` |

**Red neuronal:** Input → Linear → ReLU → Dropout → Linear(hidden//2) → ReLU → Dropout → Output. BCE/CrossEntropy, Adam, weight_decay=1e-4.

## A.2 Modelos ganadores (producción)

Fuente: `optimized_hyperparams.json`, `Carpeta_Presentacion/modelos_finales_metricas.md`

| Mercado | Modelo | Resampling | Acc CV | F1 CV | AUC CV |
|---------|--------|:----------:|--------|-------|--------|
| **1X2** | LogReg Elastic Net | Tomek | **52.84%** | 0.4703 | N/A |
| **DC 1X** | LogReg Elastic Net | — | **70.82%** | 0.8063 | 0.7147 |
| **DC X2** | LogReg Elastic Net | — | **65.35%** | 0.7062 | 0.7118 |
| **Over 2.5** | XGBoost | — | **57.02%** | 0.6810 | 0.5523 |
| **Under 2.5** | XGBoost | — | **57.34%** | 0.3192 | 0.5528 |
| **BTTS Yes** | HistGradientBoosting | — | **54.61%** | 0.6365 | 0.5222 |
| **BTTS No** | Neural Network | — | **53.94%** | 0.3612 | 0.5127 |
| **HCS** | Neural Network | Tomek | **70.99%** | 0.0635 | 0.5274 |

**Asignación:** LogReg (3) · XGBoost (2) · HGB (1) · MLP (2)

## A.3 Justificación de selección

- **LogReg (1X2, DC):** Mercados eficientes; log-odds estables para calibración; Elastic Net selecciona features.
- **XGBoost (O/U):** No linealidad goles↔xG↔fatiga; `max_depth=2` evita overfit.
- **MLP (BTTS No, HCS):** Alta varianza; dropout 17–30% regulariza.

## A.4 Optuna vs baseline

38/40 combinaciones mejoraron. Mayor salto: NN + HCS (+7.23% acc). JSON: `archive/pl-predictor/models/optimized_hyperparams.json`

## A.5 Paradoja del empate (1X2)

Optimizar Accuracy sacrifica recall de Empate (2% en último fold). Gráfico: `33_Explicacion_F1_1X2.png`

## A.6 Matrices de confusión (último fold)

Fuente: `scratch/matrices_confusion_reporte.md`

| Mercado | Acc | AUC | Nota |
|---------|-----|-----|------|
| 1X2 | 51.77% | 0.6676 | Draw recall 2% |
| DC 1X | 70.39% | 0.7203 | F1=0.80 |
| Over 2.5 XGB | 55.14% | 0.5798 | Recall Over=100% |
| BTTS No NN | 54.43% | 0.6307 | F1=0 (clase mayoría) |

---

# Parte B — Validación, Optuna y resampling

## B.1 TimeSeriesSplit (5 folds)

```
Split 1: 2017–19 → val 2019–20
Split 2: 2017–20 → val 2020–21
Split 3: 2017–21 → val 2021–22
Split 4: 2017–22 → val 2022–23
Split 5: 2017–23 → val 2023–24
Test ciego: 2024–25
```

Calibración: 80% train fold → clasificador; 20% → calibrador; fold val → métricas OOS.

## B.2 Optuna (TPE)

| Parámetro | Valor |
|-----------|-------|
| Objetivo | Maximizar Accuracy (media 5 folds) |
| Trials | 15 (8 para NN) |
| Script export | `tune_hyperparameters_optuna.py` |
| Export producción | `aplicar_hiperparametros.py` → `model_*.pkl` |

Bitácora: `Carpeta_Presentacion/Resumen_Trabajo_Optuna_Resampling.md`

## B.3 Resampling — decisión final

Estudio de 7 configs espejo (`train_models_mirrors.py`, doc `23_Estudio_*`):

| Mercado | Técnica |
|---------|---------|
| 1X2, HCS | **Tomek Links** (solo en train fold) |
| Resto (6) | Sin remuestreo |

## B.4 Log-loss (ganadores)

Fuente: `scratch/optimized_models_log_loss.md`

| Mercado | Log Loss | Acc |
|---------|----------|-----|
| 1X2 LogReg | 0.9913 | 0.5284 |
| DC 1X | 0.5734 | 0.7082 |
| Over 2.5 XGB | 0.6844 | 0.5702 |
| BTTS No NN | **1.2122** | 0.5394 |

BTTS No gana por Accuracy pero pierde en log-loss — trade-off documentado.

## B.5 Overfitting (modelos producción)

| Modelo | Train | Test | Gap |
|--------|-------|------|-----|
| LogReg 1X2 | 54.26% | 53.44% | 0.82% ✓ |
| XGB Over 2.5 | 59.90% | 57.06% | 2.85% ✓ |

Fuente: `Simulacion_Inversion/diagnostico_ajuste_modelos.md`

## B.6 Gráficos

`30_*`, `31_*`, `32_*` (Optuna vs baseline) · `52_Matrices_Confusion_Capa1.png`
