import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from hedge_optimizer import get_current_prices

# Load the merged data (from earlier analysis)
# Recreate it quickly from saved files or rebuild
def load_historical_data():
    """Rebuild the 24-month dataset from our earlier work"""
    import yfinance as yf
    
    # Local maize
    maize = pd.read_excel("nbs_maize_filtered.xlsx")
    maize['Date'] = pd.to_datetime(maize['Date'], dayfirst=True, errors='coerce')
    maize['YearMonth'] = maize['Date'].dt.to_period('M').dt.to_timestamp()
    monthly_maize = maize.groupby('YearMonth')['UPRICE'].mean().reset_index()
    
    # Global corn
    corn = yf.download("ZC=F", period="5y", interval="1d")
    ngn = yf.download("NGN=X", period="5y", interval="1d")
    corn_close = corn['Close'].squeeze() / 100
    ngn_close = ngn['Close'].squeeze()
    corn_monthly = corn_close.resample('ME').mean()
    ngn_monthly = ngn_close.resample('ME').mean()
    bushel_to_kg = 25.4
    corn_ngn_per_kg = (corn_monthly / bushel_to_kg) * ngn_monthly
    
    global_price = pd.DataFrame({
        'YearMonth': corn_ngn_per_kg.index,
        'CBOT_Corn_NGN_per_kg': corn_ngn_per_kg.values
    })
    global_price['YearMonth'] = global_price['YearMonth'].dt.to_period('M').dt.to_timestamp()
    
    # Merge
    merged = pd.merge(monthly_maize, global_price, on='YearMonth', how='inner')
    merged['Basis_NGN_per_kg'] = merged['UPRICE'] - merged['CBOT_Corn_NGN_per_kg']
    
    return merged

def backtest_case_study(data, entry_date, exit_date, yield_kg, hedge_ratio, case_name):
    """
    Simulate a farmer who hedges at entry_date and closes at exit_date
    """
    # Find closest dates in data
    entry_data = data[data['YearMonth'] <= entry_date].iloc[-1]
    exit_data = data[data['YearMonth'] <= exit_date].iloc[-1]
    
    entry_local = entry_data['UPRICE']
    entry_global = entry_data['CBOT_Corn_NGN_per_kg']
    exit_local = exit_data['UPRICE']
    exit_global = exit_data['CBOT_Corn_NGN_per_kg']
    
    # Hedge quantity
    hedge_kg = yield_kg * hedge_ratio
    
    # Unhedged P&L: full exposure to local price change
    unhedged_pnl = yield_kg * (exit_local - entry_local)
    
    # Hedged P&L: 
    # - Spot portion: (100% - hedge_ratio) exposed to local price
    # - Futures portion: hedge_ratio locked at entry_global, closes at exit_global
    spot_pnl = (yield_kg - hedge_kg) * (exit_local - entry_local)
    futures_pnl = hedge_kg * (exit_global - entry_global)  # gain/loss on futures
    hedged_pnl = spot_pnl + futures_pnl
    
    return {
        'case_name': case_name,
        'entry_date': entry_data['YearMonth'],
        'exit_date': exit_data['YearMonth'],
        'entry_local': entry_local,
        'exit_local': exit_local,
        'entry_global': entry_global,
        'exit_global': exit_global,
        'local_price_change_pct': (exit_local - entry_local) / entry_local * 100,
        'global_price_change_pct': (exit_global - entry_global) / entry_global * 100,
        'unhedged_pnl': unhedged_pnl,
        'hedged_pnl': hedged_pnl,
        'savings': unhedged_pnl - hedged_pnl,
        'hedge_ratio': hedge_ratio,
        'yield_kg': yield_kg
    }

def plot_backtest(results):
    """Visualize the three case studies"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for i, result in enumerate(results):
        ax = axes[i]
        
        # Bar chart: unhedged vs hedged P&L
        categories = ['Unhedged', 'Hedged']
        values = [result['unhedged_pnl'], result['hedged_pnl']]
        colors = ['red' if v < 0 else 'green' for v in values]
        
        bars = ax.bar(categories, values, color=colors, alpha=0.7, edgecolor='black')
        ax.axhline(0, color='black', linewidth=1)
        ax.set_ylabel('P&L (₦)')
        ax.set_title(f"{result['case_name']}\n{result['entry_date'].strftime('%b %Y')} → {result['exit_date'].strftime('%b %Y')}")
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'₦{val:,.0f}',
                   ha='center', va='bottom' if height > 0 else 'top',
                   fontsize=10, fontweight='bold')
        
        # Add savings annotation
        savings = result['savings']
        ax.text(0.5, max(values) * 0.8, 
               f"Savings: ₦{savings:,.0f}\n({result['hedge_ratio']*100:.0f}% hedge)",
               ha='center', fontsize=9,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('historical_backtest.png', dpi=300, bbox_inches='tight')
    print("Backtest visualization saved as 'historical_backtest.png'")
    plt.show()

if __name__ == "__main__":
    print("Loading historical data...")
    data = load_historical_data()
    print(f"Loaded {len(data)} months of data")
    
    # Define three case studies
    case_studies = [
        {
            'name': 'Case 1: Pre-Planting Hedge',
            'entry': '2024-04-01',
            'exit': '2024-10-01',
            'yield_kg': 10000,
            'hedge_ratio': 0.25
        },
        {
            'name': 'Case 2: Harvest Season Crash',
            'entry': '2024-08-01',
            'exit': '2024-12-01',
            'yield_kg': 10000,
            'hedge_ratio': 0.25
        },
        {
            'name': 'Case 3: Basis Spike Period',
            'entry': '2024-06-01',
            'exit': '2024-09-01',
            'yield_kg': 10000,
            'hedge_ratio': 0.25
        }
    ]
    
    results = []
    for case in case_studies:
        print(f"\nRunning {case['name']}...")
        result = backtest_case_study(
            data, 
            case['entry'], 
            case['exit'], 
            case['yield_kg'], 
            case['hedge_ratio'],
            case['name']
        )
        results.append(result)
        
        print(f"  Entry: ₦{result['entry_local']:.2f}/kg → Exit: ₦{result['exit_local']:.2f}/kg")
        print(f"  Local change: {result['local_price_change_pct']:.1f}%")
        print(f"  Global change: {result['global_price_change_pct']:.1f}%")
        print(f"  Unhedged P&L: ₦{result['unhedged_pnl']:,.0f}")
        print(f"  Hedged P&L: ₦{result['hedged_pnl']:,.0f}")
        print(f"  Savings from hedge: ₦{result['savings']:,.0f}")
    
    print("\n" + "="*60)
    print("SUMMARY: Historical Backtest Results")
    print("="*60)
    total_savings = sum(r['savings'] for r in results)
    print(f"Total savings across 3 case studies: ₦{total_savings:,.0f}")
    print(f"Average savings per case: ₦{total_savings/3:,.0f}")
    print("="*60)
    
    plot_backtest(results)