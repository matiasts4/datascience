# Comparativa de Algoritmos para el Meta-Modelo (Meta-Labeling)

Este reporte compara el desempeño de las 4 opciones de algoritmos evaluados para actuar como Meta-Modelo.

## Solo Meta-Modelo

| Algoritmo Meta-Modelo | Banca Final | ROI | Apuestas | Evitadas (Falsos Positivos) | Max Drawdown |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Random Forest | $1823.62 | 9.96% | 827 | 1433 | 19.23% |
| Logistic Regression | $1880.89 | 10.77% | 818 | 1442 | 19.23% |
| SVM | $1528.37 | 9.68% | 546 | 1714 | 19.23% |
| XGBoost | $1671.38 | 7.42% | 905 | 1355 | 19.23% |

## Sistema Dual (EV + Meta)

| Algoritmo Meta-Modelo | Banca Final | ROI | Apuestas | Evitadas (Falsos Positivos) | Max Drawdown |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Random Forest | $1711.82 | 8.52% | 835 | 1391 | 19.23% |
| Logistic Regression | $1845.69 | 10.28% | 823 | 1403 | 19.23% |
| SVM | $1562.37 | 10.32% | 545 | 1681 | 19.23% |
| XGBoost | $1415.64 | 4.50% | 924 | 1302 | 19.91% |

