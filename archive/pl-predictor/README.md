# Premier League Betting Predictor — Motor de Predicción (Backend)

Sistema avanzado de predicción de apuestas para la Premier League usando Machine Learning. Predice simultáneamente 16 tipos de mercados por partido y recomienda la apuesta con mayor probabilidad estadística de éxito.

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.10+
- Dependencias: `pip install -r requirements.txt` *(o paquetes listados abajo)*

### Paquetes necesarios
```bash
pip install flask flask-cors pandas numpy scikit-learn joblib xgboost lightgbm
```

---

## ▶️ Comandos de Ejecución

### 1. Levantar el Servidor API (Backend)
Siempre ejecutar **desde la carpeta `pl-predictor/`**:
```bash
python -m src.api
```
El servidor quedará disponible en `http://localhost:5000`.

---

### 2. Re-entrenar los Modelos ML
Si tienes datos nuevos o quieres mejorar el modelo:
```bash
# Paso 1: Construir features avanzados desde los CSVs históricos
python build_deep_features.py

# Paso 2: Entrenar con GridSearch (puede tardar ~10-30 min)
python src/models/trainer.py
```
Los modelos se guardan automáticamente en `models/`.

---

### 3. Evaluar Precisión de los Modelos (Holdout Test)
Testea la calibración sobre el 20% de datos que el modelo no vio durante el entrenamiento:
```bash
python evaluate_improvement.py
```
Imprime la Accuracy y Brier Score por cada mercado.

---

### 4. Test de Estrategia — Mejor Apuesta por Probabilidad Absoluta
Verifica qué porcentaje de acierto obtiene el selector al elegir siempre la apuesta de mayor probabilidad en los últimos 988 partidos:
```bash
python test_accuracy.py
```

---

### 5. Optimización de Parámetros del Simulador (Grid Search)
Prueba 432 combinaciones de estrategia, cuota mínima, fracción de apuesta y temporada para encontrar la configuración más rentable:
```bash
python optimizer_fast.py
```
Genera un ranking y guarda todos los resultados en `optimization_results.csv`.

---

### 6. Predecir Próximos Partidos desde Consola
```bash
python predict_best_bets.py
```

---

## 🗂 Estructura de Carpetas

```
pl-predictor/
├── data/historical/          # CSVs históricos de partidos
├── models/                   # Modelos .pkl entrenados + scaler.pkl
├── src/
│   ├── api.py                # Servidor Flask con todos los endpoints REST
│   ├── backtester.py         # Simulación financiera cronológica
│   ├── config.py             # Constantes globales (targets, features, paths)
│   ├── upcoming.py           # Scraping de partidos futuros desde FBref
│   └── models/
│       ├── trainer.py        # Entrenamiento y GridSearch
│       └── selector.py       # Inferencia multi-modelo (MasterBetSelector)
├── build_deep_features.py    # Pipeline de feature engineering avanzado
├── evaluate_improvement.py   # Evaluación de calibración del modelo
├── test_accuracy.py          # Test de winrate con estrategia de prob. absoluta
├── optimizer_fast.py         # Grid search para encontrar la mejor configuración
└── predict_best_bets.py      # CLI para predicción de próximos partidos
```

---

## 🌐 Endpoints de la API

| Método | Ruta                       | Descripción                                      |
|--------|----------------------------|--------------------------------------------------|
| GET    | `/api/stats`               | Métricas generales del modelo                    |
| GET    | `/api/teams`               | Ranking de equipos con Elo y forma               |
| GET    | `/api/matches/upcoming`    | Partidos programados con predicciones            |
| GET    | `/api/performance`         | Resultados del backtest financiero               |
| GET    | `/api/detailed-history`    | Historial detallado con los 16 mercados          |
| POST   | `/api/predict`             | Predice un partido específico (equipo, fecha)    |
| POST   | `/api/simulate`            | Simulación interactiva del portafolio de apuestas|

---

## 📈 Mercados Activos (8 Mercados — EV Potencialmente Positivo)

Estos son los mercados donde la cuota esperada del corredor (≥1.50) puede superar el margen de error del modelo:

| Mercado                             | Accuracy Aprox. | Cuota Implícita | Razonamiento                               |
|-------------------------------------|-----------------|-----------------|--------------------------------------------|
| 1X2 (Match Winner)                  | ~56%            | 2.00 - 5.00     | Alta variáncia pero potencial de ganancia real |
| Double Chance 1X (Local o Empate)   | ~70%            | 1.30 - 1.60     | Doble cobertura reduce riesgo              |
| Double Chance X2 (Visita o Empate)  | ~68%            | 1.30 - 1.60     | Doble cobertura reduce riesgo              |
| Over 2.5 Goals                      | ~57%            | 1.70 - 2.00     | Mercado líquido, odds reales razonables    |
| Under 2.5 Goals                     | ~62%            | 1.70 - 2.00     | Mercado líquido, Under tiene mejor accuracy|
| BTTS (Ambos Anotan)                 | ~54%            | 1.70 - 2.00     | Complementario a Over 2.5 Goals           |
| BTTS - No                           | ~58%            | 1.70 - 2.00     | Mayor accuracy que BTTS, potencial edge    |
| Home Clean Sheet                    | ~67%            | 2.00 - 3.50     | Alta cuota, accuracy considerable          |

---

## ❌ Mercados Eliminados (8 Mercados — EV Estructuralmente Negativo)

Estos mercados fueron removidos de `src/config.py` porque incluso con alta accuracy, **la cuota del corredor es demasiado baja** para recuperar las apuestas perdidas:

| Mercado                              | Razón de Eliminación                                          |
|--------------------------------------|---------------------------------------------------------------|
| Home Team Over 0.5 Goals             | Accuracy ~88% pero cuota implícita ~1.10. EV ≈ **-5%**       |
| Away Team Over 0.5 Goals             | Accuracy ~82% pero cuota implícita ~1.15. EV ≈ **-5%**       |
| Over 22.5 Fouls                      | Accuracy ~58%, cuota ~1.55. EV ≈ **-10%**                    |
| Under 22.5 Fouls                     | Accuracy ~60%, cuota ~1.55. EV ≈ **-7%**                     |
| Over 4.5 Cards                       | Evento raro (~35% partidos), modelo sin ventaja real          |
| Under 4.5 Cards                      | Demasiado frecuente; odds ~1.30. EV siempre negativo          |
| Away Clean Sheet                     | Baja frecuencia, alta varianza. Accuracy inconsistente        |
| Home Win to Nil                      | Evento compuesto (<25%). Alta varianza, bajo EV              |
