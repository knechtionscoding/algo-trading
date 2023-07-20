from __future__ import annotations

import pytest

import main


@pytest.mark.parametrize(
    "quote,price,result",
    [
        ({"fifty_two_week": {"high": 100}, "open": 95}, 85.0, True),
        ({"fifty_two_week": {"high": 100}, "open": 50}, 45.0, False),
        ({"fifty_two_week": {"high": 100}, "open": 95}, 93.0, False),
    ],
)
def test_calulate_should_buy(quote, price, result):
    assert (main.calculate_should_buy(quote, price)) == result
