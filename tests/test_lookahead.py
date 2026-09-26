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


def test_trade_fills_at_the_next_close_not_the_decision_close():
    # A signal raised at day 3's close is BOUGHT at day 4's close, so it earns nothing until day 5.
    # Day 4's +10% jump happens after the decision but BEFORE we could trade: we must miss it.
    # (The old engine bought at day 3's close and wrongly earned the day-4 jump.)
    prices = make_prices([100, 100, 100, 100, 110, 121])
    signal = pd.Series([0, 0, 0, 1, 1, 1], index=prices.index, dtype=float)
    res = run_backtest(prices, signal, cost_multiplier=0)
    assert res.position.tolist() == [0, 0, 0, 0, 0, 1]
    assert res.equity.iloc[-1] == pytest.approx(1.10)    # only day 5's +10%
    old = run_backtest(prices, signal, cost_multiplier=0, execution="same_close")
    assert old.position.tolist() == [0, 0, 0, 0, 1, 1]
    assert old.equity.iloc[-1] == pytest.approx(1.21)    # the optimistic old answer


class PeeksTwoDaysAhead(Strategy):
    """Deliberately broken: 'buy if the price will rise from tomorrow to the day after'."""
    name = "cheater2"

    def generate_signals(self, prices):
        close = prices["Close"]
        return (close.shift(-2) > close.shift(-1)).astype(float)


def test_cheater_looks_brilliant(demo_prices):
    # Why this matters: a rule that reads the future makes a fortune in a backtest. If a result
    # ever looks this good, suspect look-ahead bias first. (Trading a day later doesn't save us
    # from a rule that reads far enough ahead; only the truncation test catches that.)
    prices = demo_prices["SPY"].loc["2010":"2012"]
    res = run_backtest(prices, PeeksTwoDaysAhead().generate_signals(prices))
    assert res.equity.iloc[-1] > 10  # >10x in 3 years: impossible without seeing the future
    assert not lookahead_check(PeeksTwoDaysAhead(), prices)[0]


def test_overfit_search_refuses_test_period_data(demo_prices):
    from strategies.overfit_demo import OverfitDemo
    with pytest.raises(ValueError, match="test period"):
        OverfitDemo().fit(demo_prices["SPY"].loc["2005":"2019"])
