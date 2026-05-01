import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from hedge_optimizer import recommend_hedge, get_current_prices

def monte_carlo_scenario(yield_kg, current_local_price, hedge_ratio, 
                         global_price, basis_mean, basis_std,
                         n_simulations=1000, price_drop_range=(-0.30, 0.10)):
    """
    Run Monte Carlo simulation of price scenarios
    """
    np.random.seed(42)  # Reproducible
    
    # Generate random price shocks
    price_shocks = np.random.uniform(price_drop_range[0], price_drop_range[1], n_simulations)
    
    # Local price paths: global component + basis noise
    global_shocks = price_shocks * 0.6  # 60% correlation with global
    basis_noise = np.random.normal(0, basis_std / current_local_price, n_simulations)
    
    local_price_paths = current_local_price * (1 + global_shocks + basis_noise)
    
    # Ensure no negative prices
    local_price_paths = np.maximum(local_price_paths, current_local_price * 0.5)
    
    # Calculate P&L
    hedge_quantity_kg = yield_kg * hedge_ratio
    
    # Unhedged: full exposure
    unhedged_pnl = yield_kg * (local_price_paths - current_local_price)
    
    # Hedged: protected portion
    hedged_spot_pnl = hedge_quantity_kg * (local_price_paths - current_local_price)
    futures_pnl = -hedge_quantity_kg * global_price * global_shocks  # futures gain/loss
    hedged_pnl = (yield_kg - hedge_quantity_kg) * (local_price_paths - current_local_price) + futures_pnl
    
    return {
        'price_shocks': price_shocks,
        'local_price_paths': local_price_paths,
        'unhedged_pnl': unhedged_pnl,
        'hedged_pnl': hedged_pnl,
        'hedge_ratio': hedge_ratio
    }

def plot_scenarios(results, yield_kg, current_local_price):
    """
    Visualize Monte Carlo outcomes
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Price distribution
    axes[0, 0].hist(results['local_price_paths'], bins=50, alpha=0.7, color='blue', edgecolor='black')
    axes[0, 0].axvline(current_local_price, color='red', linestyle='--', linewidth=2, label=f'Current: ₦{current_local_price:,.0f}/kg')
    axes[0, 0].set_xlabel('Local Maize Price (₦/kg)')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Simulated Price Distribution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: P&L comparison (scatter)
    axes[0, 1].scatter(results['unhedged_pnl'], results['hedged_pnl'], alpha=0.5, s=10)
    axes[0, 1].plot([-5e6, 5e6], [-5e6, 5e6], 'r--', label='Break-even line')
    axes[0, 1].set_xlabel('Unhedged P&L (₦)')
    axes[0, 1].set_ylabel('Hedged P&L (₦)')
    axes[0, 1].set_title(f'Hedged vs. Unhedged P&L ({results["hedge_ratio"]*100:.0f}% hedge)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: P&L distributions
    axes[1, 0].hist(results['unhedged_pnl'], bins=50, alpha=0.5, label='Unhedged', color='red')
    axes[1, 0].hist(results['hedged_pnl'], bins=50, alpha=0.5, label='Hedged', color='green')
    axes[1, 0].axvline(0, color='black', linestyle='-', linewidth=1)
    axes[1, 0].set_xlabel('P&L (₦)')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('P&L Distribution Comparison')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Risk metrics table (text)
    axes[1, 1].axis('off')
    
    unhedged = results['unhedged_pnl']
    hedged = results['hedged_pnl']
    
    metrics = [
        ['Metric', 'Unhedged', 'Hedged', 'Improvement'],
        ['Mean P&L', f'₦{np.mean(unhedged):,.0f}', f'₦{np.mean(hedged):,.0f}', f'₦{np.mean(hedged)-np.mean(unhedged):,.0f}'],
        ['Worst Case (5%)', f'₦{np.percentile(unhedged, 5):,.0f}', f'₦{np.percentile(hedged, 5):,.0f}', f'₦{np.percentile(hedged, 5)-np.percentile(unhedged, 5):,.0f}'],
        ['Best Case (95%)', f'₦{np.percentile(unhedged, 95):,.0f}', f'₦{np.percentile(hedged, 95):,.0f}', f'₦{np.percentile(hedged, 95)-np.percentile(unhedged, 95):,.0f}'],
        ['Std Deviation', f'₦{np.std(unhedged):,.0f}', f'₦{np.std(hedged):,.0f}', f'{((np.std(unhedged)-np.std(hedged))/np.std(unhedged)*100):.1f}% reduction'],
    ]
    
    table = axes[1, 1].table(cellText=metrics[1:], colLabels=metrics[0], 
                              cellLoc='center', loc='center', bbox=[0, 0.3, 1, 0.6])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    axes[1, 1].set_title('Risk Metrics Comparison', pad=20)
    
    plt.tight_layout()
    plt.savefig('monte_carlo_scenarios.png', dpi=300, bbox_inches='tight')
    print("Scenario analysis saved as 'monte_carlo_scenarios.png'")
    
    plt.show()

if __name__ == "__main__":
    # Test parameters
    yield_kg = 10000
    current_local_price = 1150
    hedge_ratio = 0.25
    global_price = get_current_prices()
    basis_mean = 884
    basis_std = 49
    
    print(f"Running {1000} simulations...")
    print(f"Parameters: {yield_kg:,.0f}kg, ₦{current_local_price:,.0f}/kg, {hedge_ratio*100:.0f}% hedge")
    
    results = monte_carlo_scenario(
        yield_kg=yield_kg,
        current_local_price=current_local_price,
        hedge_ratio=hedge_ratio,
        global_price=global_price,
        basis_mean=basis_mean,
        basis_std=basis_std
    )
    
    plot_scenarios(results, yield_kg, current_local_price)
    
    print(f"\nSimulation complete.")
    print(f"Unhedged worst case (5%): ₦{np.percentile(results['unhedged_pnl'], 5):,.0f}")
    print(f"Hedged worst case (5%): ₦{np.percentile(results['hedged_pnl'], 5):,.0f}")