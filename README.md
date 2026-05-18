# 🧠 Data Science Workspace - Premier League Predictor

Este repositorio está estandarizado bajo los frameworks **OSSEMN** y **CRISP-DM**, enfocado estructuralmente en la predicción de resultados analíticos de Fútbol (Premier League) garantizando la trazabilidad matemática y contención de métricas puras.

---

## 📂 Organización y Rutas Principales

El proyecto se divide de manera modular. A continuación, el mapa de la anatomía del Workspace:

### 1. Documentación Core
- **`📁 DataSciencePDF/`**: Material fundacional y apuntes universitarios/teóricos de OSSEMN, Manejo de Transformaciones, Modelos GIGO, etc.
- **`📄 sanitizacion.md`**: 🔥 **El Santo Grial del Preprocesamiento.** Checklist metodológico 100% blindado de la teoría que debe aplicarse antes de que cualquier modelo consuma de estas tablas.
- **`📄 rubrica.md`**: Detalles de evaluación o entregables. 

### 2. Algoritmia y Modelado (La Capa de IA)
- **`📄 eval_models.py`** / **`eval_models_pro.py`** / **`eval_models_expert.py`**: Laboratorios de experimentación. Toman datos procesados y ejecutan ciclos de Regresión Logística y Bosques (RandomForest) sobre los mercados (Ej. Línea 1X2, Over/Under). 
- **`📄 run_eda.py`**: Analítico exploratorio crudo y autómata para auditar la integridad de un dataset en búsqueda de ruido o fuga estadística.

### 3. Las Capas de Datos (`archive/`)
Aquí es donde ocurre la extracción (ETL) y el almacenamiento:
- **`📁 archive/pl-scraper/`**: La capa extractiva. Tiene data aislada por temporada (ej. `/data/processed/2022/matches.csv`). 
  > ⚠️ *Estado:* Data particionada y cruda. Posee variables de varianza cero y ruido de formato.
- **`📁 archive/pl-predictor/data/historical/`**: **EL CORE DE NEGOCIO.** Acá conviven los maestros unificados año por año y las matrices finales de machine learning.

---

## 📊 Arquitectura del Dato: ¿Cuál usar y en qué estado están?

Si vas a levantar un modelo hoy o probar el pipeline de preprocesamiento, esto es lo que debés saber:

#### 🚧 El Dataset Maestro Restringido (RAW / Crudo COMPLETO)
📍 **Ruta:** `archive/pl-predictor/data/historical/all_match_features_v4_xg.csv`
- **¿Qué es?:** Es el dataset base final obtenido por proceso de web-scraping y apilamiento (Ej. historiales L5, variables ELO y Expected Goals xG). **VERIFICADO: Contiene todas las 3420 filas recuperadas (2017 a 2026)** sorteando errores previos de unificación.
- **ESTADO:** **Materia Prima.** Contiene fugas de información, asimetrías severas y outliers que rompen cualquier entrenamiento ML standard. Jamás debe inyectarse a un modelo predictivo directamente.

#### 💎 Output Definitivo (Data Sanitizada Base)
📍 **Ruta Recomendada:** `archive/pl-predictor/data/historical/historical_sanitized_v8.csv`
- **ESTADO: 100% LISTO PARA MODELADO (RAW SANITIZADO).** 
- **¿Qué es?:** El hijo matriz del pipeline `sanitizer_pipeline.py`. Ha pasado por los rigurosos estándares metodológicos formalizados en `sanitizacion.md`, pero de forma "inteligente":
  - **Dropeo de Fugas de Información:** Se eliminaron las cuotas de apuestas de las métricas de entrenamiento para evitar el sesgo del Bookmaker, y se eliminaron los goles reales previos por alta colinealidad.
  - **Data Leakage Cero:** El dataset `v8` NO tiene aplicada la normalización ni la imputación de manera global. Se guarda "crudo pero limpio" para que las transformaciones se aprendan estrictamente dentro del *Train Split* usando `sklearn.pipeline.Pipeline`.
  
  > ⚠️ **¡ADVERTENCIA DE INTEGRIDAD ML (Fixtures Futuros)!** 
  > El dataset `v8` abarca hasta la temporada 2025/26. Contiene explícitamente los calendarios pre-cargados de partidos aún no jugados. Los modelos utilizan `dropna(subset=['result_1x2'])` para entrenar solo con el pasado, y usan los nulos para inferir el futuro.

---

## 🏗️ La Matriz de 27 Features (El Cerebro del Modelo)
Tras exhaustivos análisis de Multicolinealidad y EDA, el modelo ignora los nombres de los equipos y utiliza una matriz exacta de 27 variables continuas:
1. **Jerarquía (6):** `home_elo`, `away_elo`, `home_rest`, `away_rest`, `is_derby`, `relegation_pressure`.
2. **Árbitro (1):** `referee_avg_cards_history`.
3. **Racha Ofensiva/Defensiva Local (10):** Puntos, Tiros, Tiros al arco, Goles, Faltas, xG a favor y en contra (media móvil de 5 partidos).
4. **Racha Ofensiva/Defensiva Visita (10):** Lo mismo aplicado al visitante.

---

## 🛠️ ¿Cómo iniciar o ejecutar el proyecto?

**1. Entrenamiento y Backtesting:**
Para entrenar los 8 modelos base (RandomForest) sobre los mercados (1X2, BTTS, O2.5) y ver el rendimiento financiero:
`python archive/pl-predictor/train_models.py`

**2. Predicción en Vivo (Apuestas Reales):**
Para escrapear la jornada actual, pasar por el pipeline matemático y obtener recomendaciones de Positive EV:
`python archive/pl-predictor/predict_upcoming_bets.py`

**3. Generación de Gráficos de Presentación:**
Los scripts `generate_pres.py`, `generate_pres_part2.py`, etc., en la raíz, re-entrenan modelos a nivel visual para exportar PNGs analíticos a la `Carpeta_Presentacion`.
