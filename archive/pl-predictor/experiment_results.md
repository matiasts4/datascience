# Resultados de Optimización de Hiperparámetros

## 1X2 (Match Winner)
- **Logistic Regression** - Test Accuracy: `0.5414`
  - Mejores Parámetros: `{'solver': 'lbfgs', 'penalty': 'l2', 'C': 0.01}`
- **Random Forest** - Test Accuracy: `0.5414`
  - Mejores Parámetros: `{'n_estimators': 300, 'min_samples_split': 5, 'min_samples_leaf': 1, 'max_depth': 5}`
- **HistGradientBoosting** - Test Accuracy: `0.5244`
  - Mejores Parámetros: `{'max_iter': 100, 'max_depth': 10, 'learning_rate': 0.01, 'l2_regularization': 10.0}`

🏆 **GANADOR PARA 1X2 (Match Winner)**: Logistic Regression (Acc: `0.5414`)

---
## Over 2.5 Goals
- **Logistic Regression** - Test Accuracy: `0.5639`
  - Mejores Parámetros: `{'solver': 'liblinear', 'penalty': 'l2', 'C': 1}`
- **Random Forest** - Test Accuracy: `0.5808`
  - Mejores Parámetros: `{'n_estimators': 200, 'min_samples_split': 10, 'min_samples_leaf': 1, 'max_depth': 5}`
- **HistGradientBoosting** - Test Accuracy: `0.5658`
  - Mejores Parámetros: `{'max_iter': 100, 'max_depth': 3, 'learning_rate': 0.05, 'l2_regularization': 0.0}`

🏆 **GANADOR PARA Over 2.5 Goals**: Random Forest (Acc: `0.5808`)

---
## BTTS (Both Teams To Score)
- **Logistic Regression** - Test Accuracy: `0.5677`
  - Mejores Parámetros: `{'solver': 'liblinear', 'penalty': 'l2', 'C': 0.01}`
- **Random Forest** - Test Accuracy: `0.5414`
  - Mejores Parámetros: `{'n_estimators': 500, 'min_samples_split': 2, 'min_samples_leaf': 2, 'max_depth': None}`
- **HistGradientBoosting** - Test Accuracy: `0.5282`
  - Mejores Parámetros: `{'max_iter': 100, 'max_depth': 10, 'learning_rate': 0.01, 'l2_regularization': 10.0}`

🏆 **GANADOR PARA BTTS (Both Teams To Score)**: Logistic Regression (Acc: `0.5677`)

---
