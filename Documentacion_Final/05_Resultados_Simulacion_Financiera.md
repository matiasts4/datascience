# 05 — Resultados de Simulación Financiera

## 5.1 Configuración base

| Parámetro | Valor |
|-----------|-------|
| Banca inicial | $1.000 USD |
| Stake flat | 1% = $10/apuesta |
| Umbral EV | 5% |
| Calibración | Isotónica |
| Partidos simulados | ~2.356 (predicciones OOF calibradas) |
| Cuotas | Bet365 históricas (portfolio real) |

---

## 5.2 Resultado headline — mercados reales

Fuente: `Simulacion_Inversion/reporte_meta_decision.csv`

| Configuración | Banca | ROI | Apuestas | Evitadas | Max DD |
|---------------|-------|-----|----------|----------|--------|
| Línea base (iso, EV≥5%) | $582.74 | **−1.85%** | 2.260 | 0 | 77.26% |
| Solo EV dinámico | $633.14 | −1.65% | 2.226 | 34 | 74.08% |
| **Solo Meta-Modelo (RF)** | **$1.823,62** | **+9.96%** | 827 | 1.433 | **19.23%** |
| Sistema Dual (EV + Meta) | $1.711,82 | +8.52% | 835 | 1.391 | 19.23% |

---

## 5.3 P&L por mercado — Sistema Dual RF

Fuente: `scratch/ganancias_por_mercado_metamodelo.md`

| Mercado | Colocadas | ROI | Net USD | Win Rate |
|---------|-----------|-----|---------|----------|
| **1X2** | 397 | **+14.16%** | +$562.20 | 29.47% |
| DC 1X | 21 | −1.43% | −$3.00 | 66.67% |
| DC X2 | 42 | +6.50% | +$27.31 | 69.05% |
| Over 2.5 | 222 | +1.62% | +$35.90 | 54.50% |
| Under 2.5 | 153 | +5.84% | +$89.40 | 53.59% |
| **Total** | 835 | **+8.52%** | **+$711.82** | 43.47% |

Alpha principal: mercado **1X2** (+$562 de +$712).

---

## 5.4 Por mercado sin meta (flat, isotónica)

| Mercado | Banca | ROI | Apuestas |
|---------|-------|-----|----------|
| 1X2 | $822.60 | −0.88% | 2.022 |
| DC 1X | $498.06 | −9.80% | 512 |
| DC X2 | $731.96 | −5.58% | 480 |
| Over 2.5 | $867.00 | −1.91% | 697 |
| Under 2.5 | $966.00 | −0.42% | 816 |

Ningún mercado es rentable solo con calibración; el meta-modelo aporta la selección.

---

## 5.5 Portfolio 8 mercados (incluye sintéticos)

Fuente: `Simulacion_Inversion/analisis_simulacion_rentabilidad.md`

| Config | Banca | ROI | Nota |
|--------|-------|-----|------|
| Sin calibrar | $6.168 | +22.05% | Probs infladas |
| Isotónica | $7.298 | +26.86% | Incluye BTTS sintético |
| BTTS solo | $7.867 | +43.05% | Cuotas Poisson infladas |

**No extrapolar** estos ROI a mercado real.

---

## 5.6 Monte Carlo (pre-meta)

Fuente: `analisis_montecarlo_sharpe.md` · 1.000 permutaciones

| Escenario | Sharpe/bet | Prob. ruina |
|-----------|------------|-------------|
| 1X2 flat | 0.00 | 6.10% |
| Portfolio real flat | −0.0043 | 9.00% |

Calculado sin meta-modelo. La rentabilidad emerge post-meta (+9.96%).

---

## 5.7 Artefactos y gráficos

**CSVs:** `reporte_meta_decision.csv` · `reporte_simulacion_calibrada.csv` · `predicciones_prueba_calibradas.csv`

**PNG:** `35_*`, `36_*`, `37_*`, `46_Simulacion_Meta_Labeling.png`, `48_*`–`50_*`, `comparativa_algoritmos_metamodelo.png`

---

## 5.8 Resumen ejecutivo

```
Mercados ML:           8  |  Mercados cuota real:  5
Accuracy CV:    52.8% – 71.0%
ROI baseline real:         −1.85%
ROI Meta-Modelo RF:        +9.96%  ← RESULTADO FINAL
Drawdown:           77.26% → 19.23%
Apuestas filtradas:        63.4%
```
