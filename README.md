# Finance_Dashboard
My first dashboard
#  Finance Dashboard

A Python-based finance dashboard with a **Tkinter GUI** that lets you:
- Track your portfolio holdings with live profit/loss calculations
- View real-time market data and interactive charts
- Persist holdings locally in CSV for offline use
- Fetch quotes and historical data via [yfinance](https://github.com/ranaroussi/yfinance)

---

##  Features
- **Portfolio Tab**
  - Add/remove holdings (symbol, quantity, buy price)
  - Automatic enrichment with live quotes (stocks, crypto, forex)
  - Profit/Loss (absolute and %) with color-coded rows
  - Persistent storage in `src/data/portfolio.csv`

- **Market Data Tab**
  - Load any symbol (e.g. `AAPL`, `BTC-USD`, `EURUSD=X`)
  - Select time ranges (`1mo`, `6mo`, `1y`, `5y`, `10y`, `max`)
  - Interactive matplotlib chart embedded in Tkinter
  - Current price label with currency symbol

- **Backend**
  - `YahooFinanceClient` wraps yfinance for quotes and history
  - Fallback to local cache/history if offline
  - Normalization for crypto and forex tickers

---

##  Project Structure

Finance_Dashboard/ ├── src/
                   │   ├── main.py              # Entry point: launches 
                   │   ├── api.py              # YahooFinanceClient for quotes & history 
                   │   ├── models.py           # Quote, Point, Series dataclasses
                   │   ├── portfolio.py         # Portfolio persistence (add/remove/enrich) 
                   │   ├── ui/ 
                   │   │   └── ui.py           # Tkinter GUI: PortfolioUI & MarketDataUI 
                   │   ├── util/ 
                   │   │   └── util.py         # Normalization, formatting helpers 
                   │   └── data/ 
                   │       ├── portfolio.csv   # Persistent holdings 
                   │       └── cache.json      # Cached quotes 
                   ├── README.md 
                   └── requirements.txt

---

##  Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/Momo-gabriel/Finance_Dashboard
   cd Finance_Dashboard


- Install dependencies:
pip install -r requirements.txt


- requirements.txt should include:
matplotlib
yfinance
pandas
requests
numpy
python-dateutil

Also you can use:
uv sync



 Usage
Run the dashboard:
python src/main.py


- Use the Portfolio tab to add holdings (e.g. BTC-USD, qty 0.5, buy price 40000).
- Switch to the Market Data tab to load a symbol and view its chart.
- Click Refresh to update portfolio values with live data.

 Notes
- Crypto tickers: BTC-USD, ETH-USD
- Forex tickers: EURUSD=X, USDJPY=X
- Stock tickers: AAPL, MSFT, etc.
- If live data fails, the app falls back to cached or historical CSV.
