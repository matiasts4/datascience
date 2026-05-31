# Guía Metodológica: Modelos de Clasificación y Medición de Performance (Defensa de Tesis)

Este informe documenta los modelos de clasificación implementados en el proyecto de **BetAnalytics**, detallando sus configuraciones de hiperparámetros, la justificación de las medidas de performance basadas en tus diapositivas y las métricas reales obtenidas en la validación cruzada temporal.

> [!NOTE]
> **Paradigma de Aprendizaje: Aprendizaje Supervisado (Supervised Learning)**
> En este proyecto utilizamos exclusivamente **modelos de aprendizaje supervisado**. Esto significa que los algoritmos entrenan a partir de datos estructurados donde la respuesta o etiqueta (**label / target**) es conocida de antemano (los marcadores de goles reales, resultados de partidos y cuotas). El objetivo de los modelos es resolver tareas de **clasificación supervisada** (estimar probabilidades de victoria, empate, goles, etc.). No se utilizan modelos de aprendizaje no supervisado (como K-Means o agrupamiento sin etiquetas).

---

## 1. 📂 Partición de Datos y Error de Generalización

En machine learning, es estándar dividir la muestra en entrenamiento (**Training Dataset**) y prueba (**Test Dataset**). Tradicionalmente se utiliza un esquema 80/20, pero en datos de series de tiempo deportivos esto induciría a fuga temporal.
* **Nuestra Estrategia:** Implementamos **TimeSeriesSplit con 5 splits**.
* **Error de Generalización (Tasa de Error en nuevos casos):** Cada split valida de forma cronológica sobre un conjunto de prueba "futuro" que el modelo jamás ha visto. La tasa de acierto en este conjunto de prueba representa el error de generalización real del modelo en producción.

---

## 2. 🎛️ Modelos de Clasificación y sus Parámetros

Entrenamos y comparamos 5 clasificadores (lineales y no lineales). A continuación se detallan sus configuraciones de hiperparámetros aplicadas en el código:

### A. Regresión Logística con Elastic Net (Clasificador Lineal)
* **Parámetros:** `penalty='elasticnet'`, `solver='saga'`, `l1_ratio=0.5`, `C=0.1`, `max_iter=5000`.
* **Justificación:** Es un modelo lineal regularizado. El parámetro `l1_ratio=0.5` equilibra la penalización L1 (Lasso, para selección de variables) y la L2 (Ridge, para estabilizar colinealidades), controlando el sobreajuste.

### B. Random Forest Classifier (Clasificador No Lineal - Ensamble Bagging)
* **Parámetros:** `n_estimators` (100 a 500), `max_depth` (5 a 20 según target), `min_samples_split` (2 a 10), `min_samples_leaf=4` (evita hojas demasiado pequeñas que memoricen el ruido), `random_state=42`.
* **Justificación:** Reduce la varianza del modelo promediando múltiples árboles de decisión independientes entrenados en subconjuntos aleatorios.

### C. HistGradientBoosting Classifier (Clasificador No Lineal - Ensamble Boosting)
* **Parámetros:** `learning_rate` (0.01 a 0.041), `max_depth` (3 a 10), `l2_regularization` (0.05 a 9.98), `max_iter` (50 a 200), `early_stopping=True`, `validation_fraction=0.1`, `n_iter_no_change=10`.
* **Justificación:** Construye árboles secuencialmente para corregir los errores de los anteriores. La regularización L2 y el *Early Stopping* (detener el entrenamiento si la pérdida de validación no mejora en 10 iteraciones) protegen el modelo contra el sobreajuste.

### D. XGBoost Classifier (Clasificador No Lineal - Boosting Avanzado)
* **Parámetros:** `max_depth=4`, `learning_rate=0.05`, `n_estimators=150`, `reg_lambda=3.0` (regularización L2), `reg_alpha=0.5` (regularización L1), `eval_metric='logloss'`, `random_state=42`.
* **Justificación:** Optimiza el gradiente con regularización estructural extrema (L1/L2 en los pesos de las hojas), ideal para datasets con ruido y asimetrías.

