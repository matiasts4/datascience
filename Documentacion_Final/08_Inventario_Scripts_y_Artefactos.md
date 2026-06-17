# 08 — Inventario de Scripts, Artefactos y Pipeline

## 8.1 Pipeline de ejecución (orden)

```
1. python sanitizer_pipeline.py
      → archive/pl-predictor/data/historical/historical_sanitized_v8.csv

2. python archive/pl-predictor/aplicar_hiperparametros.py
      → archive/pl-predictor/models/model_*.pkl  (8 modelos)

3. python Simulacion_Inversion/simular_estrategias_apuestas.py
      → predicciones_prueba_calibradas.csv  ⭐ artefacto central
      → reporte_simulacion_calibrada.csv

4. python Simulacion_Inversion/simular_meta_decision.py
      → reporte_meta_decision.csv
      → Carpeta_Presentacion/46_Simulacion_Meta_Labeling.png

5. Análisis complementarios (scratch/):
      calcular_log_loss.py · comparar_metamodelos.py · generar_shap.py
```

**Dependencia crítica:** pasos 4–5 requieren `predicciones_prueba_calibradas.csv` del paso 3.

---

## 8.2 Estructura del repositorio

```
datascience/
├── Documentacion_Final/       ← esta documentación (10 archivos)
├── Carpeta_Presentacion/      ← PNGs, informes visuales
├── Simulacion_Inversion/      ← simulación, CSVs de resultados
├── scratch/                   ← SHAP, meta-modelos, log-loss
├── archive/pl-scraper/        ← extracción FBRef, CSV por temporada
├── archive/pl-predictor/      ← entrenamiento, modelos, config
├── sanitizer_pipeline.py
└── sanitizacion.md
```

---

## 8.2b Scripts de extracción y limpieza

| Script / módulo | Función |
|-----------------|---------|
| `archive/pl-scraper/pipeline.py` | Scrape por temporada (schedule → lineups → events → stats) |
| `archive/pl-scraper/run_all_seasons.py` | Orquestador multi-temporada |
| `archive/pl-scraper/checkpoint/manager.py` | Reanudación incremental por `game_id` |
| `archive/pl-scraper/scraper/fbref_client.py` | Cliente FBRef (`soccerdata`) |
| **`sanitizer_pipeline.py`** | RAW v4_xg → `historical_sanitized_v8.csv` |
| `sanitizacion.md` | Checklist metodológico OSSEMN (7 secciones) |
| `run_eda.py` | EDA automatizado pre-modelado |

**Informes de calidad:** `Carpeta_Presentacion/17_Tratamiento_Problemas_Datos.md` · `18_Auditoria_Calidad_Datos.md`

---

## 8.3 Scripts de modelado (`archive/pl-predictor/`)

| Script | Función |
|--------|---------|
| **`aplicar_hiperparametros.py`** | Exporta modelos finales `.pkl` |
| `evaluar_modelos_optimos.py` | Evaluación post-tuning (usado por scratch) |
| `tune_hyperparameters_optuna.py` | Optuna TPE → `optimized_hyperparams.json` |
| `train_models_mirrors.py` | Estudio resampling (7 configs) |
| `train_models.py` | Barrido baseline exploratorio |
| `generar_*.py`, `visualizar_*.py` | Gráficos presentación |

**Módulos core:** `src/config.py` · `src/models_neural.py` · `src/models/selector.py` (`MasterBetSelector`)

---

## 8.4 Scripts de simulación (`Simulacion_Inversion/`)

| Script | Output principal |
|--------|------------------|
| **`simular_estrategias_apuestas.py`** | Predicciones calibradas + reportes |
| **`simular_meta_decision.py`** | `reporte_meta_decision.csv` |
| `simular_filtros_optimizacion.py` | `reporte_optimizacion_filtros.csv` |
| `simulacion_montecarlo.py` | Análisis Sharpe |
| `obtener_cuotas_over_under.py` | `historical_with_ou_odds.csv` |
| `inspect_overfitting.py` | Diagnóstico train vs test |
| `graficar_*.py` | Regeneración de PNGs |

---

## 8.5 Scripts de análisis (`scratch/`)

| Script | Output |
|--------|--------|
| `calcular_log_loss.py` | `optimized_models_log_loss.md/.csv` |
| `comparar_metamodelos.py` | `comparacion_algoritmos_metamodelo.md` |
| `analizar_ganancias_por_mercado.py` | `ganancias_por_mercado_metamodelo.md` |
| `generar_shap.py` | PNGs SHAP en Carpeta_Presentacion |
| `graficar_matrices_confusion.py` | `matrices_confusion_reporte.md` |

---

## 8.6 Modelos y datos serializados

```
archive/pl-predictor/models/
├── optimized_hyperparams.json
├── model_1X2_Match_Winner.pkl  … (8 total)
├── baseline_vs_optimized_metrics.csv
└── mirrors/mirror_comparison_results.csv

archive/pl-predictor/data/historical/
├── all_match_features_v4_xg.csv      (RAW)
└── historical_sanitized_v8.csv       (producción)
```

---

## 8.7 CSVs de resultados

| Archivo | Contenido |
|---------|-----------|
| `predicciones_prueba_calibradas.csv` | OOF calibradas — input meta-modelo |
| `reporte_meta_decision.csv` | 4 configs — **ROI headline** |
| `reporte_simulacion_calibrada.csv` | 137 combos cal×staking |
| `reporte_optimizacion_filtros.csv` | 50 filtros |
| `historical_with_ou_odds.csv` | ELO + rest para meta |
| `scratch/optimized_models_log_loss.csv` | Log-loss grid |

---

## 8.8 Informes complementarios (fuera de esta carpeta)

| Tema | Ubicación |
|------|-----------|
| Entrega rúbrica | `Simulacion_Inversion/Entregable_Final_Evaluacion_Rubrica.md` |
| Mercados reales | `Simulacion_Inversion/analisis_mercados_reales.md` |
| Rentabilidad 8 mkts | `Simulacion_Inversion/analisis_simulacion_rentabilidad.md` |
| Modelos métricas | `Carpeta_Presentacion/modelos_finales_metricas.md` |
| Resampling | `Carpeta_Presentacion/23_Estudio_Desbalance_Resampling.md` |
| Guía oral 10 min | `Carpeta_Presentacion/Guia_Presentacion_10_Minutos.md` |

---

## 8.9 Dependencias

`pandas`, `numpy`, `scikit-learn`, `xgboost`, `optuna`, `imbalanced-learn`, `torch`, `shap`, `matplotlib`

Entorno: `venv/` en raíz del proyecto.

---

## 8.10 Mapa rápido documentación → tema

| Tema | Documento |
|------|-----------|
| Visión y alcance | 01 |
| Arquitectura y datos | 02 |
| Modelos y validación | 03 |
| Cuotas y calibración | 04 |
| ROI y simulación | 05 |
| Meta-labeling | 06 |
| SHAP e historial | 07 |
| Scripts y pipeline | 08 (este) |
| Tablas de referencia | 09 |
