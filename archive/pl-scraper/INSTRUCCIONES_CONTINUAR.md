# Instrucciones para Continuar el Scraping

Este documento describe el estado exacto en el que se detuvo el scraper y los pasos necesarios para reanudar el trabajo desde otro equipo. El objetivo es que todas las temporadas (2017 a 2024, incluyendo 21/22) queden exactamente iguales, es decir, con las extracciones de **Alineaciones (Lineups)**, **Eventos (Events)**, **Tiros (Shots)** y las **6 Estadísticas de Jugadores (Player Stats)** completadas.

---

## 🛑 1. Estado Actual (Marzo 2026)

Se avanzó significativamente. Las temporadas más pesadas ya descargaron todos sus datos partido a partido. Aquí está el progreso exacto:

| Temporada | Alineaciones | Eventos | Tiros (Shots) | Stats Jugadores | Estado General |
|-----------|--------------|---------|----------------|-----------------|----------------|
| **2024** | 380/380 | 380/380 | 380/380 | 2 de 6 | ✅ Partidos Completos |
| **21/22** | 373/380 | 380/380 | 380/380 | 0 de 6 | ✅ Partidos Completos |
| **2023** | 380/380 | 380/380 | 380/380 | 2 de 6 | ✅ Partidos Completos |
| **2022** | 380/380 | 380/380 | 380/380 | 2 de 6 | ✅ Partidos Completos |
| **2020** | 380/380 | 380/380 | 380/380 | 2 de 6 | ✅ Partidos Completos |
| **2019** | 380/380 | 380/380 | 380/380 | 2 de 6 | ✅ Partidos Completos |
| **2018** | 380/380 | 380/380 | **66/380** | 1 de 6 | ⏳ **EN PROGRESO** (Faltan tiros) |
| **2017** | 380/380 | 380/380 | **0/380** | 1 de 6 | ⏳ **PENDIENTE** (Faltan tiros) |

### ¿Qué falta para igualar todas las temporadas?
1. **Tiros (Shots):** Solo restan descargar los datos de tiros de los partidos de la temporada **2018** (faltan ~314 partidos) y la **2017** (faltan 380 partidos).
2. **Estadísticas Generales:** A casi todas las temporadas les faltan 4 o 6 categorías (Passing, Defense, Possession, Misc, etc.). Estas descargas son a nivel de temporada entera, no partido a partido, por lo que tardarán solo un par de minutos por temporada en completarse.

---

## 🚀 2. Cómo Continuar en el Nuevo Equipo

Todo el sistema de estados está sincronizado. Al llevarte este repositorio al nuevo equipo, el scraper sabrá **exactamente** dónde retomar gracias a los archivos `checkpoint_<season>.json`.

**Pasos a seguir:**

1. Clona/actualiza el repositorio en el nuevo equipo.
2. Activa el entorno virtual e instala dependencias:
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Ejecuta el script automatizado (puedes dejarlo corriendo de fondo usando `nohup` o en una sesión de `tmux`):
   ```bash
   python run_all_seasons.py
   ```

El script revisará automáticamente el orden de prioridades, detectará que 21/22, 2024, etc., ya no necesitan descargas de partidos, e irá directamente a continuar descargando los **tiros de 2018**.

*Nota: Para monitorear el progreso mientras corre en el otro equipo, puedes ejecutar en otra terminal `python status.py`.*