### E. Red Neuronal Artificial (Perceptrón Multicapa - MLP en PyTorch) (No Lineal)
* **Parámetros:** `input_dim=27` (features), `hidden_dim=64` (neuronas en capa oculta), `dropout_rate=0.3` (30% de apagado aleatorio de neuronas para regularizar), `lr=0.01`, `epochs=80`, `batch_size=64`, `random_state=42`.
* **Justificación:** Mapea relaciones no lineales complejas mediante capas densas conectadas y funciones de activación ReLU, con regularización por Dropout para evitar la codependencia de variables.

---

## 3. 📊 Resultados de Performance Reales (Validación Temporal 5-Splits)

A continuación se presentan las métricas de rendimiento reales obtenidas por los modelos sobre los 3,389 partidos históricos del dataset final:

### A. Mercado: 1X2 (Match Winner) - Clasificación Multiclase
| Clasificador | Accuracy | ROC-AUC | F1-Score (Weighted) |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Elastic Net)** | **0.5298** | - | 0.4631 |
| **Random Forest** | 0.5287 | - | 0.4595 |
| **HistGradientBoosting (Early Stopping)** | 0.5223 | - | 0.4505 |
| **XGBoost (L1/L2 Regularized)** | 0.5007 | - | 0.4567 |
| **Neural Network (Dropout)** | 0.4848 | - | 0.4429 |
* *Ganador:* **Logistic Regression** (Exactitud: 52.98%).

### B. Mercado: Doble Oportunidad 1X (Home or Draw)
| Clasificador | Accuracy | ROC-AUC | F1-Score |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Elastic Net)** | **0.7071** | **0.7145** | 0.8056 |
| **Random Forest** | 0.6957 | 0.6897 | 0.7995 |
| **HistGradientBoosting (Early Stopping)** | 0.6918 | 0.6843 | 0.7997 |
| **XGBoost (L1/L2 Regularized)** | 0.6819 | 0.6817 | 0.7884 |
| **Neural Network (Dropout)** | 0.6702 | 0.6552 | 0.7795 |
* *Ganador:* **Logistic Regression** (Exactitud: 70.71%, ROC-AUC: 0.7145).

### C. Mercado: Doble Oportunidad X2 (Away or Draw)
| Clasificador | Accuracy | ROC-AUC | F1-Score |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Elastic Net)** | **0.6422** | **0.7091** | 0.6851 |
| **Random Forest** | 0.6394 | 0.6952 | 0.6853 |
| **HistGradientBoosting (Early Stopping)** | 0.6372 | 0.6731 | 0.6887 |
| **XGBoost (L1/L2 Regularized)** | 0.6287 | 0.6778 | 0.6704 |
| **Neural Network (Dropout)** | 0.6291 | 0.6615 | 0.6737 |
* *Ganador:* **Logistic Regression** (Exactitud: 64.22%, ROC-AUC: 0.7091).

### D. Mercado: Over 2.5 Goals
| Clasificador | Accuracy | ROC-AUC | F1-Score |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Elastic Net)** | 0.5472 | 0.5576 | 0.6294 |
| **Random Forest** | **0.5525** | 0.5434 | 0.6356 |
| **HistGradientBoosting (Early Stopping)** | 0.5507 | 0.5363 | **0.6644** |
| **XGBoost (L1/L2 Regularized)** | 0.5426 | 0.5361 | 0.6065 |
| **Neural Network (Dropout)** | 0.5156 | 0.5318 | 0.5375 |
* *Ganador:* **Random Forest** (Exactitud: 55.25%).

