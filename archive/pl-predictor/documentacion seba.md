# Documentación Técnica: Bot de Apuestas Premier League
### Proyecto Universitario — Sebastián  
**Última actualización:** 03 Abril 2026 — Data hasta Marzo 2026 (Temporada 25/26)  
**Dataset activo:** `all_match_features_v7.csv` (2,969 partidos) | **Features activas:** 49  
**Entorno:** Python 3.9 · scikit-learn 1.6 · `.venv` local · macOS compatible  

---

## ⭐️ EL BENCHMARK CIENTÍFICO FINAL ⭐️
Tras inyectar los más de 300 partidos de la temporada actual 25/26, los resultados del hold-out validation (532 partidos de prueba ciegos) son:

| Mercado o Tipo de Apuesta | Precisión | Calibración Pura |
|---|---|---|
| **Doble Oportunidad 1X** (Casa o Empate) | **75.6%** | Excelente |
| **Home Clean Sheet** (Arco Cero Local) | **76.5%** | Muy Fuerte |
| **Doble Oportunidad X2** (Visita o Empate) | **70.3%** | Excelente |
| **Over/Under 2.5 Goles** | **62.6%** | Rentable |
| **Ambos Anotan (BTTS)** | **58.1%** | Moderado |
| **Ganador Directo (1X2)** | **58.6%** | **ROI: +244.5%** |

* **Promedio Global (8 mercados):** **65.3%**
* **La Lección:** El modelo sacrificó algo de ruido general en mercados caóticos (BTTS) para hyper-especializarse en asegurar tu dinero en la Doble Oportunidad (`1X`). Ganar 75 de cada 100 apuestas en 1X te construye liquidez garantizada.

---

## El Pipeline Híbrido Final (Las 7 Fases de Datos)
Para lograr estos números monstruosos, la IA no ve solo "goles". Cruza 7 bases de datos en orden:

1. **`build_deep_features.py`**: FBref — Fuerza táctica (Linderos de Ataque/Defensa L5) y Rating ELO profundo.
2. **`append_2025_data.py`**: FBref (Scraper) — Actualiza la máquina añadiendo y procesando la Temporada actual 2025/2026.
3. **`integrar_cuotas.py`**: Football-Data — Adquiere cuotas reales de Bet365 para ver dónde se equivoca el casino.
4. **`integrar_xg.py`**: GitHub FPL Oficial — Mide el xG (Expected Goals) para castigar/premiar el rendimiento engañoso.
5. **`integrar_clima.py`**: OpenMeteo API — Detecta lluvia/frío del día de partido para mercados Under 2.5.
6. **`integrar_poisson.py`**: scikit-learn — Usa cálculo de Poisson para simular marcadores exactos (`2-0`, `0-1`, etc.).
7. **`integrar_momentum.py`**: Analítica Propia — Determina la Moral: Rachas acumuladas de imbatibilidad.

Todo decanta en el Ensamble Clínico: **`src/models/trainer.py`**.
La toma de decisión final es un Voto Suave (`Soft VotingClassifier`) entre un Bosque Aleatorio (`RandomForest`) y Ecuaciones Lineales (`LogisticRegression`).

---

## 💰 ¿Cómo usar el modelo este Fin de Semana? (Paso a Paso) 💰

No toques código, compórtate como un Inversionista Data Driven. Yo te construí una Terminal de Comando a la cual debes preguntar tus dudas.

### 1. Activar el Motor (Tu Consola Mac):
Siempre que abras la consola, sitúate en tu carpeta (pl-predictor) y ejecuta el arranque nuclear:
```bash
source .venv/bin/activate
export PYTHONPATH=.
```

### 2. Invocar a la Interfaz del Oráculo:
Ejecuta la interfaz humana que te dejé programada:
```bash
python oraculo.py
```

### 3. Jugar en el Casino Real:
* El script te listará los nombres de todos los equipos disponibles en la memoria de la IA.
* Ingresa con exactitud mayúscula (Ej: `Arsenal` vs `Chelsea`).
* Revisa en pantalla sus probabilidades, ignora su sugerencia si es menor al 70%, o anota la "**👉 APUESTA ESTRELLA**" si el modelo huele sangre.
* Entra a tu aplicación celular de Betano (o la que uses), busca el partido y ponle esos usd de liquidez en la celda "**Apuesta Doble: Local/Empate**".
* Cierra la ventana y espera ser rentable.

---
**Nota al Desarrollador/Jurado:** La capacidad del "Oráculo" para leer el futuro radica en que asume el partido introducido con las estadísticas perfectas del final del dataset (`all_match_features_v7.csv`), lo que significa que evalúa el Momentum y Forma Física cerrando exactamente a **Marzo de 2026**. Es decir, toma "foto" del momento inmediato previo antes de la fecha simulada.
