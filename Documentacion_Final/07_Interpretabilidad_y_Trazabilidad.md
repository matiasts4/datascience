# 07 — Interpretabilidad (SHAP) y Trazabilidad del Proyecto

---

# Parte A — Interpretabilidad SHAP

## A.1 Framework

**Librería:** SHAP · **Scripts:** `scratch/generar_shap.py`, `test_shap_all.py` · **Guía:** `scratch/explicacion_shap.md`

## A.2 Gráficos Capa 1 (`Carpeta_Presentacion/shap_capa1_*.png`)

| Mercado | Archivo |
|---------|---------|
| 1X2 | `shap_capa1_1x2_match_winner.png` |
| DC 1X / X2 | `shap_capa1_double_chance_1x.png`, `_x2.png` |
| Over/Under 2.5 | `shap_capa1_over_2_5_goals.png`, `_under_2_5_goals.png` |
| BTTS / HCS | `shap_capa1_btts_yes.png`, `_btts_no.png`, `_home_clean_sheet.png` |

## A.3 Gráfico Capa 2

`shap_capa2_metamodelo.png` — meta-modelo Random Forest

## A.4 Patrones globales

**Goles (O/U):** `h_l5_xg`, `a_l5_xg` dominan.

**Resultados (1X2, DC):** ELO y forma reciente dominan.

**BTTS:** `h_l5_ga`, `a_l5_ga`, tiros a puerta.

**Bajo impacto:** `referee_avg_cards_history` — prescindible.

**Meta-modelo:** `ev` #1; `rest_diff` y `odd` regulan riesgo.

## A.5 Regenerar SHAP

```bash
python scratch/generar_shap.py
python scratch/test_shap_all.py
```

---

# Parte B — Trazabilidad e iteraciones

## B.1 Cronología

| Fase | Hito |
|------|------|
| Inicio | Scraping FBRef, dataset v4 |
| EDA | Sanitización v8, auditoría calidad |
| Presentación 1 | POC con leakage — problemas identificados |
| Iteración | TimeSeriesSplit, Optuna, resampling |
| Calibración | 135 combos simulación |
| Meta-Labeling | +9.96% ROI en mercados reales |
| Frontend | Dashboard `pl-web/` (módulo aparte) |

## B.2 Cinco correcciones desde Presentación 1

Fuente: `Simulacion_Inversion/Entregable_Final_Evaluacion_Rubrica.md`

| # | Problema | Corrección | Impacto |
|---|----------|------------|---------|
| 1 | Leakage temporal | TimeSeriesSplit | Métricas honestas |
| 2 | Quiebra financiera | Calibración isotónica | $8.77 → $1.334 |
| 3 | Desbalance 1X2/HCS | Tomek Links | HCS 70.99% acc |
| 4 | Cuotas Poisson sesgadas | ELO + overround 6.38% | ~95% realismo |
| 5 | Drawdown 77% | EV dinámico + Meta | DD 19.23%, ROI +9.96% |

## B.3 Evolución de métricas

```
P1 accuracy inflada (~60%+)  →  52.8%–71.0% (CV temporal honesta)
P1 ROI engañoso              →  −1.85% real / +9.96% con meta
Sin meta-decisión              →  RandomForest walk-forward
```

## B.4 Hitos de desarrollo

| Hito | Aportación |
|------|------------|
| Optuna + resampling | Hiperparámetros definitivos y estudio Tomek Links |
| Informe de evaluación | Documento de defensa ante rúbrica académica |
| Comparativa meta-modelos | Evaluación RF, LogReg, SVM y XGBoost |
| Análisis SHAP | Interpretabilidad Capa 1 y Capa 2 |
| Métricas completas | Log-loss, matrices de confusión y tablas finales |

## B.5 Decisiones de diseño

| Decisión | Razón |
|----------|-------|
| Accuracy como objetivo Optuna | Selección académica consistente |
| Isotónica > Platt | Mejor estabilidad de banca |
| RF meta default | +9.96% vs XGB +7.42% (solo meta) |
| Tomek solo 1X2+HCS | Limpia frontera sin forzar 50/50 |
| Cuotas fuera de FEATURES | Evita bookmaker leakage |

## B.6 Limitaciones conocidas

1. BTTS No NN: alta acc, log-loss 1.21, F1=0 en minoría.
2. XGB O/U: recall extremo (100%/0%).
3. ROI 8-mercados inflado por Poisson BTTS/HCS.
4. Monte Carlo Sharpe calculado pre-meta.
5. Fixtures 2025/26 en v8 requieren `dropna` estricto.

## B.7 Entregables académicos relacionados

`Entregable_Final_Evaluacion_Rubrica.md` · `Informe_Final_Pipeline_y_Meta_Decision.md` · `Guia_Presentacion_10_Minutos.md` · `rubrica.md`
