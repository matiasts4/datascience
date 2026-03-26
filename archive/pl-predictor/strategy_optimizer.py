"""
Strategy Optimizer for Over 2.5 Goals
Runs hundreds of simulations across different parameter combinations
to find the configuration that maximizes profit.
"""
import pandas as pd
import numpy as np
from itertools import product
from src.config import FEATURES_PATH
from src.models.selector import MasterBetSelector
from src.backtester import evaluate_market_result

### SETTINGS ###
TARGET_MARKET     = 'Over 2.5 Goals'
INITIAL_BANKROLL  = 1000
N_MATCHES         = 1000        # Last N matches in the dataset
BEST_MARKET       = TARGET_MARKET

# Parameter grid to explore
CONF_THRESHOLDS   = [0.50, 0.52, 0.55, 0.57, 0.60, 0.62, 0.65, 0.70]
STAKE_AMOUNTS     = [10, 15, 20, 25, 30, 50]        # Fixed flat stakes
KELLY_FRACS       = [0.03, 0.05, 0.07, 0.10, 0.15]  # Kelly fraction caps
VIG_LEVELS        = [0.85, 0.90, 0.95, 0.98, 1.00]  # Bookmaker vig (1.0 = zero-edge)
STRATEGIES        = ['flat', 'kelly']
MIN_ODDS          = [1.1, 1.2, 1.3, 1.4, 1.5, 1.6]


def simulate(completed, selector, conf, stake, strategy, kelly_frac, vig, min_odd):
    bankroll = float(INITIAL_BANKROLL)
    total_bets = 0
    wins = 0
    profit_history = [bankroll]
    
    for _, row in completed.iterrows():
        if bankroll <= 0:
            break
        
        features = {col: row[col] for col in completed.columns if col in selector.scaler.feature_names_in_}
        preds = selector.get_best_bet(features)
        market_preds = [p for p in preds if p['Market'] == TARGET_MARKET]
        
        if not market_preds:
            continue
        
        prob = market_preds[0]['Probability']
        if prob < conf:
            continue
        
        # Calculate implied odds with vig factor
        fair_odds = 1.0 / prob
        boosted_odds = fair_odds * vig  # Simulate market offering vig-adjusted odds
        
        if boosted_odds < min_odd:
            continue
        
        # Determine stake
        if strategy == 'flat':
            s = min(float(stake), bankroll)
        else:  # kelly
            edge = (prob * boosted_odds) - 1
            kelly_stake = max(0, (edge / (boosted_odds - 1)) * bankroll)
            s = min(kelly_stake * kelly_frac, bankroll * 0.10, bankroll)
            s = max(s, 1.0)  # minimum bet
        
        bankroll -= s
        total_bets += 1
        
        is_win = evaluate_market_result(TARGET_MARKET, row['home_goals'], row['away_goals'], row.get('result_1x2'))
        if is_win:
            bankroll += s * boosted_odds
            wins += 1
        
        profit_history.append(bankroll)
    
    net_profit = bankroll - INITIAL_BANKROLL
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
    roi = (net_profit / (total_bets * float(stake) + 1e-9)) * 100
    sharpe = 0.0
    if len(profit_history) > 2:
        returns = np.diff(profit_history)
        sharpe = (returns.mean() / (returns.std() + 1e-9)) * np.sqrt(len(returns))
    
    return {
        'conf': conf,
        'stake': stake,
        'strategy': strategy,
        'kelly_frac': kelly_frac,
        'vig': vig,
        'min_odds': min_odd,
        'total_bets': total_bets,
        'wins': wins,
        'win_rate': round(win_rate, 2),
        'net_profit': round(net_profit, 2),
        'final_bankroll': round(bankroll, 2),
        'roi': round(roi, 2),
        'sharpe': round(sharpe, 4)
    }


