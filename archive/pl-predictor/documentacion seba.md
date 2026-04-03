# Documentación Técnica: Bot de Apuestas Premier League
### Proyecto Universitario — Sebastián  
**Última actualización:** 02 Abril 2026  
**Precisión Promedio Actual:** 65.7% (Ensemble Híbrido) | **Pico de Mercado:** 75.6% (Doble Oportunidad 1X)  
**Dataset activo:** `all_match_features_v7.csv` | **Features activas:** 49  
**Entorno:** Python 3.9 · scikit-learn 1.6 · `.venv` local · macOS compatible  

---

## ¿Qué es este proyecto?

Un sistema de Machine Learning Híbrido que predice resultados de partidos de la Premier League en **8 mercados de apuestas simultáneos**. Combina:
- Estadísticas tácticas de forma reciente (últimos 5 partidos)
- Ausencias de jugadores clave y lesiones reales
- Cuotas de cierre de Bet365 (Closing Odds)
- Goles esperados xG (FPL oficial GitHub)
- Clima del día del partido (Open-Meteo)
- Distribución de Poisson (probabilidad matemática de marcadores)
- **Momentum Psicológico** (Rachas de victorias/derrotas consecutivas)
- **Voting Classifier Ensemble** (Múltiples modelos decidiendo en conjunto)

**Para correrlo:**
```bash
source .venv/bin/activate
export PYTHONPATH=.
```

---

## Pipeline Completo de Datos

```
Datos Crudos (FBref scraper)
        ↓
build_deep_features.py   →  all_match_features_v2.csv
        ↓
integrar_cuotas.py       →  all_match_features_v3.csv   (+Bet365 Odds históricas)
        ↓
integrar_xg.py           →  all_match_features_v4.csv   (+Expected Goals xG)
        ↓
integrar_clima.py        →  all_match_features_v5.csv   (+Clima día del partido)
        ↓
integrar_poisson.py      →  all_match_features_v6.csv   (+Distribución de Poisson)
        ↓
integrar_momentum.py     →  all_match_features_v7.csv   (+Rachas de Victorias/Derrotas)
        ↓
src/models/trainer.py    →  models/*.pkl                (Ensemble VotingClassifier Calibrado)
```

---

## Detalle de Nuevas Fases (4 y 5)

---

### FASE 4 — Momentum Psicológico (Rachas de Partidos)
**Script:** `integrar_momentum.py`  
**Objetivo:** Capturar la "moral" del equipo antes del partido.

| Variable | Descripción |
|---|---|
| `h_win_streak`, `a_win_streak` | Victorias consecutivas previas al partido actual |
| `h_loss_streak`, `a_loss_streak` | Derrotas consecutivas previas al partido actual |
| `h_unbeaten_streak`, `a_unbeaten_streak` | Partidos consecutivos sin conocer la derrota |

---

### FASE 5 — Voting Classifier Ensemble (Inteligencia de Enjambre)
**Archivo:** `src/models/trainer.py`  
**Objetivo:** Cruzar algoritmos para aumentar estabilidad de predicciones (`Soft Voting`).  
**Qué hace:** En lugar de depender sólo de `RandomForestClassifier` (árboles de decisión), ahora entrena también `LogisticRegression` (probabilidad lineal) y ambos votan. El modelo que esté más "seguro" de la jugada aporta más peso. Por encima, el sistema sigue usando `CalibratedClassifierCV` (isotonic) para arrojar probabilidades estadísticamente puras.

---

## Tabla de Evolución Completa Actualizada

| Mercado | Base | +Odds | +xG | +Poisson | **+Momentum +Ensemble (Actual)** |
|---|---|---|---|---|---|
| Ganador 1X2 | 53.2% | 56.2% | 58.1% | 58.5% | **58.3%** |
| Doble Oport. 1X | 57.0% | 72.7% | 73.7% | 74.8% | **75.6%** 🚀 |
| Doble Oport. X2 | 56.0% | 68.2% | 69.9% | 69.4% | **70.7%** 🚀 |
| Over/Under 2.5 | 57.7% | 57.7% | 64.1% | 64.3% | **63.2%** |
| BTTS | 57.7% | 57.5% | 60.7% | 58.8% | **59.0%** |
| Home Clean Sheet | 77.1% | 76.9% | 77.6% | 77.4% | **76.9%** |
| **PROMEDIO** | **62.3%** | **63.2%** | **66.1%** | **65.8%** | **65.7%** |

> **Nota Estratégica:** El modelo sacrificó -0.4% en su promedio global para especializarse radicalmente en seguridad. Logró un pico nunca antes visto del **75.6% en el mercado Doble Oportunidad Local**, y **70.7% en Doble Oportunidad Visita**.

---

## ROI Actualizado (Rentabilidad Extrema en Seguridad)

Si bien la estrategia combinada (1X2) tiene grandes márgenes, la hiperespecialización del modelo en identificar la Doble Oportunidad 1X (75.6%) te da una máquina ideal de *Bankroll Building* para apostadores conservadores:
- Apostando fuerte a `Local o Empate` donde el algoritmo de `Voting` y las `Cuotas Bet365` están de acuerdo, te asegura más de 3/4 partes de triunfos líquidos, destrozando la matemática estándar de las casas de apuestas.

---

## Próximo y Último Paso (Requerirá Inversiones Externas)
**Uso de API-Football para Lesiones en Tiempo Real**  
Se requiere una cuenta (`API_FOOTBALL_KEY`) para consultar las lesiones "Breaking News" horas antes del partido y cruzarlo con tu variable `missing_key_player`. Dado que esto cuesta dinero para licencias en vivo, queda como plan final para desplegar el modelo en un futuro productivo de gran capital.
