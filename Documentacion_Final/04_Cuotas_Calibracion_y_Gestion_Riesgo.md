# 04 — Cuotas, Calibración y Gestión de Riesgo

---

# Parte A — Cuotas y mercados

## A.1 Tipología por mercado

| Mercado | Cuota | Columnas / origen |
|---------|-------|-------------------|
| 1X2 | Real Bet365 | `B365H`, `B365D`, `B365A` |
| DC 1X / X2 | Derivada 1X2 | `B365_1X`, `B365_X2` |
| Over/Under 2.5 | Real Bet365 | `B365>2.5`, `B365<2.5` |
| BTTS Yes/No, HCS | Sintética Poisson | Generada en simulación |

**Portfolio real (5):** 1X2, DC 1X, DC X2, Over 2.5, Under 2.5  
**Portfolio completo (8):** incluye BTTS/HCS — ROI inflado por cuotas sintéticas

## A.2 Fórmulas

```
B365_1X = (1 / (1/B365H + 1/B365D)) × 0.98
B365_X2 = (1 / (1/B365D + 1/B365A)) × 0.98
EV = p̂_calibrada × cuota − 1
```

## A.3 Overround y Poisson

| Concepto | Valor |
|----------|-------|
| Overround Bet365 | ~4–7% (docs usan ~6.38%) |
| BTTS sintético promedio | ~$2.55 vs real $1.70–$2.00 |
| Expectativa ROI real post-meta | 3–8% |

**Limitación Poisson:** independencia de goles infla cuotas BTTS → no extrapolar ROI 8-mercados a producción.

Script cuotas O/U: `obtener_cuotas_over_under.py` · Fallback live: `MasterBetSelector` (ELO + 5% margen)

## A.4 Favorite-longshot bias

| Filtro cuota | ROI 8 mkts | ROI 5 real |
|--------------|------------|------------|
| Favoritos 1.0–2.0 | −2.35% | −0.70% |
| Sorpresas ≥2.50 | +0.49% | −3.90% |

Gráfico: `44_Sensibilidad_Filtro_Cuotas.png`

---

# Parte B — Calibración y filtros

## B.1 Métodos comparados

| Método | Resultado |
|--------|-----------|
| Sin calibrar | Quiebra ($8.77 en portfolio 8) |
| Sigmoide (Platt) | Intermedio |
| **Isotónica** | **Ganadora** — alinea prob con frecuencia empírica |

Implementación: `CalibratedClassifierCV(method='isotonic')`

## B.2 Impacto calibración

### Portfolio 8 mercados (flat 1%)

| Config | Banca | ROI |
|--------|-------|-----|
| Sin calibrar | $8.77 | −6.21% |
| Isotónica | $1.334 | +1.44% |
| Isotónica (incl. sintéticos) | $7.298 | +26.86%* |

*Incluye BTTS/HCS con cuotas Poisson — no comparable a real.

### Mercados reales (flat 1%)

| Mercado | Sin cal. | Isotónica |
|---------|----------|-----------|
| 1X2 | $3.60 | **$822.60** (−0.88%) |
| Under 2.5 | $734 | **$966** (−0.42%) |
| **Portfolio 5** | $0.38 | **$582.74** (−1.85%) |

Fuente: `Simulacion_Inversion/analisis_mercados_reales.md`

## B.3 EV dinámico (Capa 3)

$\text{edge\_req}(c) = 0.05 \times \max(1, \sqrt{c-1})$

Impacto real: −1.85% → −1.65% ROI (marginal vs. meta-modelo).

## B.4 Filtros adicionales

**Probabilidad mínima** (`analisis_filtros_optimizacion.md`):

| Prob ≥ | ROI 8 mkts | ROI 5 real |
|--------|------------|------------|
| 0% | +1.44% | −1.85% |
| 10% | +1.52% | −1.70% |
| 90% | +2.30% | — |

## B.5 Estrategias de staking

| Estrategia | Descripción |
|------------|-------------|
| **Flat** | $10 fijo (1% de $1.000) — usado en resultados headline |
| Full / Half / Quarter Kelly | $f^* = EV/(c−1)$ con cap 2.5–5% |
| Edge-proportional | 0.5 × EV, cap 5% |

135 combos simulados: 3 calibraciones × 9 portfolios × 5 staking.  
Script: `simular_estrategias_apuestas.py` → `reporte_simulacion_calibrada.csv`

Gráficos: `35_*`, `43_*`, `44_*`
