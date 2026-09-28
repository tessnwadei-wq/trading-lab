"""
The equal-risk mix (session 5): the same-risk mix rescaled so that its TEST-period volatility equals the
strategy's test-period volatility. It closes the "bumpier wins" loophole in check 3: a strategy that beats the
same-risk mix only because it ended up taking more risk than the mix must FAIL.
"""

import numpy as np
import pandas as pd
import pytest

from lab import config
from lab.backtest import buy_and_hold, run_backtest
from lab.metrics import volatility
from lab.skeptic import FAIL, alternatives_comparisons, equal_risk_weight, evaluate
from strategies.ma_trend import MATrend
from tests.conftest import make_prices


def random_prices(seed=0, n=400):
    rng = np.random.default_rng(seed)
    return make_prices(100 * np.cumprod(1 + 0.01 * rng.standard_normal(n)))


def test_equal_risk_weight_scales_the_mix_to_the_strategys_volatility():
    prices = random_prices()
    bh = buy_and_hold(prices, cost_multiplier=0)
    half = run_backtest(prices, pd.Series(0.5, index=prices.index), cost_multiplier=0)
    # A 30% mix vs a strategy that is (about) as bumpy as a 50% mix -> the equal-risk mix holds about 50%.
    mix30 = run_backtest(prices, pd.Series(0.3, index=prices.index), cost_multiplier=0)
    w = equal_risk_weight(0.3, half, mix30)
    assert w == pytest.approx(0.3 * volatility(half.returns) / volatility(mix30.returns))
    assert w == pytest.approx(0.5, abs=0.02)
    # Never above 100%: the lab doesn't borrow.
    assert equal_risk_weight(0.8, bh, mix30) == 1.0


def test_equal_risk_mix_matches_the_strategys_test_volatility(demo_prices):
    ev = evaluate(MATrend(), demo_prices["SPY"], demo_prices["SPY"], "SPY", is_demo=True)
    assert ("test", "eqmix") in ev.metrics.index and ("test", "eqmix_2x") in ev.metrics.index
    assert ("train", "eqmix") not in ev.metrics.index   # a test-period yardstick only
    strat_vol = ev.metrics.loc[("test", "strategy"), "volatility"]
    eq_vol = ev.metrics.loc[("test", "eqmix"), "volatility"]
    if ev.eq_mix_weight < 1.0:
        assert eq_vol == pytest.approx(strat_vol, rel=0.05)
    assert [c.number for c in ev.checks] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert "Equal-risk mix =" in ev.checks[2].finding


def test_equal_risk_mix_does_not_change_the_same_risk_mix(demo_prices):
    """The same-risk mix is still sized on training data only; the new benchmark sits alongside it."""
    spy = demo_prices["SPY"]
    changed = spy.copy()
    changed.loc[config.TEST_START:, "Close"] *= np.linspace(1, 3, len(changed.loc[config.TEST_START:]))
    a = evaluate(MATrend(), spy, spy, "SPY", is_demo=True)
    b = evaluate(MATrend(), changed, changed, "SPY", is_demo=True)
    assert a.mix_weight == pytest.approx(b.mix_weight)


def metrics(strat_cagr, mix_cagr, eqmix_cagr):
    """Test-period numbers where the strategy beats buy-and-hold, SPY and the same-risk mix."""
    rows = {"strategy": (0.90, strat_cagr), "strategy_2x": (0.88, strat_cagr - 0.002),
            "buy_hold": (0.70, 0.14), "buy_hold_2x": (0.70, 0.14), "index": (0.70, 0.14), "index_2x": (0.70, 0.14),
            "mix": (0.70, mix_cagr), "mix_2x": (0.70, mix_cagr), "eqmix": (0.70, eqmix_cagr),
            "eqmix_2x": (0.70, eqmix_cagr)}
    return pd.DataFrame([{"period": "test", "who": w, "sharpe": s, "cagr": c} for w, (s, c) in rows.items()]
                        ).set_index(["period", "who"])


def test_bumpier_win_over_the_same_risk_mix_now_fails():
    # vol_target's pattern: ahead of the (training-sized) same-risk mix, but only because it was bumpier;
    # at the same risk, the mix earned more.
    comps = alternatives_comparisons(metrics(0.109, 0.103, 0.112), "buy-and-hold")
    lost = [c for c in comps if not c["won"]]
    assert {c["name"] for c in lost} == {"the equal-risk mix"}
    assert {c["costs"] for c in lost} == {"normal costs", "double costs"}
    assert len(comps) == 8   # 4 yardsticks x 2 cost levels


def test_beating_the_equal_risk_mix_too_is_a_win():
    comps = alternatives_comparisons(metrics(0.109, 0.103, 0.105), "buy-and-hold")
    assert all(c["won"] for c in comps)


def test_check_3_fails_end_to_end_when_the_equal_risk_mix_earns_more(demo_prices, monkeypatch):
    """Through the whole Skeptic: rig the equal-risk mix to 100% of the asset, which out-earns ma_trend here."""
    import lab.skeptic as sk
    monkeypatch.setattr(sk, "equal_risk_weight", lambda *a: 1.0)
    ev = evaluate(MATrend(), demo_prices["SPY"], demo_prices["SPY"], "SPY", is_demo=True)
    m = ev.metrics
    assert m.loc[("test", "strategy"), "cagr"] < m.loc[("test", "eqmix"), "cagr"]
    assert ev.checks[2].status == FAIL
    assert "the equal-risk mix at normal costs (yearly return" in ev.checks[2].finding
    assert "capped at 100%" in ev.checks[2].finding
