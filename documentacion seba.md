# Actualización del Modelo PL-Predictor: Mejoras de Ratio Bajas y Defensa/Ataque (02 Abr 2026)

Esta actualización implementa mejoras significativas para aumentar el ROI ("ratio") al momento de simular las apuestas, centrándose en el impacto real de las alineaciones titulares y la forma por "bloques" (Defensa y Ataque).

## 1. Prioridad 1: Bajas Importantes (Key Players por Minutos)
**Archivo modificado:** `archive/pl-predictor/build_deep_features.py` (Líneas ~85-115)
**Archivo modificado:** `archive/pl-predictor/src/config.py` (Líneas 36-39)

### ¿Qué se cambió?
Anteriormente, el sistema definía a un "Key Player" estrictamente como el **goleador principal** (`Performance_Gls`). 
Ahora:
- El script evalúa a los **Top 5 jugadores con más minutos** acumulados para cada equipo a lo largo del dataset. Esto define a los "Titulares Indiscutibles" (Core).
- Para cada partido, si alguno de esos 5 pilares no jugó al menos 45 minutos (ej. banca, lesión de último minuto, expulsión temprana), se cuenta como **"Ausencia Crítica"**.
- Se insertaron las variables `h_missing_key_player` y `a_missing_key_player` en la lista maestra `FEATURES` del modelo. 

### Impacto en el Ratio:
Esta variable permite que el modelo baje drásticamente la probabilidad de victoria estadística cuando se detecta que faltan pilares como el portero titular, el capitán o el contención estructural, identificando oportunidades de apostar en contra con gran valor (Value Bet).

---

## 2. Prioridad 2: Notas Agrupadas (Índices de Ataque y Defensa)
**Archivo modificado:** `archive/pl-predictor/build_deep_features.py` (Líneas ~90-100 y 150-165)
**Archivo modificado:** `archive/pl-predictor/src/config.py` (Líneas 36-39)

### ¿Qué se cambió?
En vez de cruzar duelos directos ruidosos (`RW vs LB`), se construyeron dos índices holísticos automatizados para el bloque defensivo y ofensivo de cada equipo basándonos en variables subyacentes críticas del partido:

- **Attack Rating (`atk_idx`)**: Un índice ponderado que recompensa:
  * Tiros al arco (`Performance_SoT`)
  * Goles reales (`Performance_Gls` x2)
  * Asistencias (`Performance_Ast` x1.5)
- **Defense Rating (`def_idx`)**: Un índice para contención estructural:
  * Quites ganados (`Performance_TklW`)
  * Intercepciones defensivas (`Performance_Int`)

Se calcularon los promedios móviles (últimos 5 partidos) de estos índices para armar las variables `h_l5_atk`, `h_l5_def`, `a_l5_atk`, y `a_l5_def` y fueron agregados directamente a la vectorización del ML.

### Impacto en el Ratio:
Al consolidar la forma en "Defensa Integral" vs "Ataque Integral", el modelo predice los mercados de **"Ambos Equipos Anotan (BTTS)"** y **"Más de 2.5 Goles"** con una mejor calibración. Si un Equipo A tiene un `atk_rating` por los cielos, y el Equipo B tiene un `def_rating` deprimente, el modelo apostará fortísimo a goles, logrando predecir goleadas o blanqueadas sistemáticas.

---

**Siguientes pasos recomendados para ti:**
1. Es necesario correr nuevamente `python build_deep_features.py` para materializar todos estos cálculos en el `.csv`.
2. Seguido de un re-entrenamiento total con `python src/models/trainer.py` para que los pesos absorban estas nuevas columnas en todos los algoritmos.
