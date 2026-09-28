"""vol_target (idea #4): the pre-registered rule, its month-end timing, and its sample-size rule."""

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lab import config
from lab.backtest import run_backtest
from lab.skeptic import NMD, PASS, evaluate, lookahead_check
from strategies.vol_target import SPEC_COMMIT, SPEC_PATH, VolTarget, month_end_decision_days

ROOT = Path(__file__).resolve().parent.parent


def prices_from_returns(rets, start="2021-01-01"):
    idx = pd.bdate_range(start, periods=len(rets) + 1)
    return pd.DataFrame({"Close": 100 * np.cumprod(np.r_[1.0, 1 + np.asarray(rets)])}, index=idx)


def test_parameters_are_the_pre_registered_ones():
    assert VolTarget().params == {"target_vol": 0.12, "vol_days": 21}
    assert VolTarget().sensitivity_grid() == {"target_vol": [0.08, 0.10, 0.12, 0.14, 0.16], "vol_days": [10, 21, 42, 63]}
    assert VolTarget.sample_size_rule == "rebalances" and "no search" in VolTarget.how_chosen


def test_weight_is_target_over_volatility_capped_at_100_percent():
    rng = np.random.default_rng(7)
    calm = 0.004 * rng.standard_normal(60)          # ~6% a year: fully invested
    stormy = 0.025 * rng.standard_normal(60)        # ~40% a year: about 30% invested
    p = prices_from_returns(np.r_[calm, stormy])
    sig = VolTarget().generate_signals(p)
    rets = p["Close"].pct_change()
    for day in p.index[month_end_decision_days(p.index)]:
        known = rets.loc[:day].dropna()
        if len(known) < 21:
            assert np.isnan(sig.loc[day])               # warm-up: not enough history yet
            continue
        vol = known.iloc[-21:].std() * np.sqrt(252)
        assert sig.loc[day] == pytest.approx(min(1.0, 0.12 / vol))
    decided = sig.dropna()
    assert decided.max() == 1.0 and 0.2 < decided.min() < 0.45


def test_decisions_are_made_only_at_month_end_and_held_in_between():
    rng = np.random.default_rng(3)
    p = prices_from_returns(0.02 * rng.standard_normal(150))
    sig = VolTarget().generate_signals(p).dropna()
    changes = sig.index[sig.diff().fillna(1) != 0]
    for day in changes:
        nxt = day + pd.offsets.BDay(1)
        assert nxt.month != day.month       # every change happens on the month's last weekday


def test_holiday_on_the_last_weekday_moves_the_decision_to_the_next_trading_day():
    idx = pd.bdate_range("2024-03-01", "2024-04-30")
    idx = idx.drop(pd.Timestamp("2024-03-29"))      # Good Friday: markets shut on the last weekday of March
    d = pd.Series(month_end_decision_days(idx), index=idx)
    assert not d.loc["2024-03-28"]                  # Thursday: the next weekday (Friday) is still March
    assert d.loc["2024-04-01"]                      # so March's decision is made on April 1st, a day late
    assert d.loc["2024-04-30"] and d.sum() == 2


def test_no_look_ahead_including_around_month_ends(demo_prices):
    ok, msg = lookahead_check(VolTarget(), demo_prices["SPY"].loc["2005":"2012"], n_cuts=25)
    assert ok, msg


def test_monthly_trades_pay_costs_on_the_weight_change_only(demo_prices):
    p = demo_prices["SPY"].loc["2006":"2009"]
    sig = VolTarget().generate_signals(p)
    res = run_backtest(p, sig)
    traded_days = res.turnover[res.turnover > 0].index
    # At most one trade a month. The engine books a trade on the first day the new weight earns: decided at the
    # month's last close (t), filled at the next close (t+1, the new month's first trading day), earning from t+2.
    assert traded_days.to_period("M").is_unique
    for d in traded_days[1:]:
        fill, decision = d - pd.offsets.BDay(1), d - pd.offsets.BDay(2)
        assert decision.month != fill.month
    cost = res.turnover * config.COST_PER_TRADE
    gross = res.position * p["Close"].pct_change().fillna(0).loc[res.position.index]
    assert np.allclose(res.returns, gross - cost)   # cash earns 0 here: return = invested share x move - costs


def test_sample_size_rule_counts_active_rebalances(demo_prices):
    ev = evaluate(VolTarget(), demo_prices["SPY"], demo_prices["SPY"], "SPY", is_demo=True)
    check = ev.checks[4]
    assert check.name == "Sample size" and check.status == PASS
    assert "active rebalances" in check.finding
    n = ev.results[("full", "strategy")].rebalances(config.ACTIVE_REBALANCE_MIN_CHANGE)
    assert n >= config.MIN_ACTIVE_REBALANCES and f"{n} active rebalances" in check.finding


def test_sample_size_rule_says_needs_more_data_when_too_short(demo_prices):
    short = demo_prices["SPY"].loc[:"2021-06-30"]   # only 3.5 years of test period
    ev = evaluate(VolTarget(), short, short, "SPY", is_demo=True)
    assert ev.checks[4].status == NMD and "years" in ev.checks[4].headline


def test_round_trip_strategies_keep_the_30_trade_rule(demo_prices):
    from strategies.ma_trend import MATrend
    ev = evaluate(MATrend(), demo_prices["SPY"], demo_prices["SPY"], "SPY", is_demo=True)
    assert "trades in total" in ev.checks[4].finding


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
    # The rules haven't been edited since they were frozen.
    assert committed == spec.read_text(encoding="utf-8")
