# 09 — Referencia Rápida de Métricas y Resultados

Documento de consulta rápida para defensa, revisión y trazabilidad numérica.

---

## A. Modelos de producción (8 mercados)

| Mercado | Modelo | Resampling | Acc CV | F1 CV |
|---------|--------|:----------:|--------|-------|
| 1X2 | LogReg Elastic Net | Tomek | 52.84% | 0.4703 |
| DC 1X | LogReg Elastic Net | — | 70.82% | 0.8063 |
| DC X2 | LogReg Elastic Net | — | 65.35% | 0.7062 |
| Over 2.5 | XGBoost | — | 57.02% | 0.6810 |
| Under 2.5 | XGBoost | — | 57.34% | 0.3192 |
| BTTS Yes | HistGradientBoosting | — | 54.61% | 0.6365 |
| BTTS No | Neural Network | — | 53.94% | 0.3612 |
| HCS | Neural Network | Tomek | 70.99% | 0.0635 |

Fuente: `optimized_hyperparams.json` · `modelos_finales_metricas.md`

---

## B. Log-loss ganadores

| Mercado | Log Loss | Acc |
|---------|----------|-----|
| 1X2 | 0.9913 | 0.5284 |
| DC 1X | 0.5734 | 0.7082 |
| DC X2 | 0.6191 | 0.6535 |
| Over 2.5 | 0.6844 | 0.5702 |
| Under 2.5 | 0.6841 | 0.5734 |
| BTTS Yes | 0.6913 | 0.5461 |
| BTTS No | 1.2122 | 0.5394 |
| HCS | 0.6569 | 0.7099 |

Fuente: `scratch/optimized_models_log_loss.md`

---

## C. Resultados financieros — mercados reales

| Config | Banca | ROI | Bets | Max DD |
|--------|-------|-----|------|--------|
| Baseline (iso, EV≥5%) | $582.74 | −1.85% | 2.260 | 77.26% |
| Solo EV dinámico | $633.14 | −1.65% | 2.226 | 74.08% |
| **Solo Meta RF** | **$1.823,62** | **+9.96%** | 827 | **19.23%** |
| Sistema Dual RF | $1.711,82 | +8.52% | 835 | 19.23% |

Fuente: `reporte_meta_decision.csv`

---

## D. Meta-algoritmos comparados

| Algoritmo | ROI solo meta | ROI dual |
|-----------|---------------|----------|
| Random Forest | **+9.96%** | +8.52% |
| Logistic Regression | +10.77% | **+10.28%** |
| SVM | +9.68% | +10.32% |
| XGBoost | +7.42% | +4.50% |

Fuente: `scratch/comparacion_algoritmos_metamodelo.md`

---

## E. P&L por mercado (Sistema Dual RF)

| Mercado | ROI | Net USD |
|---------|-----|---------|
| **1X2** | **+14.16%** | +$562.20 |
| DC 1X | −1.43% | −$3.00 |
| DC X2 | +6.50% | +$27.31 |
| Over 2.5 | +1.62% | +$35.90 |
| Under 2.5 | +5.84% | +$89.40 |
| **Total** | **+8.52%** | **+$711.82** |

---

## F. Calibración — impacto clave

| Escenario | Banca | ROI |
|-----------|-------|-----|
| 8 mkts sin calibrar | $8.77 | −6.21% |
| 8 mkts isotónica | $1.334 | +1.44% |
| 5 mkts real isotónica | $583 | −1.85% |
| 5 mkts + meta RF | $1.824 | **+9.96%** |

---

## G. Parámetros de simulación

| Parámetro | Valor |
|-----------|-------|
| Banca inicial | $1.000 |
| Stake flat | $10 (1%) |
| Umbral EV | 5% |
| Calibración | Isotónica |
| Meta threshold | P(ganar) ≥ 0.50 |
| Meta algoritmo | RF, max_depth=3 |
| CV | TimeSeriesSplit, 5 folds |
| Dataset train | historical_sanitized_v8.csv |
| Partidos OOF | ~2.356 |

---

## H. Mercados y cuotas

| Tipo | Mercados |
|------|----------|
| Cuota real Bet365 | 1X2, DC 1X, DC X2, O/U 2.5 |
| Cuota sintética Poisson | BTTS Yes/No, HCS |
| Features entrenamiento | 27 (sin cuotas Bet365) |
| Overround referencia | ~6.38% |

---

## I. Archivos fuente por métrica

| Métrica | Archivo |
|---------|---------|
| Accuracy / hiperparámetros | `optimized_hyperparams.json` |
| Log-loss | `scratch/optimized_models_log_loss.csv` |
| ROI headline | `reporte_meta_decision.csv` |
| Meta comparativa | `scratch/comparacion_algoritmos_metamodelo.md` |
| P&L mercado | `scratch/ganancias_por_mercado_metamodelo.md` |
| Confusion matrices | `scratch/matrices_confusion_reporte.md` |

---

## J. Resultado final (una línea)

**BetAnalytics en 5 mercados reales Bet365: calibración isotónica + Meta-Labeling (RF) → ROI +9.96%, drawdown 19.23%, 827/2.260 apuestas ejecutadas.**
