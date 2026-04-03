import pandas as pd
import numpy as np
import joblib
import os
from src.config import FEATURES_PATH, FEATURES, MODELS_DIR

df = pd.read_csv(FEATURES_PATH).dropna()
# Take last 532 matches as test (like the evaluation script does)
test_df = df.iloc[-532:].copy()

scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
X_test = scaler.transform(test_df[FEATURES])

model_1x2 = joblib.load(os.path.join(MODELS_DIR, 'model_1X2_Match_Winner.pkl'))

preds = model_1x2.predict(X_test)
test_df['predicted_1x2'] = preds
test_df['actual_1x2'] = test_df['result_1x2'].astype(int)

# Calc ROI for 1X2 Flat betting (10 units each)
spent = 0
won = 0

for idx, row in test_df.iterrows():
    p = row['predicted_1x2']
    a = row['actual_1x2']
    odds = 0
    if p == 0: odds = row['B365H']
    elif p == 1: odds = row['B365D']
    elif p == 2: odds = row['B365A']
    
    if odds == 0 or pd.isna(odds): odds = 2.0 # fallback

    spent += 10
    if p == a:
        won += 10 * odds

roi = ((won - spent) / spent) * 100
acc = (test_df['predicted_1x2'] == test_df['actual_1x2']).mean() * 100

print(f'== Real-world Hold-out Backtest ==')
print(f'1X2 Accuracy: {acc:.1f}%')
print(f'1X2 Total Spent: ${spent}')
print(f'1X2 Total Won: ${won:.2f}')
print(f'1X2 ROI: {roi:.2f}%')
