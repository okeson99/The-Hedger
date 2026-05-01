import pandas as pd
import yfinance as yf


def get_current_prices():
    """Fetch current CBOT corn and NGN/USD, convert to N/kg"""
    corn = yf.download("ZC=F", period="5d", interval="1d")
    ngn = yf.download("NGN=X", period="5d", interval="1d")
    
    corn_close = corn['Close'].squeeze().iloc[-1] / 100
    ngn_close = ngn['Close'].squeeze().iloc[-1]
    
    bushel_to_kg = 25.4
    corn_ngn_per_kg = (corn_close / bushel_to_kg) * ngn_close
    
    return corn_ngn_per_kg


def recommend_hedge(yield_kg, planting_month, harvest_month, risk_tolerance, current_local_price):
    """
    Recommend hedge ratio based on farmer inputs
    """
    hedge_ratios = {
        'conservative': 0.40,
        'moderate': 0.25,
        'aggressive': 0.10
    }
    
    hedge_ratio = hedge_ratios.get(risk_tolerance.lower(), 0.25)
    
    contract_month = (harvest_month % 12) + 1
    contract_year = 2026 if harvest_month >= 12 else 2025
    
    global_price = get_current_prices()
    basis = current_local_price - global_price
    
    hedge_quantity_kg = yield_kg * hedge_ratio
    
    kg_to_bushel = 1 / 25.4
    hedge_quantity_bushels = hedge_quantity_kg * kg_to_bushel
    
    contract_size = 5000
    num_contracts = round(hedge_quantity_bushels / contract_size)
    
    margin_per_contract_usd = 1500
    ngn_usd = yf.download("NGN=X", period="1d", interval="1d")['Close'].squeeze()
    margin_per_contract_ngn = margin_per_contract_usd * ngn_usd
    total_margin = num_contracts * margin_per_contract_ngn
    
    price_drop = 0.20
    
    unhedged_loss = yield_kg * current_local_price * price_drop
    
    hedged_spot_loss = hedge_quantity_kg * current_local_price * price_drop
    futures_gain = hedge_quantity_kg * global_price * price_drop
    net_hedged_loss = unhedged_loss - futures_gain
    
    return {
        'hedge_ratio': hedge_ratio,
        'hedge_quantity_kg': hedge_quantity_kg,
        'num_contracts': num_contracts,
        'contract_month': contract_month,
        'contract_year': contract_year,
        'current_global_price_ngn_kg': global_price,
        'basis': basis,
        'total_margin_ngn': total_margin,
        'scenario_price_drop': price_drop,
        'unhedged_loss_ngn': unhedged_loss,
        'hedged_loss_ngn': net_hedged_loss,
        'savings_ngn': unhedged_loss - net_hedged_loss
    }


if __name__ == "__main__":
    result = recommend_hedge(
        yield_kg=10000,
        planting_month=4,
        harvest_month=10,
        risk_tolerance='moderate',
        current_local_price=1150
    )
    
    # Check scale feasibility
    if result['num_contracts'] == 0:
        print("\n" + "="*60)
        print("SCALE WARNING")
        print("="*60)
        print(f"Your hedge quantity ({result['hedge_quantity_kg']:,.0f} kg) is too small")
        print("for direct CBOT futures (minimum: ~127,000 kg equivalent).")
        print("\nRecommended alternatives:")
        print("1. Join a cooperative/aggregator to pool volume")
        print("2. Use OTC forward contracts with local buyers")
        print("3. Increase hedge ratio if risk tolerance allows")
        print("="*60 + "\n")
    
    print("HEDGE RECOMMENDATION:")
    for key, value in result.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:,.2f}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\nBottom line: Hedging saves ₦{result['savings_ngn']:,.2f} if prices drop 20%")