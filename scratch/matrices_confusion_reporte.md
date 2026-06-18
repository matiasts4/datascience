# Reporte de Matrices de Confusión y Métricas de Clasificación (Capa 1)

Este documento presenta el desglose detallado de las matrices de confusión y métricas asociadas evaluadas sobre el conjunto de test final (último fold de TimeSeriesSplit 5-folds).

## Resumen Ejecutivo de Métricas

| Mercado | Algoritmo | AUC-ROC | Accuracy | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1X2 (Match Winner) | LogisticRegression | 0.6638 | 0.5177 | 0.4733 | 0.5177 | 0.4429 |
| Double Chance 1X | LogisticRegression | 0.7132 | 0.6968 | 0.7257 | 0.8747 | 0.7932 |
| Double Chance X2 | LogisticRegression | 0.7059 | 0.6401 | 0.7072 | 0.6535 | 0.6793 |
| Over 2.5 Goals | RandomForestClassifier | 0.6177 | 0.5780 | 0.5674 | 0.9774 | 0.7180 |
| Under 2.5 Goals | HistGradientBoostingClassifier | 0.6441 | 0.5585 | 0.6923 | 0.0354 | 0.0674 |
| BTTS (Both Teams To Score) | HistGradientBoostingClassifier | 0.6236 | 0.5674 | 0.5587 | 0.9772 | 0.7109 |
| BTTS - No | XGBClassifier | 0.6261 | 0.5496 | 0.7143 | 0.0195 | 0.0379 |
| Home Clean Sheet | LogisticRegression | 0.6169 | 0.7252 | 0.2727 | 0.0200 | 0.0373 |

---

## Detalle de Clasificación: 1X2 (Match Winner)
* **Algoritmo:** `LogisticRegression`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6638`
  * **Accuracy:** `0.5177`
  * **Precision:** `0.4733`
  * **Recall:** `0.5177`
  * **F1-Score:** `0.4429`

### Classification Report Completo:
```
              precision    recall  f1-score   support

   Visitante       0.52      0.53      0.53       189
      Empate       0.33      0.01      0.01       140
       Local       0.52      0.81      0.63       235

    accuracy                           0.52       564
   macro avg       0.46      0.45      0.39       564
weighted avg       0.47      0.52      0.44       564
```

---

## Detalle de Clasificación: Double Chance 1X
* **Algoritmo:** `LogisticRegression`
* **Métricas Generales:**
  * **AUC-ROC:** `0.7132`
  * **Accuracy:** `0.6968`
  * **Precision:** `0.7257`
  * **Recall:** `0.8747`
  * **F1-Score:** `0.7932`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `65`
  * Falsos Positivos (FP - Apuestas Perdidas): `124`
  * Falsos Negativos (FN): `47`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `328`

### Classification Report Completo:
```
              precision    recall  f1-score   support

        Otro       0.58      0.34      0.43       189
          1X       0.73      0.87      0.79       375

    accuracy                           0.70       564
   macro avg       0.65      0.61      0.61       564
weighted avg       0.68      0.70      0.67       564
```

---

## Detalle de Clasificación: Double Chance X2
* **Algoritmo:** `LogisticRegression`
* **Métricas Generales:**
  * **AUC-ROC:** `0.7059`
  * **Accuracy:** `0.6401`
  * **Precision:** `0.7072`
  * **Recall:** `0.6535`
  * **F1-Score:** `0.6793`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `146`
  * Falsos Positivos (FP - Apuestas Perdidas): `89`
  * Falsos Negativos (FN): `114`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `215`

### Classification Report Completo:
```
              precision    recall  f1-score   support

        Otro       0.56      0.62      0.59       235
          X2       0.71      0.65      0.68       329

    accuracy                           0.64       564
   macro avg       0.63      0.64      0.63       564
