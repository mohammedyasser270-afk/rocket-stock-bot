import os
import requests
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest


TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_USER_ID = os.environ["TELEGRAM_USER_ID"]

ALPACA_API_KEY = os.environ["ALPACA_API_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]


def send_telegram_message(message: str) -> None:
    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_USER_ID,
            "text": message,
        },
        timeout=30,
    )

    response.raise_for_status()


def get_latest_price(symbol: str) -> float:
    client = StockHistoricalDataClient(
        ALPACA_API_KEY,
        ALPACA_SECRET_KEY,
    )

    request = StockLatestTradeRequest(
        symbol_or_symbols=symbol
    )

    latest_trade = client.get_stock_latest_trade(request)

    return float(latest_trade[symbol].price)


def main() -> None:
    symbol = "PATH"
    price = get_latest_price(symbol)

    if 2 <= price <= 50:
        status = "✅ Passed price filter"
    else:
        status = "⛔ Outside allowed range"

    message = (
        "🚀 Rocket Scanner Test\n\n"
        f"Ticker: {symbol}\n"
        f"Latest price: ${price:.2f}\n"
        f"Allowed range: $2–$50\n"
        f"Status: {status}\n\n"
        "Data source: Alpaca"
    )

    send_telegram_message(message)


if __name__ == "__main__":
    main()
