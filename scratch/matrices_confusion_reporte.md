# Reporte de Matrices de Confusión y Métricas de Clasificación (Capa 1)

Este documento presenta el desglose detallado de las matrices de confusión y métricas asociadas evaluadas sobre el conjunto de test final (último fold de TimeSeriesSplit 5-folds).

## Resumen Ejecutivo de Métricas

| Mercado | Algoritmo | AUC-ROC | Accuracy | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1X2 (Match Winner) | LogisticRegression | 0.6676 | 0.5177 | 0.4457 | 0.5177 | 0.4513 |
| Double Chance 1X | LogisticRegression | 0.7203 | 0.7039 | 0.7203 | 0.9067 | 0.8028 |
| Double Chance X2 | LogisticRegression | 0.7052 | 0.6596 | 0.7009 | 0.7264 | 0.7134 |
| Over 2.5 Goals | XGBClassifier | 0.5798 | 0.5514 | 0.5506 | 1.0000 | 0.7102 |
| Under 2.5 Goals | XGBClassifier | 0.5830 | 0.5514 | 1.0000 | 0.0039 | 0.0078 |
| BTTS (Both Teams To Score) | HistGradientBoostingClassifier | 0.6934 | 0.5869 | 0.5720 | 0.9577 | 0.7162 |
| BTTS - No | PyTorchMLPClassifier | 0.6307 | 0.5443 | 0.0000 | 0.0000 | 0.0000 |
| Home Clean Sheet | PyTorchMLPClassifier | 0.5536 | 0.7340 | 0.0000 | 0.0000 | 0.0000 |

---

## Detalle de Clasificación: 1X2 (Match Winner)
* **Algoritmo:** `LogisticRegression`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6676`
  * **Accuracy:** `0.5177`
  * **Precision:** `0.4457`
  * **Recall:** `0.5177`
  * **F1-Score:** `0.4513`

### Classification Report Completo:
```
              precision    recall  f1-score   support

   Visitante       0.53      0.52      0.53       189
      Empate       0.20      0.02      0.04       140
       Local       0.52      0.81      0.64       235

    accuracy                           0.52       564
   macro avg       0.42      0.45      0.40       564
weighted avg       0.45      0.52      0.45       564
```

---

## Detalle de Clasificación: Double Chance 1X
* **Algoritmo:** `LogisticRegression`
* **Métricas Generales:**
  * **AUC-ROC:** `0.7203`
  * **Accuracy:** `0.7039`
  * **Precision:** `0.7203`
  * **Recall:** `0.9067`
  * **F1-Score:** `0.8028`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `57`
  * Falsos Positivos (FP - Apuestas Perdidas): `132`
  * Falsos Negativos (FN): `35`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `340`

### Classification Report Completo:
```
              precision    recall  f1-score   support

        Otro       0.62      0.30      0.41       189
          1X       0.72      0.91      0.80       375

    accuracy                           0.70       564
   macro avg       0.67      0.60      0.60       564
weighted avg       0.69      0.70      0.67       564
```

---

## Detalle de Clasificación: Double Chance X2
* **Algoritmo:** `LogisticRegression`
* **Métricas Generales:**
  * **AUC-ROC:** `0.7052`
  * **Accuracy:** `0.6596`
  * **Precision:** `0.7009`
  * **Recall:** `0.7264`
  * **F1-Score:** `0.7134`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `133`
  * Falsos Positivos (FP - Apuestas Perdidas): `102`
  * Falsos Negativos (FN): `90`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `239`

### Classification Report Completo:
```
              precision    recall  f1-score   support

        Otro       0.60      0.57      0.58       235
          X2       0.70      0.73      0.71       329

    accuracy                           0.66       564
   macro avg       0.65      0.65      0.65       564
weighted avg       0.66      0.66      0.66       564
```

---

## Detalle de Clasificación: Over 2.5 Goals
* **Algoritmo:** `XGBClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.5798`
  * **Accuracy:** `0.5514`
  * **Precision:** `0.5506`
  * **Recall:** `1.0000`
  * **F1-Score:** `0.7102`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `1`
  * Falsos Positivos (FP - Apuestas Perdidas): `253`
  * Falsos Negativos (FN): `0`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `310`

### Classification Report Completo:
```
              precision    recall  f1-score   support

   Under 2.5       1.00      0.00      0.01       254
    Over 2.5       0.55      1.00      0.71       310

    accuracy                           0.55       564
   macro avg       0.78      0.50      0.36       564
weighted avg       0.75      0.55      0.39       564
```

---

## Detalle de Clasificación: Under 2.5 Goals
* **Algoritmo:** `XGBClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.5830`
  * **Accuracy:** `0.5514`
  * **Precision:** `1.0000`
  * **Recall:** `0.0039`
  * **F1-Score:** `0.0078`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `310`
  * Falsos Positivos (FP - Apuestas Perdidas): `0`
  * Falsos Negativos (FN): `253`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `1`

### Classification Report Completo:
```
              precision    recall  f1-score   support

    Over 2.5       0.55      1.00      0.71       310
   Under 2.5       1.00      0.00      0.01       254

    accuracy                           0.55       564
   macro avg       0.78      0.50      0.36       564
weighted avg       0.75      0.55      0.39       564
```

---

## Detalle de Clasificación: BTTS (Both Teams To Score)
* **Algoritmo:** `HistGradientBoostingClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6934`
  * **Accuracy:** `0.5869`
  * **Precision:** `0.5720`
  * **Recall:** `0.9577`
  * **F1-Score:** `0.7162`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `37`
  * Falsos Positivos (FP - Apuestas Perdidas): `220`
  * Falsos Negativos (FN): `13`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `294`

### Classification Report Completo:
```
              precision    recall  f1-score   support

     No BTTS       0.74      0.14      0.24       257
        BTTS       0.57      0.96      0.72       307

    accuracy                           0.59       564
   macro avg       0.66      0.55      0.48       564
weighted avg       0.65      0.59      0.50       564
```

---

## Detalle de Clasificación: BTTS - No
* **Algoritmo:** `PyTorchMLPClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6307`
  * **Accuracy:** `0.5443`
  * **Precision:** `0.0000`
  * **Recall:** `0.0000`
  * **F1-Score:** `0.0000`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `307`
  * Falsos Positivos (FP - Apuestas Perdidas): `0`
  * Falsos Negativos (FN): `257`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `0`

### Classification Report Completo:
```
              precision    recall  f1-score   support

        BTTS       0.54      1.00      0.70       307
     No BTTS       0.00      0.00      0.00       257

    accuracy                           0.54       564
   macro avg       0.27      0.50      0.35       564
weighted avg       0.30      0.54      0.38       564
```

---

## Detalle de Clasificación: Home Clean Sheet
* **Algoritmo:** `PyTorchMLPClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.5536`
  * **Accuracy:** `0.7340`
  * **Precision:** `0.0000`
  * **Recall:** `0.0000`
  * **F1-Score:** `0.0000`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `414`
  * Falsos Positivos (FP - Apuestas Perdidas): `0`
  * Falsos Negativos (FN): `150`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `0`

### Classification Report Completo:
```
               precision    recall  f1-score   support

Gol Concedido       0.73      1.00      0.85       414
Valla Invicta       0.00      0.00      0.00       150

     accuracy                           0.73       564
    macro avg       0.37      0.50      0.42       564
 weighted avg       0.54      0.73      0.62       564
```