def main():
    print('📂 Loading models and data...')
    df = pd.read_csv(FEATURES_PATH, parse_dates=['date'])
    selector = MasterBetSelector()
    
    completed = df[df['home_goals'].notna()].sort_values('date').tail(N_MATCHES)
    
    print(f'🏟  Dataset: {len(completed)} recent completed matches')
    print(f'🎯 Target Market: {TARGET_MARKET}')
    print(f'💳 Initial Bankroll: ${INITIAL_BANKROLL}')
    
    all_results = []
    total_runs = (len(CONF_THRESHOLDS) * len(STAKE_AMOUNTS) * len(VIG_LEVELS) * len(MIN_ODDS)) + \
                 (len(CONF_THRESHOLDS) * len(KELLY_FRACS) * len(VIG_LEVELS) * len(MIN_ODDS))
    
    print(f'\n🔁 Running {total_runs} simulations...\n')
    
    run_idx = 0
    # Flat strategy grid
    for conf, stake, vig, min_odd in product(CONF_THRESHOLDS, STAKE_AMOUNTS, VIG_LEVELS, MIN_ODDS):
        run_idx += 1
        res = simulate(completed, selector, conf, stake, 'flat', 0.05, vig, min_odd)
        all_results.append(res)
        if run_idx % 50 == 0:
            print(f'  [{run_idx}/{total_runs}] Best profit so far: ${max(r["net_profit"] for r in all_results):.2f}')
    
    # Kelly strategy grid
    for conf, kelly_frac, vig, min_odd in product(CONF_THRESHOLDS, KELLY_FRACS, VIG_LEVELS, MIN_ODDS):
        run_idx += 1
        res = simulate(completed, selector, conf, 20, 'kelly', kelly_frac, vig, min_odd)
        all_results.append(res)
        if run_idx % 50 == 0:
            print(f'  [{run_idx}/{total_runs}] Best profit so far: ${max(r["net_profit"] for r in all_results):.2f}')
    
    # Convert to DataFrame and sort by net profit
    results_df = pd.DataFrame(all_results)
    
    print('\n' + '='*70)
    print('       TOP 15 CONFIGURATIONS BY NET PROFIT')
    print('='*70)
    top15 = results_df.nlargest(15, 'net_profit')
    print(top15[['conf', 'strategy', 'stake', 'kelly_frac', 'vig', 'min_odds',
                  'total_bets', 'win_rate', 'net_profit', 'roi', 'sharpe']].to_string(index=False))
    
    print('\n' + '='*70)
    print('       TOP 5 BY SHARPE RATIO (MOST CONSISTENT)')
    print('='*70)
    top5_sharpe = results_df[results_df['total_bets'] >= 20].nlargest(5, 'sharpe')
    print(top5_sharpe[['conf', 'strategy', 'stake', 'kelly_frac', 'vig', 'min_odds',
                        'total_bets', 'win_rate', 'net_profit', 'roi', 'sharpe']].to_string(index=False))
    
    print('\n' + '='*70)
    print('       🏆 ABSOLUTE BEST CONFIGURATION')
    print('='*70)
    best = results_df.loc[results_df['net_profit'].idxmax()]
    print(f"  Strategy:          {best['strategy'].upper()}")
    print(f"  Confidence Min:    {best['conf']*100:.0f}%")
    if best['strategy'] == 'flat':
        print(f"  Stake:             ${best['stake']:.0f} per bet")
    else:
        print(f"  Kelly Fraction:    {best['kelly_frac']*100:.0f}%")
    print(f"  Bookmaker Vig:     {best['vig']*100:.0f}% of fair odds")
    print(f"  Min Odds Filter:   {best['min_odds']:.1f}")
    print(f"  Total Bets:        {best['total_bets']}")
    print(f"  Win Rate:          {best['win_rate']:.1f}%")
    print(f"  Net Profit:        ${best['net_profit']:.2f}")
    print(f"  Final Bankroll:    ${best['final_bankroll']:.2f}")
    print(f"  ROI:               {best['roi']:.2f}%")
    print(f"  Sharpe Ratio:      {best['sharpe']:.4f}")
    
    # Save full results CSV
    out_path = r'c:\Users\PC\DataScience\archive\pl-predictor\strategy_optimization_results.csv'
    results_df.sort_values('net_profit', ascending=False).to_csv(out_path, index=False)
    print(f'\n📊 Full results saved to: {out_path}')
    
    return best

if __name__ == '__main__':
    main()
