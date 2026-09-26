"""Cash interest: money waiting in cash earns the T-bill rate, and Sharpe is measured above it."""

import numpy as np
import pandas as pd
import pytest

from lab.backtest import run_backtest
from lab.cash import align_cash, daily_cash_returns
from lab.metrics import result_sharpe, sharpe
from tests.conftest import make_prices


def irx(values, start="2020-01-01"):
    """IRX-style data: the yearly rate in %."""
    return make_prices(values, start)


def test_rate_is_converted_to_daily_and_lagged_one_day():
    daily = daily_cash_returns(irx([5.04, 2.52, 2.52]))
    # 5.04% a year / 252 days = 0.02% a day, but only from the NEXT day (known in advance).
    assert daily.iloc[0] == pytest.approx(0.0504 / 252)
    assert daily.index[0] == pd.bdate_range("2020-01-01", periods=2)[1]
    assert len(daily) == 2


def test_cash_earns_interest_when_out_of_the_market():
    prices = make_prices([100, 50, 25, 200, 100])
    rate = daily_cash_returns(irx([2.52] * 5))  # 0.01% a day
    res = run_backtest(prices, pd.Series(0.0, index=prices.index), cash_rate=rate)
    # Never invested: 4 days of interest (the first day has no known rate yet).
    assert res.equity.iloc[-1] == pytest.approx(1.0001 ** 4)


def test_invested_days_earn_the_asset_not_the_cash_rate():
    prices = make_prices([100, 100, 110, 110])
    rate = daily_cash_returns(irx([25.2] * 4))  # 0.1% a day, exaggerated so it's visible
    signal = pd.Series([1, 1, 1, 1], index=prices.index, dtype=float)
    res = run_backtest(prices, signal, cost_multiplier=0, cash_rate=rate)
    assert res.equity.iloc[-1] == pytest.approx(1.10)  # all asset, no interest


def test_missing_irx_warns_and_cash_earns_zero():
    with pytest.warns(UserWarning, match="python run_lab.py --refresh"):
        assert daily_cash_returns(None) is None
    idx = pd.bdate_range("2020-01-01", periods=3)
    assert align_cash(None, idx).tolist() == [0.0, 0.0, 0.0]


def test_align_fills_days_the_bill_market_was_closed():
    rate = pd.Series([0.001, 0.002], index=pd.to_datetime(["2020-01-02", "2020-01-06"]))
    idx = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"])
    assert align_cash(rate, idx).tolist() == [0.0, 0.001, 0.001, 0.002]


def test_sharpe_is_measured_above_the_cash_rate():
    rng = np.random.default_rng(1)
    idx = pd.bdate_range("2020-01-01", periods=500)
    r = pd.Series(0.0004 + 0.01 * rng.standard_normal(500), index=idx)
    cash = pd.Series(0.0002, index=idx)
    assert sharpe(r, cash) < sharpe(r)
    assert sharpe(r, cash) == pytest.approx(sharpe(r - 0.0002))
    # Holding only cash: no extra return over cash, so Sharpe 0.
    prices = make_prices([100] * 50)
    res = run_backtest(prices, pd.Series(0.0, index=prices.index), cash_rate=pd.Series(0.0002, index=prices.index))
    assert result_sharpe(res) == pytest.approx(0.0, abs=1e-9)
