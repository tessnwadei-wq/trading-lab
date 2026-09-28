"""ts_momentum (idea #5): the pre-registered signal, the monthly resize / re-arm engine features, and check 5."""

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lab import config
from lab.portfolio import evaluate_portfolio, simulate_portfolio
from lab.skeptic import lookahead_check
from strategies.ts_momentum import SPEC_COMMIT, SPEC_PATH, TSMomentum
from strategies.vol_target import month_end_decision_days

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ["SPY", "XIU.TO", "GLD", "IEF"]


def steady(yearly_growth, years=2.5, start="2020-01-01", wiggle=0.0):
    """A price that grows smoothly at `yearly_growth` a year, with an optional up/down wiggle every day."""
    idx = pd.bdate_range(start, periods=int(252 * years))
    daily = (1 + yearly_growth) ** (1 / 252)
    w = np.where(np.arange(len(idx)) % 2 == 0, 1 + wiggle, 1 / (1 + wiggle))
    return pd.DataFrame({"Close": 100 * np.cumprod(np.full(len(idx), daily) * w)}, index=idx)


def flat_cash(yearly, index):
    return pd.Series(yearly / 252, index=index)


def test_parameters_are_the_pre_registered_ones():
    s = TSMomentum()
    assert s.params == {"lookback_months": 12, "skip_months": 0}
    assert s.sensitivity_grid() == {"lookback_months": [6, 9, 12, 15, 18], "skip_months": [0, 1]}
    assert s.sample_size_rule == "signal_changes" and s.control_weight == 0.20 and "no search" in s.how_chosen
    assert config.PORTFOLIO_STRATEGIES["ts_momentum"] == ASSETS


def test_hold_only_when_the_past_year_beat_cash():
    p = steady(0.03)                                         # +3% a year
    beats_zero = TSMomentum(cash_rate=None).generate_signals(p)
    loses_to_cash = TSMomentum(cash_rate=flat_cash(0.05, p.index)).generate_signals(p)   # T-bills paid 5%
    assert beats_zero.dropna().eq(1).all()
    assert loses_to_cash.dropna().eq(0).all()                # beating 0% isn't enough: it must beat cash
    assert TSMomentum().generate_signals(steady(-0.10)).dropna().eq(0).all()


def test_signal_uses_the_month_end_twelve_months_back():
    p = steady(0.10)
    sig = TSMomentum().generate_signals(p)
    days = p.index[month_end_decision_days(p.index)]
    assert sig.first_valid_index() == days[12]               # the 13th month-end is the first with a 12-month past
    assert sig.loc[:days[12]].iloc[:-1].isna().all()          # warm-up: no signal yet


def test_decisions_only_change_at_month_ends():
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2019-01-01", periods=900)
    p = pd.DataFrame({"Close": 100 * np.cumprod(1 + 0.015 * rng.standard_normal(900))}, index=idx)
    sig = TSMomentum().generate_signals(p)
    changed = sig.ne(sig.shift()) & sig.notna() & sig.shift().notna()
    decide = pd.Series(month_end_decision_days(idx), index=idx)
    assert changed.any() and decide[changed].all()


def test_no_look_ahead(demo_prices):
    cash = demo_prices["^IRX"]["Close"] / 100 / 252
    for a in ASSETS:
        ok, msg = lookahead_check(TSMomentum(cash_rate=cash.shift(1).dropna()), demo_prices[a])
        assert ok, msg


def test_monthly_resize_brings_a_drifted_position_back_and_resets_the_stop():
    # Two calm assets, always "hold": each is bought at 20%. A rises fast and B slowly, so they drift apart;
    # at each month-end both are resized back to 20% (paying costs only on the difference).
    idx = pd.bdate_range("2020-01-01", periods=int(252 * 1.6))
    a = steady(0.30, years=1.6, wiggle=0.002)
    b = steady(0.02, years=1.6, wiggle=0.002)
    strat = TSMomentum()
    res = simulate_portfolio(strat, {"A": a, "B": b}, assets=["A", "B"])
    log = res.risk
    assert log.resizes > 0 and log.stop_exits == 0
    sig_on = strat.generate_signals(a).reindex(idx).notna()
    decide = pd.Series(month_end_decision_days(idx), index=idx)
    # The day after each month-end decision (the fill), both positions are back at 20% (costs aside).
    fills = [idx[i + 1] for i in range(len(idx) - 1) if decide.iloc[i] and sig_on.iloc[i] and
             res.weights.loc[idx[i]].gt(0).all()]
    assert fills
    for day in fills:
        assert res.weights.loc[day].to_numpy() == pytest.approx([0.20, 0.20], abs=0.002)
    assert (res.trades["reason"] == "resize").sum() == log.resizes


