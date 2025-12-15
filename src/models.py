from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Quote:
    symbol: str
    price: float
    change: float
    change_percent: float
    last_refreshed: datetime
    source: str
    quantity: float = 0.0
    cost_basis: float = 0.0

@dataclass
class Point:
    time: datetime
    close: float

@dataclass
class Series:
    symbol: str
    points: List[Point]

class Config:
    """Global configuration constants for the dashboard."""
    DEFAULT_CLIENT = "YahooFinance"
    REFRESH_INTERVAL = 60   # seconds
    OFFLINE_CACHE = "src/data/cache.json"

def get_client(name: str = None):
    """Factory to return the correct API client."""
    from api import YahooFinanceClient
    if name is None or name == Config.DEFAULT_CLIENT:
        return YahooFinanceClient()
    raise ValueError(f"Unknown client: {name}")