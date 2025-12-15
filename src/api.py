import yfinance as yf
import json
from datetime import datetime
from pathlib import Path
import csv
from util.util import normalize_symbol
from models import Quote, Point, Series



# Paths for cache and history
CACHE_FILE = Path("src/data/cache.json")
HISTORY_FILE = Path("src/data/history.csv")




HISTORY_FILE = Path("history.csv")

class YahooFinanceClient:
    def get_quote(self, symbol: str) -> Quote:
        """Fetch a live quote from YahooFinance. Falls back to cache.json or history.csv if offline."""
        try:
            yf_symbol = normalize_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)

            # Try fast_info first
            info = getattr(ticker, "fast_info", {})
            price = info.get("lastPrice")

            # Fallback to history if fast_info fails
            if price is None or price == 0.0:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]

            if price is None:
                price = 0.0

            quote = Quote(
                symbol=yf_symbol,
                price=price,
                change=0.0,
                change_percent=0.0,
                last_refreshed=datetime.now(),
                source="yfinance"
            )
            self._save_cache(yf_symbol, quote)
            self._save_history(quote)
            return quote

        except Exception as e:
            # Fallback logic
            norm = normalize_symbol(symbol)
            cached = self._load_cache(norm)
            if cached:
                return cached
            if HISTORY_FILE.exists():
                with HISTORY_FILE.open() as f:
                    rows = list(csv.DictReader(f))
                    for row in reversed(rows):
                        if row["symbol"] == norm:
                            return Quote(
                                symbol=row["symbol"],
                                price=float(row["price"]),
                                change=float(row.get("change", 0.0)),
                                change_percent=float(row.get("change_percent", 0.0)),
                                last_refreshed=datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S"),
                                source="offline-history"
                            )
            raise RuntimeError(f"No offline data available for {symbol}: {e}")



    def get_daily(self, symbol: str, range: str = "1mo") -> Series:
        """
        Fetch daily historical series for a symbol.
        Returns a Series of Points (time, close).
        """
        try:
            hist = yf.Ticker(symbol).history(period=range)
            points = [
                Point(time=index.to_pydatetime(), close=row["Close"])
                for index, row in hist.iterrows()
            ]
            return Series(symbol=symbol, points=points)
        except Exception:
            # Offline mode: no chart data available
            return Series(symbol=symbol, points=[])

    # --- Cache methods ---
    def _save_cache(self, symbol: str, quote: Quote):
        cache = {}
        if CACHE_FILE.exists():
            try:
                cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                cache = {}
        cache[symbol] = {
            "symbol": quote.symbol,
            "price": quote.price,
            "change": quote.change,
            "change_percent": quote.change_percent,
            "last_refreshed": quote.last_refreshed.isoformat(),
            "source": quote.source
        }
        CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")

    def _load_cache(self, symbol: str) -> Quote | None:
        if CACHE_FILE.exists():
            try:
                cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
                if symbol in cache:
                    entry = cache[symbol]
                    return Quote(
                        symbol=entry["symbol"],
                        price=entry["price"],
                        change=entry["change"],
                        change_percent=entry["change_percent"],
                        last_refreshed=datetime.fromisoformat(entry["last_refreshed"]),
                        source="cache"
                    )
            except Exception:
                pass
        return None

    # --- History methods ---
    def _save_history(self, quote: Quote):
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        write_header = not HISTORY_FILE.exists()
        with HISTORY_FILE.open("a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["symbol", "price", "change", "change_percent", "timestamp", "source"])
            writer.writerow([
                quote.symbol,
                quote.price,
                quote.change,
                quote.change_percent,
                quote.last_refreshed.strftime("%Y-%m-%d %H:%M:%S"),
                quote.source
            ])