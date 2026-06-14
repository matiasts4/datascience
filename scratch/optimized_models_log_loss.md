# Resultados de Log Loss y Accuracy de Validacion Cruzada Temporal (5 splits)

| Mercado | Modelo | Log Loss | Accuracy | Estado |
| :--- | :--- | :---: | :---: | :---: |
| 1X2 (Match Winner) | Logistic Regression (Elastic Net) | 0.99126 | 0.5284 | **GANADOR** |
| 1X2 (Match Winner) | Random Forest | 1.00046 | 0.5262 |  |
| 1X2 (Match Winner) | HistGradientBoosting (Early Stopping) | 1.01417 | 0.5209 |  |
| 1X2 (Match Winner) | XGBoost (L1/L2 Regularized) | 1.00273 | 0.5252 |  |
| 1X2 (Match Winner) | Neural Network (Dropout) | 1.07672 | 0.5135 |  |
| Double Chance 1X (Home or Draw) | Logistic Regression (Elastic Net) | 0.57341 | 0.7082 | **GANADOR** |
| Double Chance 1X (Home or Draw) | Random Forest | 0.58143 | 0.7046 |  |
| Double Chance 1X (Home or Draw) | HistGradientBoosting (Early Stopping) | 0.58740 | 0.6933 |  |
| Double Chance 1X (Home or Draw) | XGBoost (L1/L2 Regularized) | 0.58959 | 0.6975 |  |
| Double Chance 1X (Home or Draw) | Neural Network (Dropout) | 0.60020 | 0.7014 |  |
| Double Chance X2 (Away or Draw) | Logistic Regression (Elastic Net) | 0.61908 | 0.6535 | **GANADOR** |
| Double Chance X2 (Away or Draw) | Random Forest | 0.62526 | 0.6465 |  |
| Double Chance X2 (Away or Draw) | HistGradientBoosting (Early Stopping) | 0.63004 | 0.6440 |  |
| Double Chance X2 (Away or Draw) | XGBoost (L1/L2 Regularized) | 0.63343 | 0.6440 |  |
| Double Chance X2 (Away or Draw) | Neural Network (Dropout) | 0.62823 | 0.6436 |  |
| Over 2.5 Goals | Logistic Regression (Elastic Net) | 0.69997 | 0.5475 |  |
| Over 2.5 Goals | Random Forest | 0.68471 | 0.5603 |  |
| Over 2.5 Goals | HistGradientBoosting (Early Stopping) | 0.68792 | 0.5500 |  |
| Over 2.5 Goals | XGBoost (L1/L2 Regularized) | 0.68439 | 0.5702 | **GANADOR** |
| Over 2.5 Goals | Neural Network (Dropout) | 0.73364 | 0.5468 |  |
| Under 2.5 Goals | Logistic Regression (Elastic Net) | 0.70068 | 0.5482 |  |
| Under 2.5 Goals | Random Forest | 0.68462 | 0.5606 |  |
| Under 2.5 Goals | HistGradientBoosting (Early Stopping) | 0.68722 | 0.5589 |  |
| Under 2.5 Goals | XGBoost (L1/L2 Regularized) | 0.68410 | 0.5734 | **GANADOR** |
| Under 2.5 Goals | Neural Network (Dropout) | 0.69048 | 0.5479 |  |
| BTTS (Both Teams To Score) | Logistic Regression (Elastic Net) | 0.69266 | 0.5337 |  |
| BTTS (Both Teams To Score) | Random Forest | 0.69329 | 0.5220 |  |
| BTTS (Both Teams To Score) | HistGradientBoosting (Early Stopping) | 0.69129 | 0.5461 | **GANADOR** |
| BTTS (Both Teams To Score) | XGBoost (L1/L2 Regularized) | 0.69370 | 0.5284 |  |
| BTTS (Both Teams To Score) | Neural Network (Dropout) | 0.69025 | 0.5323 |  |
| BTTS - No | Logistic Regression (Elastic Net) | 0.69271 | 0.5337 |  |
| BTTS - No | Random Forest | 0.69397 | 0.5131 |  |
| BTTS - No | HistGradientBoosting (Early Stopping) | 0.72155 | 0.5376 |  |
| BTTS - No | XGBoost (L1/L2 Regularized) | 0.69279 | 0.5255 |  |
| BTTS - No | Neural Network (Dropout) | 1.21223 | 0.5394 | **GANADOR** |
| Home Clean Sheet | Logistic Regression (Elastic Net) | 0.60708 | 0.7085 |  |
| Home Clean Sheet | Random Forest | 0.59435 | 0.7071 |  |
| Home Clean Sheet | HistGradientBoosting (Early Stopping) | 0.59802 | 0.7089 |  |
| Home Clean Sheet | XGBoost (L1/L2 Regularized) | 0.60072 | 0.7085 |  |
| Home Clean Sheet | Neural Network (Dropout) | 0.65694 | 0.7099 | **GANADOR** |
