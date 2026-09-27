"""
Fractional positions (session 4): any weight from 0% to 100%, weights drift between trades, and costs are
charged on how much the weight changes. And the proof that all-in/all-out strategies are unaffected.
"""

import numpy as np
import pandas as pd
import pytest

from lab import config
from lab.backtest import _drifting_weights, execution_lag, run_backtest
from lab.cash import align_cash
from run_lab import STRATEGIES
from strategies.ma_trend import MATrend
from tests.conftest import make_prices

C = config.COST_PER_TRADE


def old_engine(prices, signal, cost_multiplier=1.0, start=None, end=None, cash_rate=None, execution=None):
    """A frozen copy of the session-3 engine's maths (0/1 positions, no drift), to compare against."""
    close = prices["Close"].astype(float)
    signal = signal.reindex(close.index).fillna(0.0).clip(0, 1)
    position = signal.shift(execution_lag(execution)).fillna(0.0)
    asset_ret = close.pct_change().fillna(0.0)
    cash_ret = align_cash(cash_rate, close.index)
    if start is not None or end is not None:
        position, asset_ret, cash_ret = (x.loc[start:end] for x in (position, asset_ret, cash_ret))
    turnover = (position - position.shift(1).fillna(0.0)).abs()
    strat_ret = position * asset_ret + (1 - position) * cash_ret - turnover * C * cost_multiplier
    return (1 + strat_ret).cumprod(), strat_ret, position


# ---- Existing (all-in / all-out) strategies: results identical -----------------------------------------------

@pytest.mark.parametrize("name", list(STRATEGIES))
@pytest.mark.parametrize("execution", ["next_close", "same_close"])
def test_all_in_all_out_strategies_give_identical_results(name, execution, demo_prices):
    strategy = STRATEGIES[name]()
    if not getattr(strategy, "fractional", False):
        prices = demo_prices["SPY"]
        cash = (demo_prices["^IRX"]["Close"] / 100 / 252).shift(1).dropna()
        signal = strategy.generate_signals(prices)
        for m, (s, e) in [(1.0, (None, None)), (2.0, ("2008-01-01", "2012-12-31")), (1.0, ("2018-01-01", None))]:
            new = run_backtest(prices, signal, m, s, e, cash, execution)
            eq, rets, pos = old_engine(prices, signal, m, s, e, cash, execution)
            assert new.equity.equals(eq) and new.returns.equals(rets) and new.position.equals(pos)


def test_drift_calculation_matches_the_simple_formula_for_0_1_positions(demo_prices):
    """The new day-by-day calculation, forced onto a 0/1 strategy, gives the same numbers as the old formula.
    So the fast path used for 0/1 strategies is only a shortcut, not a different model."""
    prices = demo_prices["XIU.TO"]
    cash = (demo_prices["^IRX"]["Close"] / 100 / 252).shift(1).dropna()
    signal = MATrend().generate_signals(prices)
    fast = run_backtest(prices, signal, cash_rate=cash)
    target = signal.reindex(prices.index).fillna(0.0).shift(2).fillna(0.0)
    held, traded, rets = _drifting_weights(target, prices["Close"].pct_change().fillna(0.0),
                                           align_cash(cash, prices.index), C)
    assert np.array_equal(rets.to_numpy(), fast.returns.to_numpy())
    assert np.array_equal(held.to_numpy(), fast.position.to_numpy())
    assert np.allclose(traded, fast.turnover)


# ---- Fractional positions ------------------------------------------------------------------------------------

