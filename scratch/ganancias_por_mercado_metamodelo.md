# Análisis de Desempeño y Ganancias por Mercado del Meta-Modelo

Este reporte desglosa los resultados financieros de la simulación de segunda capa, agrupados por mercado de apuestas, para evaluar dónde genera mayor valor el Meta-Modelo.

## Meta-Modelo: SVM (Sistema Dual)

| Mercado | Apuestas Candidatas | Apuestas Colocadas | Evitadas (Falsos Positivos) | Ganadas | Perdidas | ROI Neto | Ganancia Neta (USD) | Tasa de Acierto |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1X2 (Home/Draw/Away) | 1603 | 399 | 1204 | 97 | 302 | 9.05% | $361.20 | 24.31% |
| Double Chance 1X | 19 | 6 | 13 | 4 | 2 | 11.19% | $6.72 | 66.67% |
| Double Chance X2 | 77 | 15 | 62 | 9 | 6 | -12.91% | $-19.36 | 60.00% |
| Over 2.5 Goals | 227 | 46 | 181 | 27 | 19 | 13.24% | $60.90 | 58.70% |
| Under 2.5 Goals | 288 | 36 | 252 | 17 | 19 | 15.06% | $54.20 | 47.22% |
| **TOTAL PORTAFOLIO** | **2214** | **502** | **1712** | **154** | **348** | **9.24%** | **$463.66** | **30.68%** |

## Meta-Modelo: Random Forest (Sistema Dual)

| Mercado | Apuestas Candidatas | Apuestas Colocadas | Evitadas (Falsos Positivos) | Ganadas | Perdidas | ROI Neto | Ganancia Neta (USD) | Tasa de Acierto |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1X2 (Home/Draw/Away) | 1603 | 444 | 1159 | 122 | 322 | 8.16% | $362.30 | 27.48% |
| Double Chance 1X | 19 | 12 | 7 | 7 | 5 | -14.14% | $-16.97 | 58.33% |
| Double Chance X2 | 77 | 39 | 38 | 25 | 14 | -2.79% | $-10.89 | 64.10% |
| Over 2.5 Goals | 227 | 183 | 44 | 93 | 90 | -5.09% | $-93.10 | 50.82% |
| Under 2.5 Goals | 288 | 94 | 194 | 59 | 35 | 22.11% | $207.80 | 62.77% |
| **TOTAL PORTAFOLIO** | **2214** | **772** | **1442** | **306** | **466** | **5.82%** | **$449.14** | **39.64%** |

## Meta-Modelo: Logistic Regression (Sistema Dual)

| Mercado | Apuestas Candidatas | Apuestas Colocadas | Evitadas (Falsos Positivos) | Ganadas | Perdidas | ROI Neto | Ganancia Neta (USD) | Tasa de Acierto |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1X2 (Home/Draw/Away) | 1603 | 405 | 1198 | 100 | 305 | 8.85% | $358.40 | 24.69% |
| Double Chance 1X | 19 | 13 | 6 | 7 | 6 | -20.75% | $-26.97 | 53.85% |
| Double Chance X2 | 77 | 24 | 53 | 16 | 8 | -8.29% | $-19.89 | 66.67% |
| Over 2.5 Goals | 227 | 162 | 65 | 83 | 79 | -3.81% | $-61.80 | 51.23% |
| Under 2.5 Goals | 288 | 122 | 166 | 64 | 58 | 7.35% | $89.70 | 52.46% |
| **TOTAL PORTAFOLIO** | **2214** | **726** | **1488** | **270** | **456** | **4.68%** | **$339.44** | **37.19%** |

