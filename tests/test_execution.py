"""
Trade timing (execution): a decision made at day t's close is traded at day t+1's close.

The old engine traded at the SAME close it used to decide, which you can't do in real life.
These tests pin the new default everywhere (single asset, benchmarks, portfolio, Skeptic) and
prove the look-ahead check now catches the old timing.
"""

import numpy as np
import pandas as pd
import pytest

from lab import config
from lab.backtest import buy_and_hold, fixed_mix, run_backtest
from lab.portfolio import evaluate_portfolio, portfolio_timing_check, simulate_portfolio
from lab.skeptic import evaluate, execution_timing_check, full_lookahead_check
from run_lab import STRATEGIES
from strategies.ma_trend import MATrend
from tests.conftest import make_prices

PORT = config.PORTFOLIO_ASSETS


def test_next_close_is_the_default_everywhere():
    assert config.EXECUTION == "next_close"
    prices = make_prices([100, 100, 100, 100, 110])
    signal = pd.Series(1.0, index=prices.index)
    assert run_backtest(prices, signal).position.tolist() == [0, 0, 1, 1, 1]
    assert run_backtest(prices, signal, execution="same_close").position.tolist() == [0, 1, 1, 1, 1]


def test_unknown_execution_is_refused():
    prices = make_prices([100, 101, 102])
    with pytest.raises(ValueError, match="execution"):
        run_backtest(prices, pd.Series(1.0, index=prices.index), execution="tomorrow_open")


def test_selling_also_waits_for_the_next_close():
    # "Out" decided at day 2's close (before the -50% crash on day 3). Sold at day 3's close: too late.
    prices = make_prices([100, 100, 100, 50, 50])
    signal = pd.Series([1, 1, 0, 0, 0], index=prices.index, dtype=float)
    res = run_backtest(prices, signal, cost_multiplier=0, start=prices.index[2])
    assert res.position.tolist() == [1, 1, 0]
    assert res.equity.iloc[-1] == pytest.approx(0.5)
    old = run_backtest(prices, signal, cost_multiplier=0, execution="same_close", start=prices.index[2])
    assert old.equity.iloc[-1] == pytest.approx(1.0)   # the old engine dodged a crash it couldn't have dodged


def test_timing_check_catches_the_old_same_close_engine(demo_prices):
    prices = demo_prices["SPY"].loc["2005":"2008"]
    ok, msg = execution_timing_check(prices, execution="next_close")
    assert ok, msg
    ok, msg = execution_timing_check(prices, execution="same_close")
    assert not ok and "same closing price" in msg


def test_portfolio_timing_check_catches_same_close(demo_prices):
    prices = {a: demo_prices[a].loc["2005":"2007"] for a in PORT}
    assert portfolio_timing_check(prices, PORT, "next_close")[0]
    ok, msg = portfolio_timing_check(prices, PORT, "same_close")
    assert not ok and "same closing price" in msg


@pytest.mark.parametrize("name", list(STRATEGIES))
def test_every_strategy_passes_the_full_look_ahead_check(name, demo_prices):
    ok, msg = full_lookahead_check(STRATEGIES[name](), demo_prices["SPY"].loc["2005":"2010"])
    assert ok and "close after the decision" in msg, msg


def test_mix_rebalance_is_worked_out_a_close_early():
    # 50% in A, 50% cash, no costs. A doubles on Fri 31 Jan; the monthly rebalance trades at that close.
    idx = pd.bdate_range("2020-01-27", periods=8)          # Mon 27 Jan .. Wed 5 Feb
    closes = pd.DataFrame({"A": [100, 100, 100, 100, 200, 200, 100, 100]}, index=idx, dtype=float)
    same = fixed_mix(closes, {"A": 0.5}, cost_multiplier=0, execution="same_close")
    nxt = fixed_mix(closes, {"A": 0.5}, cost_multiplier=0, execution="next_close")
    # same_close: sized at 31 Jan's close (A worth 1.0 of 1.5) -> back to 0.75/0.75, then A halves: 1.125.
    assert same.equity.iloc[-1] == pytest.approx(1.125)
    # next_close: worked out at 30 Jan's close, when the mix was already 50/50 -> no trade, so A is still
    # 1.0 of 1.5 when it halves: 1.0.
    assert nxt.equity.iloc[-1] == pytest.approx(1.0)


def test_buy_and_hold_benchmark_is_unaffected_inside_a_window():
    # Buying and holding needs no price information, so inside a window both timings agree.
    prices = make_prices(list(np.linspace(100, 150, 30)))
    a = buy_and_hold(prices, start=prices.index[10], execution="same_close")
    b = buy_and_hold(prices, start=prices.index[10])
    assert np.allclose(a.equity, b.equity)


def test_portfolio_orders_fill_at_the_next_close(demo_prices):
    prices = {a: demo_prices[a].loc["2005":"2008"] for a in PORT}
    res = simulate_portfolio(MATrend(), prices, assets=PORT)
    signals = {a: MATrend().generate_signals(prices[a]) for a in PORT}
    for t in res.trades.itertuples():
        # The signal said "in" at the close BEFORE the entry date (the decision), and the buy filled a day later.
        cal = prices[t.asset].index
        decided = cal[cal.get_loc(t.entry) - 1]
        assert signals[t.asset].loc[decided] == 1


def test_skeptic_reports_both_timings_but_judges_next_close(demo_prices):
    ev = evaluate(MATrend(), demo_prices["SPY"], demo_prices["SPY"], "SPY", is_demo=True)
    assert set(ev.timing.index.get_level_values("execution")) == {"same_close", "next_close"}
    # The judged numbers are the next-close ones.
    assert ev.timing.loc[("test", "next_close"), "sharpe"] == pytest.approx(ev.metrics.loc[("test", "strategy"), "sharpe"])
    assert "close after the decision" in ev.checks[0].finding


def test_portfolio_evaluation_has_a_timing_table(demo_prices):
    prices = {a: demo_prices[a] for a in PORT}
    ev = evaluate_portfolio(MATrend(), prices, is_demo=True)
    assert ev.timing is not None and len(ev.timing) == 6
    assert ev.checks[0].status == "PASS", ev.checks[0].finding
