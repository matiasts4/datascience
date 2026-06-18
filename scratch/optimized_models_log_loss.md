# Resultados de Log Loss y Accuracy de Validacion Cruzada Temporal (5 splits)

| Mercado | Modelo | Log Loss | Accuracy | Estado |
| :--- | :--- | :---: | :---: | :---: |
| 1X2 (Match Winner) | Logistic Regression (Elastic Net) | 0.98770 | 0.5291 | **GANADOR** |
| 1X2 (Match Winner) | Random Forest | 0.99879 | 0.5248 |  |
| 1X2 (Match Winner) | HistGradientBoosting (Early Stopping) | 1.00520 | 0.5213 |  |
| 1X2 (Match Winner) | XGBoost (L1/L2 Regularized) | 1.01172 | 0.5103 |  |
| 1X2 (Match Winner) | Neural Network (Dropout) | 1.15782 | 0.4943 |  |
| Double Chance 1X (Home or Draw) | Logistic Regression (Elastic Net) | 0.57328 | 0.7035 | **GANADOR** |
| Double Chance 1X (Home or Draw) | Random Forest | 0.58376 | 0.6950 |  |
| Double Chance 1X (Home or Draw) | HistGradientBoosting (Early Stopping) | 0.58609 | 0.6943 |  |
| Double Chance 1X (Home or Draw) | XGBoost (L1/L2 Regularized) | 0.58384 | 0.6943 |  |
| Double Chance 1X (Home or Draw) | Neural Network (Dropout) | 0.77869 | 0.6801 |  |
| Double Chance X2 (Away or Draw) | Logistic Regression (Elastic Net) | 0.62836 | 0.6387 | **GANADOR** |
| Double Chance X2 (Away or Draw) | Random Forest | 0.63057 | 0.6362 |  |
| Double Chance X2 (Away or Draw) | HistGradientBoosting (Early Stopping) | 0.63603 | 0.6379 |  |
| Double Chance X2 (Away or Draw) | XGBoost (L1/L2 Regularized) | 0.63855 | 0.6450 |  |
| Double Chance X2 (Away or Draw) | Neural Network (Dropout) | 0.72640 | 0.6351 |  |
| Over 2.5 Goals | Logistic Regression (Elastic Net) | 0.68812 | 0.5482 |  |
| Over 2.5 Goals | Random Forest | 0.68525 | 0.5543 | **GANADOR** |
| Over 2.5 Goals | HistGradientBoosting (Early Stopping) | 0.68738 | 0.5539 |  |
| Over 2.5 Goals | XGBoost (L1/L2 Regularized) | 0.68819 | 0.5482 |  |
| Over 2.5 Goals | Neural Network (Dropout) | 0.72149 | 0.5379 |  |
| Under 2.5 Goals | Logistic Regression (Elastic Net) | 0.68844 | 0.5379 |  |
| Under 2.5 Goals | Random Forest | 0.68684 | 0.5532 |  |
| Under 2.5 Goals | HistGradientBoosting (Early Stopping) | 0.68665 | 0.5571 | **GANADOR** |
| Under 2.5 Goals | XGBoost (L1/L2 Regularized) | 0.68681 | 0.5557 |  |
| Under 2.5 Goals | Neural Network (Dropout) | 0.70977 | 0.5454 |  |
| BTTS (Both Teams To Score) | Logistic Regression (Elastic Net) | 0.69258 | 0.5337 |  |
| BTTS (Both Teams To Score) | Random Forest | 0.69405 | 0.5298 |  |
| BTTS (Both Teams To Score) | HistGradientBoosting (Early Stopping) | 0.69049 | 0.5323 | **GANADOR** |
| BTTS (Both Teams To Score) | XGBoost (L1/L2 Regularized) | 0.69171 | 0.5287 |  |
| BTTS (Both Teams To Score) | Neural Network (Dropout) | 0.78434 | 0.4908 |  |
| BTTS - No | Logistic Regression (Elastic Net) | 0.69237 | 0.5323 |  |
| BTTS - No | Random Forest | 0.69327 | 0.5223 |  |
| BTTS - No | HistGradientBoosting (Early Stopping) | 0.69226 | 0.5333 |  |
| BTTS - No | XGBoost (L1/L2 Regularized) | 0.69130 | 0.5294 | **GANADOR** |
| BTTS - No | Neural Network (Dropout) | 0.86715 | 0.5011 |  |
| Home Clean Sheet | Logistic Regression (Elastic Net) | 0.59194 | 0.7018 | **GANADOR** |
| Home Clean Sheet | Random Forest | 0.59475 | 0.7053 |  |
| Home Clean Sheet | HistGradientBoosting (Early Stopping) | 0.60046 | 0.6943 |  |
| Home Clean Sheet | XGBoost (L1/L2 Regularized) | 0.60197 | 0.6879 |  |
| Home Clean Sheet | Neural Network (Dropout) | 0.60552 | 0.6890 |  |
