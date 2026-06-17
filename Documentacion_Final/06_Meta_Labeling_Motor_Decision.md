# 06 — Meta-Labeling: Motor de Decisión

## 6.1 Fundamento

Inspirado en **Meta-Labeling** (López de Prado, *Advances in Financial Machine Learning*):

| Capa | Pregunta | Output |
|------|----------|--------|
| Primary (Capa 1) | ¿Probabilidad del evento? | Dirección / prob |
| Meta (Capa 2) | ¿**Ejecutar** la apuesta? | Sí / No |

Detecta **falsos positivos de EV**: valor teórico donde contexto (fatiga, cuota, ELO) hace improbable el acierto.

---

## 6.2 Implementación

**Scripts:** `Simulacion_Inversion/simular_meta_decision.py` · `scratch/comparar_metamodelos.py` · `scratch/analizar_ganancias_por_mercado.py`

| Elemento | Detalle |
|----------|---------|
| Target | 1 = apuesta ganada, 0 = perdida |
| Features | `prob`, `odd`, `ev`, `elo_diff`, `rest_diff` |
| Algoritmo default | `RandomForestClassifier(n_estimators=100, max_depth=3)` |
| Regla | Ejecutar si `P(ganar) ≥ 0.50` |
| Entrenamiento | Walk-forward; mín. 30 apuestas históricas por split |
| Inputs | `predicciones_prueba_calibradas.csv` + `historical_with_ou_odds.csv` |

El meta-modelo **no reentrena** Capa 1 — actúa como gatekeeper externo.

---

## 6.3 Comparativa de algoritmos meta

Fuente: `scratch/comparacion_algoritmos_metamodelo.md`

### Solo Meta-Modelo

| Algoritmo | Banca | ROI | Bets | Evitadas |
|-----------|-------|-----|------|----------|
| **Random Forest** | **$1.823,62** | **+9.96%** | 827 | 1.433 |
| Logistic Regression | $1.880,89 | +10.77% | 818 | 1.442 |
| SVM | $1.528,37 | +9.68% | 546 | 1.714 |
| XGBoost | $1.671,38 | +7.42% | 905 | 1.355 |

### Sistema Dual (EV + Meta)

| Algoritmo | Banca | ROI |
|-----------|-------|-----|
| Logistic Regression | $1.845,69 | **+10.28%** |
| Random Forest | $1.711,82 | +8.52% |

**Default entrega:** RF solo meta (+9.96%). Mejor dual: LogReg (+10.28%).

---

## 6.4 Impacto cuantitativo

| Métrica | Sin meta | Con meta (RF) | Delta |
|---------|----------|---------------|-------|
| ROI | −1.85% | **+9.96%** | +11.81 pp |
| Banca | $582.74 | **$1.823,62** | +$1.240,88 |
| Apuestas | 2.260 | 827 | −63.4% |
| Max Drawdown | 77.26% | **19.23%** | −75% riesgo |

---

## 6.5 Por qué funciona

1. Filtra EV alto con contexto adverso (`rest_diff` negativo).
2. Penaliza cuotas altas con mayor tasa de error histórica.
3. Aprende walk-forward qué EVs son reales vs ruidosos.
4. Reduce varianza → drawdown institucionalmente aceptable.

---

## 6.6 SHAP del meta-modelo

Gráfico: `Carpeta_Presentacion/shap_capa2_metamodelo.png`

| Feature | Rol |
|---------|-----|
| `ev` | #1 — EV alto → aprobación |
| `rest_diff` | Fatiga desfavorable → bloqueo |
| `odd` | Regulador de riesgo |
| `elo_diff`, `prob` | Contexto moderado |

---

## 6.7 Limitaciones

- Depende de calidad de Capa 1 (no corrige dirección).
- Cold start: primeras ~30 apuestas sin filtro meta.
- No modela límites de book ni movimiento de línea.

Scripts gráficos: `scratch/graficar_frontera_metamodelo.py`, `graficar_thresholds.py`
