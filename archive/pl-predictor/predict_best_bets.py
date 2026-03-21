import pandas as pd
from src.models.selector import MasterBetSelector
from src.config import FEATURES_PATH, FEATURES

def main():
    print("Loading Master Bet Selector...")
    selector = MasterBetSelector()
    
    # Load some recent matches from our features dataset to test
    print("Loading recent matches for evaluation...")
    df = pd.read_csv(FEATURES_PATH)
    
    # Sort by date descending and grab the latest 5 matches
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)
        
    recent_matches = df.head(5)
    
    print("\n" + "="*50)
    print("🏆 MASTER BET PREDICTIONS FOR UPCOMING/RECENT MATCHES 🏆")
    print("="*50)
    
    for _, row in recent_matches.iterrows():
        match_title = f"{row.get('home_team', 'Home')} vs {row.get('away_team', 'Away')} ({row.get('date', '')})"
        print(f"\n⚽ Match: {match_title}")
        
        features_dict = {f: row[f] for f in FEATURES}
        predictions = selector.get_best_bet(features_dict)
        
        if not predictions:
            print("  No models loaded or error evaluating.")
            continue
            
        best_bet = predictions[0]
        print(f"  ⭐ BEST BET: {best_bet['Market']} -> {best_bet['Confidence']} probability")
        
        print("  Other top options:")
        for p in predictions[1:4]:
            print(f"    - {p['Market']}: {p['Confidence']}")

if __name__ == '__main__':
    main()
