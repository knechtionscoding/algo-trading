# Algo Trading

This is an attempt at algorithmic trading. I'll start off with a simple algorithm and expand from there.

## Buy the Dip Algorithm

### Target Company Profile

Fortune 1000 company

### Indicators

#### Buy

- Drop of 5%+ in a single trading day
- No more than 40% off All Time high
- Have we purchased this stock in the last 1 day

#### Sell

- 30% return

## Development Configuration

### Pre-requisites

- python
- poetry
- API keys for ALPACA and Twelvedata in environment variables.


### Notable Dependencies

1. Uses [TwelveData](https://github.com/twelvedata/twelvedata-python)
   1. Specifically uses the price call. Example response:
    ```json
      {
        "symbol": "AAPL",
        "name": "Apple Inc",
        "exchange": "NASDAQ",
        "mic_code": "XNAS",
        "currency": "USD",
        "datetime": "2021-09-16",
        "timestamp": 1631772000,
        "open": "148.44000",
        "high": "148.96840",
        "low": "147.22099",
        "close": "148.85001",
        "volume": "67903927",
        "previous_close": "149.09000",
        "change": "-0.23999",
        "percent_change": "-0.16097",
        "average_volume": "83571571",
        "rolling_1d_change": "123.123",
        "rolling_7d_change": "123.123",
        "rolling_period_change": "123.123"
        "is_market_open": false,
        "fifty_two_week": {
            "low": "103.10000",
            "high": "157.25999",
            "low_change": "45.75001",
            "high_change": "-8.40999",
            "low_change_percent": "44.37440",
            "high_change_percent": "-5.34782",
            "range": "103.099998 - 157.259995"
        },
        "extended_change": "0.09",
        "extended_percent_change": "0.05",
        "extended_price": "125.22",
        "extended_timestamp": 1649845281
      }
    ```
2. Uses [Alpaca](https://github.com/alpacahq/alpaca-py)
