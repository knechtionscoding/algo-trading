#!/usr/bin/env python3
import csv
import logging
import os
import sys
import time

import dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide
from alpaca.trading.enums import TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from requests import exceptions as r_exceptions
from retry import retry
from twelvedata import exceptions
from twelvedata import TDClient
from urllib3 import exceptions as url_exceptions

dotenv.load_dotenv(".env.paper")

logging.basicConfig()

# Create a custom logger
logger = logging.getLogger("algo-trader")

hdlr = logging.StreamHandler()
# fhdlr = logging.FileHandler("myapp.log")
logger.addHandler(hdlr)
# logger.addHandler(fhdlr)
logger.setLevel(level=os.environ.get("LOG_LEVEL", "DEBUG").upper())


# Initialize TwelveData client - apikey parameter is requiered
twelve_data = TDClient(apikey=os.environ.get("TD_API_KEY", "FAKE-KEY"))

# paper=True enables paper trading
alpaca_client = TradingClient(
    os.environ.get("ALPACA_API_KEY", "FAKE-KEY"),
    os.environ.get("ALPACA_SECRET_KEY", "FAKE-KEY"),
    paper=True,
)


def get_stock_symbols(symbols: list) -> list:
    """
    Gets the S&P 500 stock symbols from a CSV file
    """
    with open(os.environ.get("CONSTITUENT_FILE"), mode="r") as csv_file:
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
    price = twelve_data.price(symbol=symbol).as_json()
    # logger.info(prices)
    logger.debug(price)
    return float(price["price"])


@retry(
    (r_exceptions.ConnectionError, url_exceptions.NameResolutionError),
    delay=1,
    backoff=2,
    max_delay=4,
    tries=5,
)
def get_quote(symbol: str) -> float:
    logger.debug(f"Getting quote for {symbol}")
    quote = {}
    try:
        quote = twelve_data.quote(symbol=symbol).as_json()
    except exceptions.TwelveDataError:
        logger.debug(f"API Error getting quote for {symbol}")
        time.sleep(60)
        quote = get_quote(symbol)
    return quote


def calculate_should_buy(quote: dict, price: float) -> bool:
    logger.debug(
        f"Current percentage off of 52 week high {price / float(quote['fifty_two_week']['high'])}"
    )
    logger.debug(
        f"Current percentage off of open price: {price / float(quote['open'])}"
    )
    if (
        price / float(quote["fifty_two_week"]["high"]) > 0.60
        and price / float(quote["open"]) < 0.95
    ):
        return True
    else:
        return False


def should_we_sell():
    positions = alpaca_client.get_all_positions()
    for position in positions:
        logger.debug(float(position.unrealized_plpc))
        if float(position.unrealized_plpc) > 0.30:
            logger.info(f"We should sell {position.qty} of {position.symbol}")
            sell_shares(position.symbol, position.qty)


def calculate_num_shares_to_buy(price, unit_size=10):
    return unit_size / price


def buy_shares(symbol: str, quantity: float) -> bool:
    # preparing orders
    logger.info(f"Buying {quantity} shares of {symbol}")
    market_order_data = MarketOrderRequest(
        symbol=symbol, qty=quantity, side=OrderSide.BUY, time_in_force=TimeInForce.DAY
    )

    # Market order
    alpaca_client.submit_order(order_data=market_order_data)


def run_algo(symbol):
    logger.debug(f"Running Algorithm for {symbol}")

    quote = get_quote(symbol)
    logger.debug(f"{quote=}")
    price = get_stock_price(symbol)
    logger.debug(f"{price}")
    if calculate_should_buy(quote=quote, price=price):
        logger.info(f"We should buy: {symbol}")
        quantity = calculate_num_shares_to_buy(price)
        logger.info(f"Buying {quantity} shares of {symbol}")
        buy_shares(symbol, quantity)


def sell_shares(symbol: str, quantity: float):
    market_order_data = MarketOrderRequest(
        symbol=symbol, qty=quantity, side=OrderSide.SELL, time_in_force=TimeInForce.DAY
    )
    alpaca_client.submit_order(order_data=market_order_data)


if __name__ == "__main__":
    while True:
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

        print(alpaca_client.get_clock().is_open)
        if not alpaca_client.get_clock().is_open:
            sys.exit()

        time.sleep(300)
