import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# Page config
st.set_page_config(
    page_title="The Hedger",
    page_icon="🌽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f4e79;}
    .sub-header {font-size: 1.2rem; color: #555; margin-bottom: 2rem;}
    .metric-card {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;}
    .warning-box {background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ffc107;}
    .success-box {background-color: #d4edda; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #28a745;}
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🌽 The Hedger</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Quantitative risk management for Nigerian maize farmers</p>', unsafe_allow_html=True)

# Sidebar inputs
st.sidebar.header("Farmer Inputs")

yield_kg = st.sidebar.number_input(
    "Expected Yield (kg)",
    min_value=1000,
    max_value=1000000,
    value=10000,
    step=1000,
    help="Total maize you expect to harvest"
)

planting_month = st.sidebar.selectbox(
    "Planting Month",
    options=list(range(1, 13)),
    format_func=lambda x: datetime(2024, x, 1).strftime('%B'),
    index=3,  # April
    help="When you plant"
)

harvest_month = st.sidebar.selectbox(
    "Harvest Month",
    options=list(range(1, 13)),
    format_func=lambda x: datetime(2024, x, 1).strftime('%B'),
    index=9,  # October
    help="When you harvest"
)

risk_tolerance = st.sidebar.select_slider(
    "Risk Tolerance",
    options=['Conservative', 'Moderate', 'Aggressive'],
    value='Moderate',
    help="How much risk you want to take"
)

current_local_price = st.sidebar.number_input(
    "Current Local Maize Price (₦/kg)",
    min_value=500,
    max_value=3000,
    value=1150,
    step=50,
    help="What maize costs in your market today"
)

# Functions (cached to avoid repeated API calls)
@st.cache_data(ttl=3600)
def get_current_prices():
    """Fetch current CBOT corn and NGN/USD"""
    corn = yf.download("ZC=F", period="5d", interval="1d")
    ngn = yf.download("NGN=X", period="5d", interval="1d")
    
    corn_close = corn['Close'].squeeze().iloc[-1] / 100
    ngn_close = ngn['Close'].squeeze().iloc[-1]
    
    bushel_to_kg = 25.4
    corn_ngn_per_kg = (corn_close / bushel_to_kg) * ngn_close
    
    return corn_ngn_per_kg, ngn_close

def calculate_hedge(yield_kg, planting_month, harvest_month, risk_tolerance, current_local_price):
    """Core hedge calculation"""
    hedge_ratios = {
        'Conservative': 0.40,
        'Moderate': 0.25,
        'Aggressive': 0.10
    }
    
    hedge_ratio = hedge_ratios[risk_tolerance]
    contract_month = (harvest_month % 12) + 1
    contract_year = 2026 if harvest_month >= 12 else 2025
    
    global_price, ngn_rate = get_current_prices()
    basis = current_local_price - global_price
    
    hedge_quantity_kg = yield_kg * hedge_ratio
    kg_to_bushel = 1 / 25.4
    hedge_quantity_bushels = hedge_quantity_kg * kg_to_bushel
    contract_size = 5000
    num_contracts = round(hedge_quantity_bushels / contract_size)
    
    margin_per_contract_usd = 1500
    margin_per_contract_ngn = margin_per_contract_usd * ngn_rate
    total_margin = num_contracts * margin_per_contract_ngn
    
    # Scenarios
    price_drop = 0.20
    unhedged_loss = yield_kg * current_local_price * price_drop
    futures_gain = hedge_quantity_kg * global_price * price_drop
    net_hedged_loss = unhedged_loss - futures_gain
    
    return {
        'hedge_ratio': hedge_ratio,
        'hedge_quantity_kg': hedge_quantity_kg,
        'num_contracts': num_contracts,
        'contract_month': contract_month,
        'contract_year': contract_year,
        'global_price': global_price,
        'basis': basis,
        'total_margin': total_margin,
        'unhedged_loss': unhedged_loss,
        'hedged_loss': net_hedged_loss,
        'savings': unhedged_loss - net_hedged_loss,
        'scale_feasible': num_contracts >= 1
    }

def run_monte_carlo(yield_kg, current_local_price, hedge_ratio, global_price, n_simulations=500):
    """Simplified Monte Carlo for Streamlit"""
    np.random.seed(42)
    price_shocks = np.random.uniform(-0.30, 0.10, n_simulations)
    global_shocks = price_shocks * 0.6
    basis_noise = np.random.normal(0, 49/1150, n_simulations)
    
    local_price_paths = current_local_price * (1 + global_shocks + basis_noise)
    local_price_paths = np.maximum(local_price_paths, current_local_price * 0.5)
    
    hedge_kg = yield_kg * hedge_ratio
    
    unhedged_pnl = yield_kg * (local_price_paths - current_local_price)
    spot_pnl = (yield_kg - hedge_kg) * (local_price_paths - current_local_price)
    futures_pnl = -hedge_kg * global_price * global_shocks
    hedged_pnl = spot_pnl + futures_pnl
    
    return {
        'unhedged_pnl': unhedged_pnl,
        'hedged_pnl': hedged_pnl,
        'local_price_paths': local_price_paths
    }

# Main calculation
result = calculate_hedge(yield_kg, planting_month, harvest_month, risk_tolerance, current_local_price)

# Display results
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Hedge Ratio", f"{result['hedge_ratio']*100:.0f}%")
    st.metric("Quantity to Hedge", f"{result['hedge_quantity_kg']:,.0f} kg")

with col2:
    st.metric("CBOT Contracts", f"{result['num_contracts']}")
    st.metric("Margin Required", f"₦{result['total_margin']:,.0f}")

with col3:
    st.metric("Current Basis", f"₦{result['basis']:,.0f}/kg")
    st.metric("Global Price", f"₦{result['global_price']:,.0f}/kg")

# Scale warning
if not result['scale_feasible']:
    st.markdown("""
        <div class="warning-box">
            <strong>⚠️ Scale Warning</strong><br>
            Your hedge quantity is too small for direct CBOT futures (minimum: ~127,000 kg equivalent).<br><br>
            <strong>Recommended alternatives:</strong><br>
            1. Join a cooperative/aggregator to pool volume<br>
            2. Use OTC forward contracts with local buyers<br>
            3. Increase hedge ratio if risk tolerance allows
        </div>
    """, unsafe_allow_html=True)

# Scenario analysis
st.subheader("💰 Scenario Analysis: If Prices Drop 20%")

col4, col5, col6 = st.columns(3)

with col4:
    st.metric("Unhedged Loss", f"₦{result['unhedged_loss']:,.0f}", delta=None)

with col5:
    st.metric("Hedged Loss", f"₦{result['hedged_loss']:,.0f}", delta=None)

with col6:
    st.metric("Savings", f"₦{result['savings']:,.0f}", delta=f"₦{result['savings']:,.0f}")

# Monte Carlo visualization
st.subheader("📊 Monte Carlo Simulation (500 scenarios)")

mc_results = run_monte_carlo(yield_kg, current_local_price, result['hedge_ratio'], result['global_price'])

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# P&L distributions
axes[0].hist(mc_results['unhedged_pnl'], bins=50, alpha=0.6, label='Unhedged', color='red')
axes[0].hist(mc_results['hedged_pnl'], bins=50, alpha=0.6, label='Hedged', color='green')
axes[0].axvline(0, color='black', linestyle='-', linewidth=1)
axes[0].set_xlabel('P&L (₦)')
axes[0].set_ylabel('Frequency')
axes[0].set_title('P&L Distribution')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Risk metrics
unhedged = mc_results['unhedged_pnl']
hedged = mc_results['hedged_pnl']

metrics_text = f"""
Risk Metrics:
• Worst Case (5%): Unhedged ₦{np.percentile(unhedged, 5):,.0f} | Hedged ₦{np.percentile(hedged, 5):,.0f}
• Best Case (95%): Unhedged ₦{np.percentile(unhedged, 95):,.0f} | Hedged ₦{np.percentile(hedged, 95):,.0f}
• Std Deviation: Unhedged ₦{np.std(unhedged):,.0f} | Hedged ₦{np.std(hedged):,.0f}
• Risk Reduction: {((np.std(unhedged)-np.std(hedged))/np.std(unhedged)*100):.1f}%
"""

axes[1].text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
axes[1].axis('off')
axes[1].set_title('Risk Summary')

plt.tight_layout()
st.pyplot(fig)

# Historical context
st.subheader("📈 Historical Context (2024-2025)")

st.markdown("""
    <div class="success-box">
        <strong>Key Finding from 24 Months of Data:</strong><br>
        • Mean basis: ₦884/kg (77% of local price)<br>
        • Basis stability: ±₦49/kg (5.6% standard deviation)<br>
        • This stability enables predictable partial hedging<br><br>
        <em>Backtested across 3 market regimes: hedging saved ₦35k-₦133k in adverse scenarios.</em>
    </div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Built by Okaro Okechukwu | [GitHub](https://github.com/okeson99/The-Hedger) | [LinkedIn](https://www.linkedin.com/in/okechukwu-okaro-1042422b/)")