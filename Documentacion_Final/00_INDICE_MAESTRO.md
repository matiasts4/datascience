# BetAnalytics — Documentación Técnica Final

> **Proyecto:** Predicción de mercados de apuestas y gestión cuantitativa de capital — Premier League  
> **Versión:** Entrega final · Premier League 2017/18 – 2025/26

---

## Índice (10 documentos)

| # | Documento | Contenido |
|---|-----------|-----------|
| **00** | [INDICE_MAESTRO.md](./00_INDICE_MAESTRO.md) | Este índice y convenciones |
| **01** | [Vision_General_y_Contexto.md](./01_Vision_General_y_Contexto.md) | Alcance, pregunta de investigación, stack, mercados |
| **02** | [Arquitectura_y_Pipeline_Datos.md](./02_Arquitectura_y_Pipeline_Datos.md) | Arquitectura, **scraping FBRef**, limpieza OSSEMN, sanitización v8, missing data, leakage |
| **03** | [Modelos_ML_y_Validacion.md](./03_Modelos_ML_y_Validacion.md) | Algoritmos, modelos producción, Optuna, resampling, métricas |
| **04** | [Cuotas_Calibracion_y_Gestion_Riesgo.md](./04_Cuotas_Calibracion_y_Gestion_Riesgo.md) | Bet365, Poisson, calibración isotónica, EV, Kelly |
| **05** | [Resultados_Simulacion_Financiera.md](./05_Resultados_Simulacion_Financiera.md) | ROI, drawdown, P&L por mercado, Monte Carlo |
| **06** | [Meta_Labeling_Motor_Decision.md](./06_Meta_Labeling_Motor_Decision.md) | Meta-modelo walk-forward, comparativa de algoritmos |
| **07** | [Interpretabilidad_y_Trazabilidad.md](./07_Interpretabilidad_y_Trazabilidad.md) | SHAP, iteraciones P1→final, decisiones de diseño |
| **08** | [Inventario_Scripts_y_Artefactos.md](./08_Inventario_Scripts_y_Artefactos.md) | Pipeline ejecutable, scripts, CSVs, PNGs |
| **09** | [Referencia_Rapida_Metricas.md](./09_Referencia_Rapida_Metricas.md) | Tablas consolidadas para consulta y defensa |

---

## Resultado final

**Calibración isotónica + Meta-Labeling (Random Forest): ROI +9.96%** en 5 mercados reales Bet365 · Drawdown **19.23%** · 827 apuestas de 2.260 candidatas (63.4% filtradas).

---

## Fuentes primarias en el repositorio

| Área | Ruta |
|------|------|
| Modelado | `archive/pl-predictor/` |
| Simulación | `Simulacion_Inversion/` |
| Análisis reciente | `scratch/` |
| Entregables visuales | `Carpeta_Presentacion/` |
| Config producción | `archive/pl-predictor/src/config.py` |

---

## Convenciones

- **Mercados reales (5):** 1X2, DC 1X, DC X2, Over/Under 2.5 — cuotas Bet365 históricas.
- **Mercados sintéticos (3):** BTTS y Home Clean Sheet — cuotas Poisson (ROI no extrapolable a real).
- **Selección Optuna:** Accuracy en CV temporal (5 splits).
- **Simulación:** Banca $1.000 · Stake flat 1% ($10) · Umbral EV base 5%.
