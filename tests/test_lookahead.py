"""
Look-ahead bias tests: the most important tests in the lab.

Look-ahead bias = accidentally using information you wouldn't have had at the time.
It makes backtests look amazing and is the #1 way beginners fool themselves.
"""

import numpy as np
import pandas as pd
import pytest

from lab.backtest import run_backtest
from lab.skeptic import lookahead_check
from run_lab import STRATEGIES
from strategies.base import Strategy
from tests.conftest import make_prices


class CheatingStrategy(Strategy):
    """Deliberately broken: 'buy if TOMORROW's price is higher'. Must be caught."""
    name = "cheater"

    def generate_signals(self, prices):
        return (prices["Close"].shift(-1) > prices["Close"]).astype(float)


@pytest.mark.parametrize("name", list(STRATEGIES))
def test_every_registered_strategy_passes_truncation_test(name, demo_prices):
    prices = demo_prices["SPY"].loc["2005":"2012"]
    ok, msg = lookahead_check(STRATEGIES[name](), prices)
    assert ok, msg


def test_cheating_strategy_is_caught(demo_prices):
    ok, msg = lookahead_check(CheatingStrategy(), demo_prices["SPY"].loc["2005":"2012"])
    assert not ok
    assert "future" in msg


def test_backtester_acts_one_day_after_the_signal():
    # Price jumps +10% on day 3. A signal raised ON day 3 (after seeing the jump)
    # must NOT earn that jump; it only affects day 4 onwards.
    prices = make_prices([100, 100, 100, 110, 110, 110])
    signal = pd.Series([0, 0, 0, 1, 1, 1], index=prices.index, dtype=float)
    res = run_backtest(prices, signal, cost_multiplier=0)
    assert res.position.tolist() == [0, 0, 0, 0, 1, 1]
    assert res.equity.iloc[-1] == pytest.approx(1.0)  # we missed the jump, as we should


def test_cheater_looks_brilliant_without_the_lag(demo_prices):
    # Why this matters: the cheating rule makes a fortune in a backtest. If a result
    # ever looks this good, suspect look-ahead bias first.
    prices = demo_prices["SPY"].loc["2010":"2012"]
    # Even with the backtester's one-day delay, the cheater still "knows" the next move,
    # because its rule reads tomorrow's price.
    res = run_backtest(prices, CheatingStrategy().generate_signals(prices))
    assert res.equity.iloc[-1] > 10  # >10x in 3 years: impossible without seeing the future


def test_overfit_search_refuses_test_period_data(demo_prices):
    from strategies.overfit_demo import OverfitDemo
    with pytest.raises(ValueError, match="test period"):
        OverfitDemo().fit(demo_prices["SPY"].loc["2005":"2019"])