def test_half_invested_earns_half_the_move_plus_half_the_cash():
    prices = make_prices([100, 100, 100, 110])
    signal = pd.Series(0.5, index=prices.index)
    cash = pd.Series(0.001, index=prices.index)
    res = run_backtest(prices, signal, cost_multiplier=0, cash_rate=cash)   # held from day 2 (next close)
    # Days 0-1: all cash, earning 0.1% a day. Day 2: flat asset, the cash half earns 0.1%.
    # Day 3: asset +10% on the (drifted) invested part.
    w2 = 0.5
    day2 = w2 * 0 + (1 - w2) * 0.001
    w3 = w2 / (1 + day2)                 # the asset part didn't grow, the cash part did: weight drifts down a hair
    day3 = w3 * 0.10 + (1 - w3) * 0.001
    assert res.equity.iloc[-1] == pytest.approx(1.001 ** 2 * (1 + day2) * (1 + day3))
    assert res.position.iloc[3] == pytest.approx(w3)


def test_weights_drift_between_trades_and_only_the_change_pays_costs():
    # Target 50% for days 0-4, then 30%. The asset doubles on day 3, so the 50% drifts to 2/3 before the change.
    prices = make_prices([100, 100, 100, 200, 200, 200, 200])
    signal = pd.Series([0.5, 0.5, 0.5, 0.5, 0.3, 0.3, 0.3], index=prices.index)
    res = run_backtest(prices, signal, cash_rate=None)
    # Bought 50% at close 1 (next-close timing), paying 0.5 x 0.15%. No trade on the drift.
    assert res.turnover.iloc[2] == pytest.approx(0.5)
    assert res.turnover.iloc[3] == 0 and res.turnover.iloc[4] == 0 and res.turnover.iloc[5] == 0
    drifted = res.position.iloc[4]
    assert drifted > 0.66                                  # 0.5 of the account doubled: ~2/3 invested
    # The 30% target (decided at close 4) is traded at close 5: sell from ~2/3 down to 30%.
    assert res.position.iloc[6] == pytest.approx(0.3)
    w_before = res.position.iloc[5]                        # flat day 5: still the weight at the close before day 6
    assert res.turnover.iloc[6] == pytest.approx(w_before - 0.3)
    assert res.returns.iloc[6] == pytest.approx(-(w_before - 0.3) * C)
    assert res.rebalances() == 2 and res.rebalances(0.05) == 2


def test_a_constant_fractional_target_trades_only_once():
    rng = np.random.default_rng(1)
    prices = make_prices(100 * np.cumprod(1 + 0.01 * rng.standard_normal(250)))
    res = run_backtest(prices, pd.Series(0.6, index=prices.index))
    assert res.rebalances() == 1
    assert res.position.min() != res.position.max()        # ...and the weight really does drift


def test_weights_are_kept_between_0_and_100_percent():
    prices = make_prices([100, 101, 102, 103, 104])
    res = run_backtest(prices, pd.Series([1.7, 1.7, -0.5, -0.5, -0.5], index=prices.index), cost_multiplier=0)
    assert res.position.max() <= 1 and res.position.min() >= 0


def test_fractional_costs_double_with_the_cost_multiplier():
    prices = make_prices([100] * 8)
    signal = pd.Series([0.4, 0.4, 0.4, 0.7, 0.7, 0.2, 0.2, 0.2], index=prices.index)
    one, two = run_backtest(prices, signal), run_backtest(prices, signal, cost_multiplier=2)
    # Three trades: buy 40%, add 30%, sell 50%. Each cost is a share of the account at that moment.
    for res, m in ((one, 1), (two, 2)):
        assert res.equity.iloc[-1] == pytest.approx((1 - 0.4 * m * C) * (1 - 0.3 * m * C) * (1 - 0.5 * m * C))


def test_fractional_trades_also_wait_for_the_next_close():
    prices = make_prices([100, 100, 100, 50, 50])
    signal = pd.Series([0.8, 0.8, 0.2, 0.2, 0.2], index=prices.index)   # cut to 20% decided at close 2
    res = run_backtest(prices, signal, cost_multiplier=0)
    # ...but traded at close 3, AFTER the -50% day: it still held 80% through the crash.
    assert res.position.iloc[3] == pytest.approx(0.8)
    assert res.equity.iloc[3] == pytest.approx(1 - 0.8 * 0.5)
