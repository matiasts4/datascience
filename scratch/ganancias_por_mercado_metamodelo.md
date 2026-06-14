# Analisis de Desempeño y Ganancias por Mercado del Meta-Modelo

Este reporte desglosa los resultados financieros de la simulación de segunda capa, agrupados por mercado de apuestas, para evaluar dónde genera mayor valor el Meta-Modelo.

## Meta-Modelo: Random Forest (Sistema Dual)

| Mercado | Apuestas Candidatas | Apuestas Colocadas | Evitadas (Falsos Positivos) | Ganadas | Perdidas | ROI Neto | Ganancia Neta (USD) | Tasa de Acierto |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1X2 (Home/Draw/Away) | 1494 | 397 | 1097 | 117 | 280 | 14.16% | $562.20 | 29.47% |
| Double Chance 1X | 37 | 21 | 16 | 14 | 7 | -1.43% | $-3.00 | 66.67% |
| Double Chance X2 | 67 | 42 | 25 | 29 | 13 | 6.50% | $27.31 | 69.05% |
| Over 2.5 Goals | 295 | 222 | 73 | 121 | 101 | 1.62% | $35.90 | 54.50% |
| Under 2.5 Goals | 333 | 153 | 180 | 82 | 71 | 5.84% | $89.40 | 53.59% |
| **TOTAL PORTAFOLIO** | **2226** | **835** | **1391** | **363** | **472** | **8.52%** | **$711.82** | **43.47%** |

## Meta-Modelo: Logistic Regression (Sistema Dual)

| Mercado | Apuestas Candidatas | Apuestas Colocadas | Evitadas (Falsos Positivos) | Ganadas | Perdidas | ROI Neto | Ganancia Neta (USD) | Tasa de Acierto |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1X2 (Home/Draw/Away) | 1494 | 371 | 1123 | 101 | 270 | 14.42% | $534.80 | 27.22% |
| Double Chance 1X | 37 | 17 | 20 | 11 | 6 | -10.72% | $-18.22 | 64.71% |
| Double Chance X2 | 67 | 35 | 32 | 26 | 9 | 13.43% | $47.01 | 74.29% |
| Over 2.5 Goals | 295 | 238 | 57 | 132 | 106 | 4.60% | $109.50 | 55.46% |
| Under 2.5 Goals | 333 | 162 | 171 | 89 | 73 | 10.65% | $172.60 | 54.94% |
| **TOTAL PORTAFOLIO** | **2226** | **823** | **1403** | **359** | **464** | **10.28%** | **$845.69** | **43.62%** |

