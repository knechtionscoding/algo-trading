#!/usr/bin/env python3

from twelvedata import TDClient, exceptions
import time
import os
import logging
import csv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import dotenv

# Create a custom logger
logger = logging.getLogger("algo-trader")
hdlr = logging.StreamHandler()
# fhdlr = logging.FileHandler("myapp.log")
logger.addHandler(hdlr)
# logger.addHandler(fhdlr)
logger.setLevel(level=os.environ.get("LOG_LEVEL", "INFO").upper())

dotenv.load_dotenv(".env.paper")

# Initialize TwelveData client - apikey parameter is requiered
td = TDClient(apikey=os.getenv("TD_API_KEY"))

# paper=True enables paper trading
trading_client = TradingClient(
    os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper=True
)


def get_stock_symbols(symbols: list) -> list:
    """
    Gets the S&P 500 stock symbols from a CSV file
    """
    with open(os.getenv("CONSTITUENT_FILE"), mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                logger.debug(f'Column names are {", ".join(row)}')
                line_count += 1
            logger.debug(f'{row["Symbol"]}')
            symbols.append(row["Symbol"])
            line_count += 1

    return symbols


def get_stock_price(symbol: str) -> float:
    """
    Gets stock prices from TwelveData
    """
    price = td.price(symbol=symbol).as_json()
    # logger.info(prices)
    print(price)
    return float(price["price"])


def get_quote(symbol: str) -> float:
    logger.debug(f"getting quote for {symbol}")
    try:
        quote = td.quote(symbol=symbol).as_json()
    except exceptions.TwelveDataError:
        logger.debug(f"API Error getting quote for {symbol}")
        time.sleep(60)
        quote = get_quote(symbol)
    return quote


def calculate_should_buy(quote: dict, price: float) -> bool:
    if (
        price / float(quote["fifty_two_week"]["high"]) > 0.60
        and price / float(quote["open"]) < 0.95
    ):
        return True
    else:
        return False


def should_we_sell():
    positions = td.get_all_positions()
    for position in positions:
        if position.unrealized_plpc > 0.20:
            logger.debug(f"We should sell {position.qty} of {position.symbol}")
            sell_shares(position.symbol, position.qty)


def calculate_num_shares_to_buy(price, unit_size=10):
    return price / unit_size


def buy_shares(symbol: str, quantity: float) -> bool:
    # preparing orders
    market_order_data = MarketOrderRequest(
        symbol=symbol, qty=quantity, side=OrderSide.BUY, time_in_force=TimeInForce.DAY
    )

    # Market order
    trading_client.submit_order(order_data=market_order_data)


def run_algo(symbol):
    logger.debug(f"Running Algorithm for {symbol}")

    quote = get_quote(symbol)
    price = get_stock_price(symbol)
    if calculate_should_buy(quote=quote, price=price):
        logger.info(f"We should buy: {symbol}")
        quantity = calculate_num_shares_to_buy(price)
        logger.info(f"Buying {quantity} shares of {symbol}")
        buy_shares(symbol, quantity)


def sell_shares(symbol: str, quantity: float):
    market_order_data = MarketOrderRequest(
        symbol=symbol, qty=quantity, side=OrderSide.SELL, time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order_data=market_order_data)


if __name__ == "__main__":
    symbols = []
    symbols = get_stock_symbols(symbols)
    logger.debug(f"{symbols=}")

    group = len(symbols) // 5
    logger.debug(f"group length {group}")

    for symbol in symbols[:group]:
        run_algo(symbol)
    for symbol in symbols[group : group * 2]:
        run_algo(symbol)
    for symbol in symbols[group * 2 : group * 3]:
        run_algo(symbol)
    for symbol in symbols[group * 3 : group * 4]:
        run_algo(symbol)
    for symbol in symbols[group * 4 : group * 5]:
        run_algo(symbol)

    should_we_sell()
