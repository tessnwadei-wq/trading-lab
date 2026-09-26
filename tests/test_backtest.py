import pandas as pd
import pytest

from lab import config
from lab.backtest import buy_and_hold, run_backtest
from tests.conftest import make_prices

C = config.COST_PER_TRADE  # 0.15%


def test_costs_default_to_the_project_rules():
    assert config.COMMISSION == 0.0010
    assert config.SLIPPAGE == 0.0005


def test_buy_and_hold_pays_one_entry_cost():
    prices = make_prices([100, 100, 120])
    res = buy_and_hold(prices)
    # Day 0: no position yet. Day 1: bought (pay cost), price flat. Day 2: +20%.
    assert res.equity.iloc[-1] == pytest.approx((1 - C) * 1.2)
    assert res.n_trades == 1


def test_round_trip_pays_cost_twice_and_double_costs_double_it():
    prices = make_prices([100] * 6)
    signal = pd.Series([1, 1, 0, 0, 0, 0], index=prices.index, dtype=float)
    normal = run_backtest(prices, signal)
    double = run_backtest(prices, signal, cost_multiplier=2)
    assert normal.equity.iloc[-1] == pytest.approx((1 - C) ** 2)
    assert double.equity.iloc[-1] == pytest.approx((1 - 2 * C) ** 2)
    assert normal.n_trades == 1


def test_cash_earns_nothing_and_misses_moves():
    prices = make_prices([100, 50, 25, 200])
    signal = pd.Series(0.0, index=prices.index)
    assert run_backtest(prices, signal).equity.iloc[-1] == 1.0


def test_trades_are_listed_with_returns():
    prices = make_prices([100, 100, 110, 110, 100, 100, 100, 90])
    signal = pd.Series([1, 1, 1, 0, 0, 1, 1, 1], index=prices.index, dtype=float)
    res = run_backtest(prices, signal, cost_multiplier=0)
    assert len(res.trades) == 2
    first, second = res.trades.iloc[0], res.trades.iloc[1]
    assert first["return"] == pytest.approx(0.10)  # held through the 100 -> 110 move
    assert bool(first["closed"]) and not bool(second["closed"])  # second still open at the end


def test_window_starts_in_cash_and_pays_to_enter():
    prices = make_prices([100, 100, 100, 100])
    signal = pd.Series(1.0, index=prices.index)
    res = run_backtest(prices, signal, start=prices.index[2])
    assert res.equity.iloc[-1] == pytest.approx(1 - C)