def test_after_a_stop_out_the_asset_comes_back_at_the_next_month_end():
    # A calm uptrend (signal "hold") with one sharp fall mid-month that hits the stop.
    p = steady(0.20, years=1.5, wiggle=0.002)
    crash_day = p.index.get_loc(p.index[month_end_decision_days(p.index)][13]) + 8   # a week into a month
    p.iloc[crash_day:, 0] *= 0.95
    res = simulate_portfolio(TSMomentum(), {"A": p}, assets=["A"])
    stops = res.trades[res.trades["reason"] == "stop"]
    assert len(stops) >= 1
    stop_exit = stops.iloc[0]["exit"]
    next_month_end = p.index[month_end_decision_days(p.index) & (p.index > stop_exit)][0]
    back_in = res.weights["A"].loc[stop_exit:].gt(0)
    first_back = back_in[back_in].index[0]
    # Bought back at the close after the next month-end decision, even though the signal never switched off.
    assert first_back == p.index[p.index.get_loc(next_month_end) + 1]
    assert TSMomentum().generate_signals(p).loc[stop_exit:next_month_end].eq(1).all()


def test_no_top_ups_while_the_circuit_breaker_is_on(monkeypatch):
    """With the breaker on, a month-end resize may sell (A grew above 20%) but must not buy (B shrank below 20%)."""
    import lab.portfolio as pf

    class TrippedLater(pf.CircuitBreaker):
        # Behaves normally, but counts as tripped from 2021-03-01 on (a stand-in for a real 10% fall).
        def update(self, i, day, value):
            super().update(i, day, value)
            self.day = day

        @property
        def allows_new_trades(self):
            return getattr(self, "day", pd.Timestamp(0)) < pd.Timestamp("2021-03-01")

    monkeypatch.setattr(pf, "CircuitBreaker", TrippedLater)
    a = steady(0.40, years=1.6, wiggle=0.002)      # grows: above 20% by each month-end
    b = steady(0.01, years=1.6, wiggle=0.002)      # barely grows: below 20% by each month-end
    res = simulate_portfolio(TSMomentum(), {"A": a, "B": b}, assets=["A", "B"])
    after = res.weights.loc["2021-03-03":]
    assert res.risk.resizes_blocked_by_breaker > 0            # B's top-ups were skipped...
    assert after["B"].max() < 0.19 and after["B"].iloc[-1] < after["B"].iloc[0]   # ...so B was never topped up
    assert after["A"].max() <= config.MAX_POSITION_WEIGHT + 0.01   # A was still cut back


def test_ma_trend_portfolio_is_unchanged_by_the_monthly_features(demo_prices):
    """Strategies without rebalance_days keep the old engine behaviour exactly (no resizes, fresh-signal re-entry)."""
    from strategies.ma_trend import MATrend
    prices = {a: demo_prices[a].loc["2005":"2012"] for a in ["SPY", "XIU.TO", "GLD"]}
    res = simulate_portfolio(MATrend(), prices, assets=list(prices))
    assert res.risk.resizes == 0 and "resize" not in set(res.trades["reason"])


def test_evaluation_uses_the_control_and_signal_changes(demo_prices):
    cash = (demo_prices["^IRX"]["Close"] / 100 / 252).shift(1).dropna()
    prices = {a: demo_prices[a] for a in ASSETS}
    ev = evaluate_portfolio(TSMomentum(cash_rate=cash), prices, cash, is_demo=True, assets=ASSETS)
    assert ("test", "control") in ev.metrics.index and ("test", "control_2x") in ev.metrics.index
    assert "20% in each asset, always held, 20% cash" in ev.control_name
    check3 = ev.checks[2]
    assert "the fair control" in check3.finding and "Equal-risk mix" in check3.finding
    check5 = ev.checks[4]
    assert "signal changes" in check5.finding and ev.signal_changes["full"] >= ev.signal_changes["test"] > 0
    # The control really is 80% invested.
    assert ev.results[("full", "control")].position.iloc[0] == pytest.approx(0.80)


def test_spec_file_exists_and_is_the_committed_one():
    spec = ROOT / SPEC_PATH
    assert spec.exists() and "FROZEN" in spec.read_text(encoding="utf-8")
    try:
        files = subprocess.run(["git", "show", "--name-only", "--format=", SPEC_COMMIT], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.split()
        committed = subprocess.run(["git", "show", f"{SPEC_COMMIT}:{SPEC_PATH}"], cwd=ROOT, capture_output=True,
                                   text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git history not available here (e.g. a shallow checkout)")
    assert files == [SPEC_PATH]                       # the spec was committed on its own
    assert committed == spec.read_text(encoding="utf-8")   # and hasn't been edited since
