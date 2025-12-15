import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# --- Paths ---
DATA_DIR = Path("src/data")

PORTFOLIO_FILE = DATA_DIR / "portfolio.csv"
HISTORY_FILE = DATA_DIR / "history.csv"
CACHE_FILE = DATA_DIR / "cache.json"

def ensure_data_dirs():
    """
    Ensure that the data directory and key files exist.
    Creates empty portfolio.csv, history.csv, and cache.json if missing.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not PORTFOLIO_FILE.exists():
        PORTFOLIO_FILE.write_text("symbol,quantity,buy_price\n", encoding="utf-8")

    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("symbol,price,change,change_percent,timestamp,source\n", encoding="utf-8")

    if not CACHE_FILE.exists():
        CACHE_FILE.write_text("{}", encoding="utf-8")


# --- Logging ---
def log_info(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO {ts}] {msg}")

def log_warn(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[WARN {ts}] {msg}")

def log_error(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[ERROR {ts}] {msg}")


# --- Safe parsing ---
def safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if isinstance(val, str):
            val = val.strip()
        return float(val)
    except Exception:
        return default

def safe_int(val: Any, default: int = 0) -> int:
    try:
        if isinstance(val, str):
            val = val.strip()
        return int(val)
    except Exception:
        return default


# --- Symbol normalization ---
SYMBOL_ALIASES: Dict[str, str] = {
    # Crypto
    "btc": "BTC-USD",
    "bitcoin": "BTC-USD",
    "eth": "ETH-USD",
    "ethereum": "ETH-USD",
    "egld": "EGLD-USD",

    # Forex
    "eurusd": "EURUSD=X",
    "eur-usd": "EURUSD=X",
    "eur/usd": "EURUSD=X",
    "usdrub": "USDRUB=X",
    "usd-rub": "USDRUB=X",
    "usd/rub": "USDRUB=X",
    "eurron": "EURRON=X",
    "eur-ron": "EURRON=X",
    "eur/ron": "EURRON=X",
    "usdron": "USDRON=X",
    "usd-ron": "USDRON=X",

    # Stocks
    "nvidia": "NVDA",
    "tsla": "TSLA",
    "aapl": "AAPL",
    "amd": "AMD",
    "msft": "MSFT",
}

def normalize_symbol(sym: str) -> str:
    sym = sym.strip().lower()
    return SYMBOL_ALIASES.get(sym, sym.upper())

def currency_symbol(symbol: str) -> str:
    sym = (symbol or "").upper()
    if sym.endswith("-USD") or sym.endswith("=X") or "USD" in sym:
        return "$"
    if "EUR" in sym:
        return "€"
    if "RON" in sym:
        return "lei"
    return ""


# --- CSV helpers ---
def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception as e:
        log_error(f"Failed to read CSV {path}: {e}")
        return []

def write_csv_dict(path: Path, rows: List[Dict[str, Any]], headers: Optional[List[str]] = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if headers is None and rows:
            headers = list(rows[0].keys())
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers or [])
            if headers:
                writer.writeheader()
            for r in rows:
                writer.writerow(r)
        log_info(f"Wrote {len(rows)} rows to {path}")
    except Exception as e:
        log_error(f"Failed to write CSV {path}: {e}")


# --- JSON helpers ---
def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log_warn(f"Failed to load JSON {path}: {e}")
        return default

def save_json(path: Path, obj: Any):
    try:
        if is_dataclass(obj):
            obj = asdict(obj)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        log_info(f"Saved JSON to {path}")
    except Exception as e:
        log_error(f"Failed to save JSON {path}: {e}")


# --- Datetime helpers ---
ISO_FORMAT = "%Y-%m-%d %H:%M:%S"

def to_iso(dt: datetime) -> str:
    return dt.strftime(ISO_FORMAT)

def from_iso(s: str) -> datetime:
    return datetime.strptime(s, ISO_FORMAT)


# --- Tkinter helpers ---
class Debouncer:
    def __init__(self, root, delay_ms: int = 400):
        self.root = root
        self.delay_ms = delay_ms
        self._after_id: Optional[str] = None

    def call(self, fn: Callable, *args, **kwargs):
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(self.delay_ms, lambda: fn(*args, **kwargs))


# --- Portfolio file helpers ---
def load_portfolio_rows() -> List[Dict[str, str]]:
    rows = read_csv_dict(PORTFOLIO_FILE)
    normalized: List[Dict[str, str]] = []
    for r in rows:
        sym = normalize_symbol(r.get("symbol", ""))
        qty = r.get("quantity", "0")
        bp = r.get("buy_price", "0")
        normalized.append({"symbol": sym, "quantity": qty, "buy_price": bp})
    return normalized

def save_portfolio_rows(rows: List[Dict[str, Any]]):
    headers = ["symbol", "quantity", "buy_price"]
    write_csv_dict(PORTFOLIO_FILE, rows, headers=headers)


# --- History helpers ---
def append_history_row(row: Dict[str, Any]):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    write_header = not HISTORY_FILE.exists()
    try:
        with HISTORY_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["symbol", "price", "change", "change_percent", "timestamp", "source"]
            )
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        log_info(f"Appended history: {row.get('symbol')}")
    except Exception as e:
        log_error(f"Failed to append history: {e}")


# --- Cache helpers ---
def save_quote_cache(symbol: str, quote: Dict[str, Any]):
    cache = load_json(CACHE_FILE, default={}) or {}
    cache[symbol] = quote
    save_json(CACHE_FILE, cache)

def load_quote_cache(symbol: str) -> Optional[Dict[str, Any]]:
    cache = load_json(CACHE_FILE, default={}) or {}
    return cache.get(symbol)


# --- Validation helpers ---
def validate_holding(symbol: str, quantity: Any, buy_price: Any) -> Tuple[bool, str]:
    sym = normalize_symbol(symbol)
    if not sym:
        return False, "Symbol is required."
    try:
        qty = float(quantity)
        bp = float(buy_price)
    except Exception:
        return False, "Quantity and Buy Price must be numbers."
    if qty <= 0:
        return False, "Quantity must be greater than 0."
    if bp < 0:
        return False, "Buy Price cannot be negative."
    return True, ""


# --- Formatting helpers ---
def fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"

def fmt_percent(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}%"

def fmt_signed(value: Optional[float]) -> str:
    if value is None:
        return "-"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}"

def fmt_currency(value: Optional[float], symbol: str = "") -> str:
    if value is None:
        return "-"
    return f"{symbol}{value:.2f}" if symbol else f"{value:.2f}"


# --- Math helpers ---
def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp x between lo and hi."""
    return max(lo, min(hi, x))

