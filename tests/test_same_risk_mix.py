"""The same-risk mix: X% in the asset, the rest in cash, with X set on training data only."""

import numpy as np
import pandas as pd
import pytest

from lab import config
from lab.backtest import buy_and_hold, fixed_mix, run_backtest
from lab.metrics import volatility
from lab.skeptic import evaluate, same_risk_weight
from strategies.ma_trend import MATrend
from tests.conftest import make_prices


def test_fixed_mix_half_in_asset_half_in_cash():
    prices = make_prices([100, 100, 110])  # +10% on the last day
    res = fixed_mix(prices[["Close"]], {"Close": 0.5}, cost_multiplier=0)
    assert res.equity.iloc[-1] == pytest.approx(1.05)
    assert res.position.iloc[0] == 0.5


def test_fixed_mix_cash_part_earns_interest_and_entry_pays_costs():
    prices = make_prices([100] * 4)
    cash = pd.Series(0.001, index=prices.index)
    res = fixed_mix(prices[["Close"]], {"Close": 0.5}, cash_rate=cash)
    buy_cost = 0.5 * config.COST_PER_TRADE
    assert res.equity.iloc[-1] == pytest.approx((1 - buy_cost) * (0.5 + 0.5 * 1.001 ** 4))


def test_fully_invested_mix_matches_buy_and_hold():
    rng = np.random.default_rng(0)
    prices = make_prices(100 * np.cumprod(1 + 0.01 * rng.standard_normal(300)))
    mix = fixed_mix(prices[["Close"]], {"Close": 1.0}, start=prices.index[10])
    bh = buy_and_hold(prices, start=prices.index[10])
    # Tiny difference allowed: the mix pays the entry cost before day one's move, buy_and_hold after it.
    assert mix.equity.iloc[-1] == pytest.approx(bh.equity.iloc[-1], rel=1e-4)


def test_monthly_rebalancing_brings_the_mix_back_to_target():
    # Asset doubles in January; in February the mix is reset to 50/50 (and pays for that trade).
    idx = pd.bdate_range("2020-01-01", "2020-02-05")
    close = np.where(idx < "2020-01-15", 100.0, 200.0)
    res = fixed_mix(pd.DataFrame({"A": close}, index=idx), {"A": 0.5}, cost_multiplier=0)
    jan_end = res.equity.loc[:"2020-01-31"].iloc[-1]
    assert jan_end == pytest.approx(1.5)
    assert res.equity.iloc[-1] == pytest.approx(1.5)


def test_same_risk_weight_matches_volatility_and_caps_at_one():
    rng = np.random.default_rng(3)
    prices = make_prices(100 * np.cumprod(1 + 0.01 * rng.standard_normal(400)))
    half = pd.Series(0.5, index=prices.index)
    strat = run_backtest(prices, half, cost_multiplier=0)
    bh = buy_and_hold(prices, cost_multiplier=0)
    assert same_risk_weight(strat, bh) == pytest.approx(volatility(strat.returns) / volatility(bh.returns))
    assert same_risk_weight(bh, strat) == 1.0  # never more than 100% (no borrowing)


def test_mix_weight_uses_training_data_only(demo_prices):
    """Changing 2018+ prices must not change X: otherwise the benchmark would peek at the test period."""
    spy = demo_prices["SPY"]
    changed = spy.copy()
    changed.loc[config.TEST_START:, "Close"] *= np.linspace(1, 3, len(changed.loc[config.TEST_START:]))
    a = evaluate(MATrend(), spy, spy, "SPY", is_demo=True)
    b = evaluate(MATrend(), changed, changed, "SPY", is_demo=True)
    assert a.mix_weight == pytest.approx(b.mix_weight)
    assert 0 < a.mix_weight < 1
    assert ("test", "mix") in a.results and ("test", "mix_2x") in a.results
