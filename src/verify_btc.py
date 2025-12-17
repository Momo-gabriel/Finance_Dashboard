# for testing API and normalization
from api import YahooFinanceClient
from util.util import normalize_symbol

def main():
    raw = "BTC"
    normalized = normalize_symbol(raw)
    print("Raw:", raw)
    print("Normalized:", normalized)

    api = YahooFinanceClient()
    try:
        quote = api.get_quote(normalized)
        print("Quote:", quote)
    except Exception as e:
        print("Error from get_quote:", e)

if __name__ == "__main__":
    main()
