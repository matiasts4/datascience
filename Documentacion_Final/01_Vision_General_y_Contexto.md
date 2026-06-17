# 01 — Visión General y Contexto del Proyecto

## 1.1 Nombre y alcance

**BetAnalytics** es un sistema de predicción cuantitativa aplicado a la **Premier League inglesa** (temporadas 2017/18 a 2025/26). Combina:

1. Modelos de Machine Learning para 8 mercados de apuestas.
2. Calibración post-hoc de probabilidades.
3. Filtros de valor esperado (EV) con gestión de riesgo.
4. Meta-Labeling (segunda capa de decisión) inspirado en López de Prado.

El workspace sigue los marcos **OSSEMN** (Obtain, Scrub, Explore, Model, iNterpret) y **CRISP-DM**.

---

## 1.2 Pregunta de investigación

> ¿Es posible obtener retorno positivo y estable apostando en mercados reales de Bet365 en una liga altamente eficiente, usando ML con calibración y filtrado de apuestas?

### Respuesta cuantitativa del proyecto

| Capa | ¿Suficiente sola? | Evidencia |
|------|-------------------|-----------|
| Capa 1 (modelos sin calibrar) | **No** | Portfolio real quiebra (~$0.38 sin calibrar) |
| Capa 1 + calibración isotónica | **Parcial** | ROI −1.85% en 5 mercados reales (cerca del break-even) |
| Capa 1 + calibración + Meta-Labeling | **Sí** | ROI **+9.96%**, drawdown **19.23%** |

---

## 1.3 Datos disponibles

| Dataset | Ruta | Filas | Uso |
|---------|------|-------|-----|
| Maestro crudo | `archive/pl-predictor/data/historical/all_match_features_v4_xg.csv` | 3.420 | **Nunca entrenar directamente** — contiene leakage |
| Producción sanitizado | `archive/pl-predictor/data/historical/historical_sanitized_v8.csv` | 3.420 | Input oficial de entrenamiento |
| Partidos jugados (train) | Subconjunto con `result_1x2` no nulo | ~3.389 | Entrenamiento y validación |
| Fixtures futuros | `game_id == '0'` o resultados nulos | Resto | Inferencia upcoming |

**Temporadas cubiertas:** 2017, 2018, 2019, 2020, 2021/22 (2122), 2022, 2023, 2024, 2025.

---

## 1.4 Mercados objetivo (8)

Definidos en `archive/pl-predictor/src/config.py`:

| Mercado | Columna target | Tipo |
|---------|----------------|------|
| 1X2 Match Winner | `target_1x2` | Multiclase (0=Visitante, 1=Empate, 2=Local) |
| Double Chance 1X | `target_dc_1X` | Binario |
| Double Chance X2 | `target_dc_X2` | Binario |
| Over 2.5 Goals | `target_over_2_5_goals` | Binario |
| Under 2.5 Goals | `target_under_2_5_goals` | Binario |
| BTTS Yes | `target_btts` | Binario |
| BTTS No | `target_btts_no` | Binario |
| Home Clean Sheet | `target_home_clean_sheet` | Binario |

---

## 1.5 Stack tecnológico

| Componente | Librería / herramienta |
|------------|------------------------|
| Datos | pandas, numpy |
| ML clásico | scikit-learn |
| Boosting | XGBoost, HistGradientBoosting |
| Redes neuronales | PyTorch (MLP custom en `models_neural.py`) |
| Desbalance | imbalanced-learn (Tomek Links) |
| Hiperparámetros | Optuna (TPE) |
| Calibración | `CalibratedClassifierCV` (isotónica, sigmoide) |
| Explicabilidad | SHAP |
| Scraping histórico | `archive/pl-scraper/` (FBRef) |
| Frontend (módulo aparte) | `pl-web/` |

---

## 1.6 Documentación y entregables

| Documento | Ubicación |
|-----------|-----------|
| **Documentación técnica final** | `Documentacion_Final/` (10 archivos .md) |
| Informe evaluación rúbrica | `Simulacion_Inversion/Entregable_Final_Evaluacion_Rubrica.md` |
| Guía presentación 10 min | `Carpeta_Presentacion/Guia_Presentacion_10_Minutos.md` |
| Rúbrica del curso | `rubrica.md` |
