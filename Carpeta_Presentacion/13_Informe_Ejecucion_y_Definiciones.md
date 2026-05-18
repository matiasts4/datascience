# Informe de Ejecución y Definiciones Arquitectónicas
**Proyecto:** Premier League Predictor (Data Science & Machine Learning)

Este documento es una guía rápida para cualquier persona (jurado, profesor o desarrollador) que necesite auditar, ejecutar o entender las decisiones fundacionales de este proyecto.

---

## 1. 🚀 Guía de Ejecución

El proyecto está diseñado para ejecutarse modularmente desde la terminal. Para replicar los resultados, asegúrese de estar en la raíz del proyecto (`c:\Users\sergi\Desktop\datascience\`) y ejecutar los siguientes comandos:

### A. Entrenamiento y Backtesting Financiero
**Comando:** `python -X utf8 archive/pl-predictor/train_models.py`
* **¿Qué hace?** Lee la base de datos maestra (`historical_sanitized_v8.csv`), aplica las transformaciones matemáticas en un *Pipeline* aislado, entrena 8 modelos RandomForest paralelos y evalúa la rentabilidad histórica usando un criterio de Kelly sobre las cuotas reales de Bet365.

### B. Predicción en Vivo (Producción)
**Comando:** `python -X utf8 archive/pl-predictor/predict_upcoming_bets.py`
* **¿Qué hace?** Escrapea la jornada actual de la Premier League desde internet, calcula el Elo Rating en tiempo real de los equipos a jugar, pasa los datos por el modelo pre-entrenado y escupe recomendaciones de apuestas (Positive Expected Value).

### C. Generación de Material de Presentación
**Comando:** `python -X utf8 generate_pres.py` (y sus partes subsecuentes `part2`, `part3`, etc).
* **¿Qué hace?** Genera todos los gráficos analíticos (Distribuciones, Matrices de Multicolinealidad, Test de Kolmogorov-Smirnov, Feature Importance) y los guarda en alta resolución en la `Carpeta_Presentacion`.

---

## 2. 🧠 Definiciones Arquitectónicas Principales

Para lograr que el modelo fuera matemáticamente riguroso y aprobara los estándares OSSEMN/CRISP-DM, se tomaron las siguientes decisiones drásticas:

### A. Eliminación Absoluta del Data Leakage (Fuga de Información)
* **El Problema:** Inicialmente, el dataset se escalaba (StandardScaler) y se imputaba (KNNImputer) globalmente antes de dividir los datos. Esto causaba "Train-Test Contamination" (el modelo aprendía de la media de partidos del futuro para predecir el pasado).
* **La Solución (Pipeline):** Todo el procesamiento de datos se encapsuló en `sklearn.pipeline.Pipeline`. Las métricas de imputación y normalización ahora se calculan **estrictamente sobre el bloque de entrenamiento** en cada iteración de la validación cruzada temporal (`TimeSeriesSplit`).
* **Blindaje Adicional:** Las "Cuotas de Apuestas" se eliminaron deliberadamente de las variables de entrenamiento. Si la IA aprende de las cuotas, simplemente copia al Bookmaker (Target Leakage) en lugar de aprender de fútbol orgánico.

### B. Feature Selection (La Matriz de 27 Variables)
Pasamos de un dataset crudo y ruidoso de ~50 variables a un modelo pulido de **27 variables continuas**.
* **Eliminación de Multicolinealidad:** Variables como "Goles Anotados" o "Tiros Totales" fueron eliminadas si eran tautológicas frente a otras más poderosas. Se priorizó a los **Expected Goals (xG)** como la métrica reina del volumen ofensivo/defensivo.
* **Transformación Categórica Avanzada:** En lugar de usar `One-Hot Encoding` para los nombres de los equipos (lo cual generaría una matriz dispersa e inútil de 20 columnas con puros ceros), se implementó el **Elo Rating**. Esta heurística convierte la "camiseta" de un club en un número continuo de fuerza jerárquica que sube o baja tras cada partido, proveyendo al modelo de contexto histórico.

### C. Domesticación de Distribuciones (Manejo de Outliers)
En el fútbol, los outliers (como una racha de 4 xG) contienen información vital y no pueden ser simplemente borrados.
* **Decisión:** En lugar de hacer recortes (`Trimming`), se aplicó una transformación paramétrica **Yeo-Johnson** a todas las variables asimétricas (rachas de faltas, xG). Esta fórmula matemática comprime las colas largas (outliers) y convierte la distribución en una perfecta Campana de Gauss, haciéndola digerible para la inteligencia artificial sin perder un solo registro.

### D. Estrategia frente al Desbalanceo de Clases (Target Imbalance)
* El mercado de fútbol sufre un grave desbalanceo (el "Empate" ocurre solo el ~24% de las veces).
* **Decisión:** Se rechazaron técnicas de oversampling artificial como SMOTE (ya que inventar "partidos sintéticos" destruye la lógica matemática del deporte). En su lugar, se eligió utilizar modelos ensamblados basados en árboles (**Random Forest**) que son intrínsecamente inmunes al desbalanceo, y se optimizó la toma de decisiones utilizando `.predict_proba()` con umbrales de confianza estrictos, en lugar de clasificaciones duras (`.predict()`).