weighted avg       0.65      0.64      0.64       564
```

---

## Detalle de Clasificación: Over 2.5 Goals
* **Algoritmo:** `RandomForestClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6177`
  * **Accuracy:** `0.5780`
  * **Precision:** `0.5674`
  * **Recall:** `0.9774`
  * **F1-Score:** `0.7180`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `23`
  * Falsos Positivos (FP - Apuestas Perdidas): `231`
  * Falsos Negativos (FN): `7`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `303`

### Classification Report Completo:
```
              precision    recall  f1-score   support

   Under 2.5       0.77      0.09      0.16       254
    Over 2.5       0.57      0.98      0.72       310

    accuracy                           0.58       564
   macro avg       0.67      0.53      0.44       564
weighted avg       0.66      0.58      0.47       564
```

---

## Detalle de Clasificación: Under 2.5 Goals
* **Algoritmo:** `HistGradientBoostingClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6441`
  * **Accuracy:** `0.5585`
  * **Precision:** `0.6923`
  * **Recall:** `0.0354`
  * **F1-Score:** `0.0674`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `306`
  * Falsos Positivos (FP - Apuestas Perdidas): `4`
  * Falsos Negativos (FN): `245`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `9`

### Classification Report Completo:
```
              precision    recall  f1-score   support

    Over 2.5       0.56      0.99      0.71       310
   Under 2.5       0.69      0.04      0.07       254

    accuracy                           0.56       564
   macro avg       0.62      0.51      0.39       564
weighted avg       0.62      0.56      0.42       564
```

---

## Detalle de Clasificación: BTTS (Both Teams To Score)
* **Algoritmo:** `HistGradientBoostingClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6236`
  * **Accuracy:** `0.5674`
  * **Precision:** `0.5587`
  * **Recall:** `0.9772`
  * **F1-Score:** `0.7109`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `20`
  * Falsos Positivos (FP - Apuestas Perdidas): `237`
  * Falsos Negativos (FN): `7`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `300`

### Classification Report Completo:
```
              precision    recall  f1-score   support

     No BTTS       0.74      0.08      0.14       257
        BTTS       0.56      0.98      0.71       307

    accuracy                           0.57       564
   macro avg       0.65      0.53      0.43       564
weighted avg       0.64      0.57      0.45       564
```

---

## Detalle de Clasificación: BTTS - No
* **Algoritmo:** `XGBClassifier`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6261`
  * **Accuracy:** `0.5496`
  * **Precision:** `0.7143`
  * **Recall:** `0.0195`
  * **F1-Score:** `0.0379`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `305`
  * Falsos Positivos (FP - Apuestas Perdidas): `2`
  * Falsos Negativos (FN): `252`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `5`

### Classification Report Completo:
```
              precision    recall  f1-score   support

        BTTS       0.55      0.99      0.71       307
     No BTTS       0.71      0.02      0.04       257

    accuracy                           0.55       564
   macro avg       0.63      0.51      0.37       564
weighted avg       0.62      0.55      0.40       564
```

---

## Detalle de Clasificación: Home Clean Sheet
* **Algoritmo:** `LogisticRegression`
* **Métricas Generales:**
  * **AUC-ROC:** `0.6169`
  * **Accuracy:** `0.7252`
  * **Precision:** `0.2727`
  * **Recall:** `0.0200`
  * **F1-Score:** `0.0373`

* **Matriz de Confusión (Desglose):**
  * Verdaderos Negativos (TN): `406`
  * Falsos Positivos (FP - Apuestas Perdidas): `8`
  * Falsos Negativos (FN): `147`
  * Verdaderos Positivos (VP - Apuestas Ganadas): `3`

### Classification Report Completo:
```
               precision    recall  f1-score   support

Gol Concedido       0.73      0.98      0.84       414
Valla Invicta       0.27      0.02      0.04       150

     accuracy                           0.73       564
    macro avg       0.50      0.50      0.44       564
 weighted avg       0.61      0.73      0.63       564
```
