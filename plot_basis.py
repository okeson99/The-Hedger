import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

print("Loading data...")

# Load local maize data
maize = pd.read_excel(r"C:\Users\Okaro\Desktop\The-Hedger\nbs_maize_filtered.xlsx")
maize['Date'] = pd.to_datetime(maize['Date'], dayfirst=True, errors='coerce')
maize['YearMonth'] = maize['Date'].dt.to_period('M').dt.to_timestamp()
monthly_maize = maize.groupby('YearMonth')['UPRICE'].mean().reset_index()

# Load global corn data
corn = yf.download("ZC=F", period="5y", interval="1d")
ngn = yf.download("NGN=X", period="5y", interval="1d")

corn_close = corn['Close'].squeeze() / 100  # cents to dollars
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

# Merge and calculate basis
merged = pd.merge(monthly_maize, global_price, on='YearMonth', how='inner')
merged['Basis_NGN_per_kg'] = merged['UPRICE'] - merged['CBOT_Corn_NGN_per_kg']
merged['Basis_pct'] = (merged['Basis_NGN_per_kg'] / merged['UPRICE']) * 100

print(f"Data loaded: {len(merged)} months")

# Plot
fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

axes[0].plot(merged['YearMonth'], merged['UPRICE'], label='Nigerian Maize (₦/kg)', linewidth=2, marker='o')
axes[0].plot(merged['YearMonth'], merged['CBOT_Corn_NGN_per_kg'], label='CBOT Corn (₦/kg)', linewidth=2, marker='s')
axes[0].set_ylabel('Price (₦/kg)', fontsize=12)
axes[0].set_title('Nigerian Maize vs. CBOT Corn (Converted to ₦/kg)', fontsize=14, fontweight='bold')
axes[0].legend(loc='upper left')
axes[0].grid(True, alpha=0.3)

axes[1].plot(merged['YearMonth'], merged['Basis_NGN_per_kg'], color='red', linewidth=2, marker='o')
axes[1].axhline(y=merged['Basis_NGN_per_kg'].mean(), color='black', linestyle='--', 
                label=f'Mean Basis: ₦{merged["Basis_NGN_per_kg"].mean():.0f}/kg')
axes[1].fill_between(merged['YearMonth'], 
                     merged['Basis_NGN_per_kg'].mean() - merged['Basis_NGN_per_kg'].std(),
                     merged['Basis_NGN_per_kg'].mean() + merged['Basis_NGN_per_kg'].std(),
                     alpha=0.2, color='red', label='±1 Std Dev')
axes[1].set_ylabel('Basis (₦/kg)', fontsize=12)
axes[1].set_title('Basis Stability: Local Premium Over Global Price', fontsize=14, fontweight='bold')
axes[1].legend(loc='upper left')
axes[1].grid(True, alpha=0.3)

axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
axes[1].xaxis.set_major_locator(mdates.MonthLocator(interval=2))
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('basis_analysis.png', dpi=300, bbox_inches='tight')
print("Chart saved as 'basis_analysis.png'")

plt.show()