import pandas as pd
from src.upcoming import get_upcoming_predictions
from src.api import get_selector, build_team_last5, get_df

try:
    df = get_df()
    selector = get_selector()
    preds = get_upcoming_predictions(df, selector, build_team_last5)
    print(f"Total predictions: {len(preds)}")
    if preds:
        print("First prediction:", preds[0])
except Exception as e:
    import traceback
    traceback.print_exc()