def round_to(x: Optional[float], decimals: int = 2) -> Optional[float]:
    """Round a number safely to given decimals."""
    if x is None:
        return None
    try:
        return round(float(x), decimals)
    except Exception:
        return None


# --- String helpers ---
def safe_str(val: Any, default: str = "") -> str:
    """Convert to string safely."""
    try:
        return "" if val is None else str(val)
    except Exception:
        return default


# --- Export control ---
__all__ = [
    # paths & init
    "DATA_DIR",
    "PORTFOLIO_FILE",
    "HISTORY_FILE",
    "CACHE_FILE",
    "ensure_data_dirs",
    # logging
    "log_info",
    "log_warn",
    "log_error",
    # parsing
    "safe_float",
    "safe_int",
    # normalization & currency
    "normalize_symbol",
    "currency_symbol",
    # CSV/JSON
    "read_csv_dict",
    "write_csv_dict",
    "load_json",
    "save_json",
    # datetime
    "ISO_FORMAT",
    "to_iso",
    "from_iso",
    # tkinter
    "Debouncer",
    # portfolio IO
    "load_portfolio_rows",
    "save_portfolio_rows",
    # history/cache
    "append_history_row",
    "save_quote_cache",
    "load_quote_cache",
    # validation
    "validate_holding",
    # formatting
    "fmt_money",
    "fmt_percent",
    "fmt_signed",
    "fmt_currency",
    # math & string
    "clamp",
    "round_to",
    "safe_str",
]