### E. Mercado: Under 2.5 Goals
| Clasificador | Accuracy | ROC-AUC | F1-Score |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Elastic Net)** | 0.5472 | 0.5576 | 0.4041 |
| **Random Forest** | 0.5486 | 0.5429 | 0.4075 |
| **HistGradientBoosting (Early Stopping)** | **0.5628** | 0.5442 | 0.2893 |
| **XGBoost (L1/L2 Regularized)** | 0.5426 | 0.5361 | **0.4412** |
| **Neural Network (Dropout)** | 0.5163 | 0.5181 | 0.3615 |
* *Ganador:* **HistGradientBoosting** (Exactitud: 56.28%).

### F. Mercado: BTTS (Both Teams To Score)
| Clasificador | Accuracy | ROC-AUC | F1-Score |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Elastic Net)** | 0.5128 | 0.5076 | 0.5686 |
| **Random Forest** | 0.5074 | 0.5001 | 0.5713 |
| **HistGradientBoosting (Early Stopping)** | **0.5323** | 0.5197 | **0.6090** |
| **XGBoost (L1/L2 Regularized)** | 0.5057 | 0.5040 | 0.5597 |
| **Neural Network (Dropout)** | 0.4993 | 0.5078 | 0.5221 |
* *Ganador:* **HistGradientBoosting** (Exactitud: 53.23%).

### G. Mercado: BTTS - No
| Clasificador | Accuracy | ROC-AUC | F1-Score |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Elastic Net)** | 0.5128 | 0.5076 | 0.4013 |
| **Random Forest** | 0.5103 | 0.5004 | 0.3783 |
| **HistGradientBoosting (Early Stopping)** | **0.5351** | 0.5208 | 0.3356 |
| **XGBoost (L1/L2 Regularized)** | 0.5057 | 0.5040 | **0.4289** |
| **Neural Network (Dropout)** | 0.5191 | **0.5235** | 0.4290 |
* *Ganador:* **HistGradientBoosting** (Exactitud: 53.51%).

### H. Mercado: Home Clean Sheet (Valla Invicta Local)
| Clasificador | Accuracy | ROC-AUC | F1-Score |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Elastic Net)** | 0.7004 | **0.6099** | 0.1931 |
| **Random Forest** | 0.7014 | 0.6028 | 0.1733 |
| **HistGradientBoosting (Early Stopping)** | **0.7064** | 0.5967 | 0.0459 |
| **XGBoost (L1/L2 Regularized)** | 0.6936 | 0.5956 | 0.2238 |
| **Neural Network (Dropout)** | 0.6713 | 0.5887 | **0.2896** |
* *Ganador:* **HistGradientBoosting** (Exactitud: 70.64%).

---

## 4. 🎚️ Marco Teórico de Medidas de Performance (Defensa de Tesis)

Para justificar formalmente estas métricas ante tu comisión, enlazamos los resultados con los conceptos de tus diapositivas:

### A. La Matriz de Confusión y sus Errores
La matriz cuenta cuántas veces las observaciones de una clase real se clasifican en la clase predicha:

| | Predicho Negativo (0) | Predicho Positivo (1) |
| :--- | :---: | :---: |
| **Actual Negativo (0)** | Verdadero Negativo (**TN**) | Falso Positivo (**FP**) - *Error Tipo I* |
| **Actual Positivo (1)** | Falso Negativo (**FN**) - *Error Tipo II* | Verdadero Positivo (**TP**) |

* **Error de Tipo I (Falso Positivo):** Predecir que un evento ocurrirá (ej: predecir BTTS = Sí) cuando no ocurre. En nuestro caso de inversión, este es el error **más costoso**, ya que nos llevaría a apostar capital real en una opción perdedora.
* **Error de Tipo II (Falso Negativo):** Predecir que no ocurrirá (ej: predecir no-BTTS) cuando en realidad sí se da. Representa un costo de oportunidad (no apostar y perder una ganancia), pero no destruye capital real.

