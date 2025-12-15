import csv
from pathlib import Path
from util.util import normalize_symbol, currency_symbol, safe_float


PORTFOLIO_FILE = Path("src/data/portfolio.csv")

def _load_portfolio() -> list[dict]:
    """Load portfolio holdings from local CSV file."""
    if PORTFOLIO_FILE.exists():
        holdings = []
        with PORTFOLIO_FILE.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                holdings.append({
                    "symbol": normalize_symbol(row.get("symbol", "")),
                    "quantity": safe_float(row.get("quantity", 0)),
                    "buy_price": safe_float(row.get("buy_price", 0.0))
                })
        return holdings
    return []

def _save_portfolio(holdings: list[dict]):
    """Save portfolio holdings to local CSV file."""
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PORTFOLIO_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "quantity", "buy_price"])
        writer.writeheader()
        for h in holdings:
            writer.writerow(h)

def add_holding(symbol: str, quantity: float, buy_price: float):
    """Add a new holding to the portfolio."""
    holdings = _load_portfolio()
    symbol = normalize_symbol(symbol)
    holdings.append({
        "symbol": symbol,
        "quantity": quantity,
        "buy_price": buy_price
    })
    _save_portfolio(holdings)

def remove_holding(symbol: str):
    """Remove a holding from the portfolio by symbol."""
    holdings = _load_portfolio()
    holdings = [h for h in holdings if h["symbol"] != normalize_symbol(symbol)]
    _save_portfolio(holdings)

def enrich_portfolio(api_client) -> list[dict]:
    """Return portfolio with computed values and live/current prices."""
    holdings = _load_portfolio()
    enriched = []
    for h in holdings:
        symbol = h["symbol"]
        qty = h["quantity"]
        buy_price = h["buy_price"]
        total_spent = qty * buy_price

        try:
            quote = api_client.get_quote(symbol)
            current_price = quote.price
            value = qty * current_price
            pl = value - total_spent
            pl_percent = (pl / total_spent * 100) if total_spent else 0.0
            enriched.append({
                "symbol": symbol,
                "quantity": qty,
                "buy_price": buy_price,
                "total_spent": total_spent,
                "current_price": current_price,
                "value": value,
                "pl": pl,
                "pl_percent": pl_percent,
                "currency": currency_symbol(symbol),
                "source": quote.source
            })
        except Exception:
            enriched.append({
                "symbol": symbol,
                "quantity": qty,
                "buy_price": buy_price,
                "total_spent": total_spent,
                "current_price": None,
                "value": None,
                "pl": 0.0,
                "pl_percent": 0.0,
                "currency": currency_symbol(symbol),
                "source": "local-cache"
            })
    return enriched