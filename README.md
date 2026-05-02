# The Hedger

**Quantitative risk management tools for African agriculture.**

## The Problem

African farmers face volatile commodity prices with limited access to hedging 
instruments. Existing tools are either too expensive, too complex, or 
non-existent for local markets.

## The Solution

A web-based tool that helps maize farmers and cooperatives:

- Estimate optimal hedge ratios using local and global price data
- Run scenario analysis across price, basis, and currency risk
- Receive plain-language recommendations with visual P&L outcomes

## Current Status

🚧 **Month 1: MVP Build In Progress**  
Target: Working maize hedge model + white paper by Day 30

## Key Finding: Basis Stability

Analysis of 24 months of data (Jan 2024–Dec 2025) reveals:

- **Nigerian maize wholesale price**: ₦1,070–₦1,260/kg
- **CBOT corn (converted to ₦/kg)**: ₦160–₦300/kg
- **Mean basis**: ₦884/kg (77% of local price)
- **Basis standard deviation**: ₦49/kg (5.6% of mean)

**Implication**: The local premium over global prices is stable enough to enable 
partial hedging of the global-correlated price component.

## Tech Stack

- Python (pandas, numpy, yfinance, matplotlib)
- FastAPI (backend)
- Streamlit (frontend MVP)
- PostgreSQL (data)
- Render (deployment)

## Data Sources

- CBOT Corn Futures (yfinance)
- NGN/USD Exchange Rates (yfinance)
- Nigerian Maize Spot Prices (NBS Nigeria)

## Roadmap

| Phase | Target | Deliverable |
|-------|--------|-------------|
| Month 1 | Day 30 | Working MVP + White Paper |
| Month 2 | Day 60 | Pilot with 1–3 farms/cooperatives |
| Month 3 | Day 90 | Refined product + monetization path |

## About

Built by Okaro Okechukwu.  
Finance professional. Mathematics background. Believes complex tools should 
serve real people.

[LinkedIn](https://www.linkedin.com/in/okechukwu-okaro-1042422b/) | 
[GitHub](https://github.com/okeson99)

## License

MIT
## Live Demo

Try the tool: [https://the-hedger-kbrfkayxhtwumpp5quogpw.streamlit.app/](https://the-hedger-kbrfkayxhtwumpp5quogpw.streamlit.app/)
