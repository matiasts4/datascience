# Comparativa de Algoritmos para el Meta-Modelo (Meta-Labeling)

Este reporte compara el desempeño de las 4 opciones de algoritmos evaluados para actuar como Meta-Modelo.

## Solo Meta-Modelo

| Algoritmo Meta-Modelo | Banca Final | ROI | Apuestas | Evitadas (Falsos Positivos) | Max Drawdown |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Random Forest | $1396.64 | 5.05% | 786 | 1472 | 24.91% |
| Logistic Regression | $1352.14 | 4.87% | 723 | 1535 | 24.91% |
| SVM | $1467.56 | 9.74% | 480 | 1778 | 24.91% |
| XGBoost | $817.92 | -2.05% | 887 | 1371 | 48.39% |

## Sistema Dual (EV + Meta)

| Algoritmo Meta-Modelo | Banca Final | ROI | Apuestas | Evitadas (Falsos Positivos) | Max Drawdown |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Random Forest | $1449.14 | 5.82% | 772 | 1442 | 24.91% |
| Logistic Regression | $1339.44 | 4.68% | 726 | 1488 | 24.91% |
| SVM | $1463.66 | 9.24% | 502 | 1712 | 24.91% |
| XGBoost | $1076.64 | 0.88% | 874 | 1340 | 32.86% |