### B. Precisión, Sensibilidad (Recall) y F1-Score
* **Precision ($\frac{TP}{TP + FP}$):** Mide la capacidad de evitar Falsos Positivos. Se prioriza cuando el costo de equivocarse positivamente es altísimo (como colocar dinero real en una apuesta).
* **Recall / Sensibilidad ($\frac{TP}{TP + FN}$):** Mide la capacidad de detectar todos los casos positivos reales. Se prioriza en áreas donde no podemos permitirnos omitir un caso (como medicina o detección de fraudes bancarios).
* **F1-Score ($2 \times \frac{P \times R}{P + R}$):** Es la **media armónica** entre Precision y Recall. Es un promedio de ambas métricas, útil en literatura de machine learning para resumir el desempeño general en un solo valor.

### C. ¿Cómo decidir qué métrica priorizar?
Depende directamente del contexto del problema de negocio:
* **Exactitud (Accuracy):** La utilizamos principalmente para conjuntos balanceados como `target_over_2_5_goals` ($54.4\% - 45.6\%$) y `target_btts` ($52.9\% - 47.1\%$), donde las clases están distribuidas casi 50/50.
* **Calibración de Probabilidad y Log-Loss:** Dado que BetAnalytics es un sistema de inversión contra casas de apuestas, el objetivo fundamental **no es solo maximizar la exactitud (Accuracy)**, sino optimizar la calibración de probabilidad mediante la reducción del **Log-loss (Binary Cross-Entropy)**:
  $$\text{Log-loss} = -\frac{1}{N} \sum_{i=1}^N \left[ y_i \log(\hat{p}_i) + (1 - y_i) \log(1 - \hat{p}_i) \right]$$
  Esta métrica penaliza fuertemente predicciones erróneas hechas con alta certeza (alta probabilidad). Un Log-loss bajo nos garantiza que las probabilidades del modelo son realistas frente a las cuotas implícitas del mercado, permitiéndonos calcular correctamente el **Valor Esperado positivo (EV+)**.

### D. Curva ROC y AUC
* **Curva ROC:** Grafica la Tasa de Verdaderos Positivos (Recall) contra la Tasa de Falsos Positivos ($1 - \text{Especificidad}$) a través de diferentes umbrales de decisión.
* **AUC (Área Bajo la Curva):** Mide la capacidad discriminativa general del clasificador. 
  * Un $\text{AUC} = 0.50$ representa un desempeño equivalente al azar (lanzar una moneda).
  * Un $\text{AUC}$ cercano a $1.00$ representa una excelente discriminación. En nuestros modelos de Doble Oportunidad, logramos un $\text{AUC} \approx 0.71$, demostrando una capacidad de discriminación significativamente superior al azar.

---

## 5. 🔬 Metodología de Validación y Ajuste del Modelo (Sesgo vs. Varianza)

Para garantizar la solidez científica del proyecto, aplicamos la teoría de validación de modelos a nuestro conjunto de datos de la Premier League ($N = 3,389$ partidos):

### A. El Peligro del Naive Split vs. Cross Validation Temporal
* **Enfoque Naive (Random Train-Test Split):** Si dividimos los datos aleatoriamente (ej: 80/20 sin considerar el tiempo), incurrimos en **Fuga Temporal (Temporal Leakage)**. En el fútbol, el rendimiento de un equipo en la jornada 30 depende de su historial en las jornadas 1 a 29. Un split aleatorio podría usar información del futuro para predecir el pasado, generando métricas de validación artificialmente infladas.
* **Solución de Cross-Validation Temporal:** Utilizamos `TimeSeriesSplit(n_splits=5)`. El modelo se evalúa de manera incremental:
  * **Split 1:** Entrena con la temporada $T_1$ y valida con $T_2$.
  * **Split 2:** Entrena con $\{T_1, T_2\}$ y valida con $T_3$.
  * ... y así sucesivamente.
  * **Resultado:** Garantizamos una evaluación de generalización real, evaluando siempre sobre "el futuro" relativo al conjunto de entrenamiento.

### B. El Dilema del Ajuste: Overfitting (Varianza) vs. Underfitting (Sesgo)
En la predicción de eventos deportivos, los datos tienen un alto **ruido aleatorio (error irreducible)** provocado por factores imprevistos (lesiones en el calentamiento, tarjetas rojas tempranas, decisiones arbitrales, rebotes fortuitos).

