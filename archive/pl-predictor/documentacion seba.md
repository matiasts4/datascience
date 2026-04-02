# Documentación de Mejoras al Modelo de Predicción (Premier League)

A continuación, se documentan todos los cambios y refactorizaciones realizadas hasta el momento en el proyecto `pl-predictor` para aumentar el Retorno de Inversión (ROI) y la precisión global del bot. El promedio de precisión actual sobre los 8 mercados superó el 62.3% en Backtesting.

---

## 1. Prioridad 1: Sistema Avanzado de Bajas Notables (Key Players)
Se eliminó la restricción anticuada de medir la importancia de los jugadores solo por goles y asistencias. Se implementó una lógica de "Minutos Jugados" para detectar automáticamente a la columna vertebral del equipo (Titulares Indiscutidos). 
* Si un jugador clave no juega más de 45 minutos en el partido a predecir, se enciende una bandera roja matemática (`missing_key_player`).
* **Archivos modificados:** `build_deep_features.py` (Líneas 87-114).

## 2. Prioridad 2: Calificaciones Tácticas (Bloques de Ataque y Defensa)
Se descartaron los duelos individuales ruidosos (ej. LI vs ED). Las métricas se agruparon en bloques funcionales promediados en la ventana de los últimos 5 partidos.
* **Ataque (`atk_rating`):** Promedio de tiros a puerta (`sot`), goles a favor (`gf`) y peligrosidad ofensiva.
* **Defensa (`def_rating`):** Robustez calculada mitigando goles en contra (`ga`), faltas y cortes.
* **Archivos modificados:** `build_deep_features.py` (Líneas 147-163).
* **Nuevas Variables:** `h_l5_atk`, `h_l5_def`, `a_l5_atk`, `a_l5_def` agregadas al modelo en `src/config.py` y pasadas en `src/api.py`.

## 3. Prioridad 3: Ventaja de Estadio y Paternidad (Head-to-Head)
Basado en que factores como "United históricamente gana en casa" no pueden ser ignorados en fútbol.
* **Fortaleza Local (`team_home_win_pct` y `team_away_win_pct`):** Calcula dinámicamente la verdadera tasa de éxito del equipo cuando juega en ese estadio específico.
* **Paternidad Histórica (`h2h_home_pts_avg`):** Extrae el promedio histórico de puntos logrados por la localía en ese enfrentamiento directo en específico (ej. Arsenal vs Bournemouth en el Emirates), otorgando un altísimo peso extra al resultado 1X2.
* **Archivos modificados:** `build_deep_features.py` (Nueva función agregada antes de imputar NaNs), `src/config.py` y `src/backtester.py`.

## 4. Estabilidad de Entorno y Bugs de Machine Learning Corregidos
* **Entorno macOS:** Se removieron las dependencias conflictivas de sistemas Unix como `xgboost` y `lightgbm` en `src/models/trainer.py` debido a un problema con el compilador `libomp` en Mac. El modelo se apoya totalmente en ensamblaje asimétrico a través de la robustez de `RandomForestClassifier`.
* **Depreciación sklearn:** Se parcheó el pipeline de `optimizer_fast.py` y el entrenador `trainer.py`. Se reemplazó el obsoleto método Sigmoid que hacía crashear el motor por una función Isotónica pura (`method='isotonic'`).
* **Cache del Selector (`src/models/selector.py`):** Se re-orientó el lector dinámico de pickles (`.pkl`) para asegurar que consumiera estrictamente la versión en caliente de los modelos RandomForest re-entrenados, evitando iteraciones colgadas de sesiones pasadas.

---

**Actualización Fecha de Corte:** Marzo-Abril 2026.
**Precisión Media (8 mercados simultáneos):** ~ 62.3%
**Próximo Hito Propuesto:** Inyección de Consenso de Mercado (Market Closing Odds para Modelos Híbridos).
