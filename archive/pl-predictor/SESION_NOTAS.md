# 📋 Notas de Sesión — PL Predictor Optimizer
**Fecha:** 2026-03-25 | **Última pausa:** 21:55 UTC-3

---

## ✅ Lo que se hizo en esta sesión

### 1. Corrección Crítica de Features (Bug Fix)
- Se detectó que los modelos `.pkl` esperaban **17 features** pero el pipeline enviaba **23**.
- **Solución:** Se actualizó `src/config.py` para usar exactamente las 17 features con las que se entrenaron los modelos:
  ```
  home_elo, away_elo,
  h_l5_pts, h_l5_sh, h_l5_sot, h_l5_sot_c, h_l5_gf, h_l5_ga, h_l5_fls,
  a_l5_pts, a_l5_sh, a_l5_sot, a_l5_sot_c, a_l5_gf, a_l5_ga, a_l5_fls,
  referee_avg_cards_history
  ```
- Se re-ejecutó `optimize_ml_models.py` guardando también el `models/scaler.pkl` sincronizado.

### 2. Mejora del Selector (`src/models/selector.py`)
- Ahora incluye el campo `Pick` en las predicciones:
  - Para 1X2: retorna la clase predicha (2=Home, 1=Draw, 0=Away)
  - Para mercados binarios: retorna `1` (positivo)

### 3. Análisis por Mercado (últimos 1000 partidos)
| Mercado | Acierto | Apuestas |
|---|---|---|
| **Over 2.5 Goals** | **68.67%** ⭐ | 482 |
| BTTS (Ambos Marcan) | 65.73% | 213 |
| 1X2 (Ganador) | 64.79% | 443 |

### 4. Simulación Inicial (Over 2.5 Goals, 2% vig, $1000)
- **Bankroll Final:** $1,982.46 (+$982.46 de beneficio, ROI 10.19%)

---

## 🔁 Tarea en Curso (PAUSADA)

### `strategy_optimizer.py` → Buscando la mejor configuración
**Estado al pausar:** ~150/2640 simulaciones completadas  
**Mejor beneficio encontrado hasta il momento:** +$2,666 (de $1,000 iniciales)

El script sigue corriendo en el terminal. **Cuando termine** guardará los resultados en:
```
c:\Users\PC\DataScience\archive\pl-predictor\strategy_optimization_results.csv
```

**Parámetros que está explorando:**
- Umbral de confianza: `[50%, 52%, 55%, 57%, 60%, 62%, 65%, 70%]`
- Stake flat: `[$10, $15, $20, $25, $30, $50]`
- Fracción Kelly: `[3%, 5%, 7%, 10%, 15%]`
- Vig bookmaker: `[85%, 90%, 95%, 98%, 100%]`
- Cuota mínima: `[1.1, 1.2, 1.3, 1.4, 1.5, 1.6]`
- Estrategia: `[flat, kelly]`

---

## ⏭️ Próximos Pasos (para retomar)

1. **Verificar que terminó el optimizador:**
   ```powershell
   cat strategy_optimization_results.csv | head
   ```

2. **Leer la mejor configuración:**
   ```python
   import pandas as pd
   df = pd.read_csv('strategy_optimization_results.csv')
   print(df.head(5).to_string())
   ```

3. **Aplicar la configuración ganadora en el simulador:**
   - Actualizar `src/config.py` con `BEST_STRATEGY = { conf: ..., stake: ..., market: 'Over 2.5 Goals' }`
   - Modificar `src/backtester.py` para usar esos valores como defaults
   - Actualizar el endpoint `/api/simulate` en `src/api.py`

4. **Documentar en `walkthrough_simulator.md`** con los resultados finales

---

## 📁 Archivos Clave
| Archivo | Rol |
|---|---|
| `src/config.py` | Configuración global (17 features, rutas) |
| `src/models/selector.py` | Carga modelos PKL → predicciones con `Pick` |
| `src/backtester.py` | Motor de simulación / backtest |
| `src/api.py` | API Flask para el frontend |
| `models/optimized/*.pkl` | Modelos entrenados (1X2, O2.5, BTTS) |
| `models/scaler.pkl` | Scaler de 17 features (sincronizado con los .pkl) |
| `optimize_ml_models.py` | Re-entrena modelos y guarda scaler |
| `strategy_optimizer.py` | Búsqueda de hiperparámetros (2640 simulaciones) |
| `strategy_optimization_results.csv` | Resultados completos (se crea al terminar el optimizer) |