* **Subajuste (Underfitting / High Bias):** Ocurre si el modelo carece de flexibilidad para capturar patrones de rendimiento. 
  * *Ejemplo en nuestro proyecto:* Una Regresión Logística sin regularizar o con muy pocas variables predictivas que prediga el promedio general de victorias de local ($45\%$), sin discriminar el momento actual de los equipos.
  * *Diagnóstico:* Scores muy bajos tanto en el conjunto de entrenamiento como en el de validación.
* **Sobreajuste (Overfitting / High Variance):** Ocurre si el modelo memoriza el ruido aleatorio e histórico en lugar de aprender la tendencia general.
  * *Ejemplo en nuestro proyecto:* Una Red Neuronal profunda entrenada por demasiadas épocas sin regularización que memorice que "siempre que el árbitro X dirige un lunes lluvioso a las 20:00, gana el equipo visitante".
  * *Diagnóstico:* Un score de entrenamiento cercano al $100\%$ pero un rendimiento paupérrimo en el conjunto de validación.
* **Trade-off y Regularización:** Controlamos este balance aplicando penalizaciones estrictas en cada modelo.

### C. Validation Curve (Curva de Validación) en BetAnalytics
* **Aplicación:** Si graficamos la complejidad del modelo (por ejemplo, el parámetro `max_depth` de Random Forest) frente a la exactitud obtenida:
  * Con `max_depth` muy bajo ($2$ a $3$): El modelo subajusta (tanto train como validation score son bajos, alrededor de $69.2\% - 69.7\%$, debido a un sesgo alto).
  * Con `max_depth` óptimo ($7$): Se alcanza el punto óptimo del trade-off donde el score de validación (test) alcanza su máximo de **$70.07\%$**.
  * Con `max_depth` muy alto ($>10$): El score de train sigue subiendo hacia el $94.79\%$, pero el score de validación decae y se estanca en $69.4\%$ (el modelo se sobreajusta y memoriza el ruido).
* **Decisión:** Los hiperparámetros elegidos para producción representan el **vértice óptimo de la curva de validación**, maximizando la generalización sobre datos no vistos.

![Curva de Validación: Rendimiento vs. Complejidad](file:///c:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/21_Curva_Validacion_Complejidad.png)

### D. Learning Curve (Curva de Aprendizaje) y la Convergencia de Datos
* **Comportamiento:** Grafica el rendimiento del modelo a medida que aumentamos el número de partidos de entrenamiento.
  * Con pocos partidos de entrenamiento ($N \approx 169$), el modelo tiene alta varianza: el score de entrenamiento es muy alto ($92.16\%$) pero el de validación es bajo ($68.79\%$).
  * Al aumentar los datos de entrenamiento a $1,697$ partidos (promedio por split), el score de entrenamiento disminuye y el de validación aumenta, convergiendo progresivamente.
* **Diagnóstico de BetAnalytics:** Con nuestro dataset histórico sanitizado, las curvas de aprendizaje entran en la **zona de convergencia** (estabilizándose en torno al $70\%$).
  * *Implicancia clave:* Añadir más datos históricos antiguos (de ligas de hace 15 o 20 años) no mejoraría el ajuste (el fútbol táctico ha cambiado y actuaría como ruido).
  * *Estrategia de Mejora:* En lugar de recopilar más volumen de datos horizontales ($N$), la única forma de elevar la asíntota de rendimiento es mediante la **Ingeniería de Características (Feature Engineering)**, es decir, aumentando la complejidad predictiva de las variables (métricas de Expected Goals, cuotas implícitas de casas de apuestas y ratings dinámicos de rendimiento).

![Curva de Aprendizaje: Rendimiento vs. Volumen de Datos](file:///c:/Users/sergi/Desktop/datascience/Carpeta_Presentacion/22_Curva_Aprendizaje_Convergencia.png)
