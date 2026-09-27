"""
The CLAUDE.md risk rules, one test each. Tiny made-up price paths so every number can be
checked by hand.
"""

import numpy as np
import pandas as pd
import pytest

from lab import config
from lab.portfolio import portfolio_lookahead_check, simulate_portfolio
from strategies.base import Strategy
from strategies.ma_trend import MATrend


class AlwaysIn(Strategy):
    """Wants to be invested in everything, every day (after a short warm-up)."""
    name = "always_in"

    def generate_signals(self, prices):
        s = pd.Series(1.0, index=prices.index)
        s.iloc[:config.STOP_ATR_DAYS] = np.nan
        return s


def wiggle(n, daily_move, start=100.0, drift=0.0):
    """Prices that alternate up/down by `daily_move`, so the average daily move is exactly that."""
    moves = np.where(np.arange(n) % 2 == 0, 1 + daily_move, 1 / (1 + daily_move)) * (1 + drift)
    return start * np.cumprod(moves)


def book(**series):
    idx = pd.bdate_range("2020-01-01", periods=len(next(iter(series.values()))))
    return {k: pd.DataFrame({"Close": v}, index=idx) for k, v in series.items()}


def run(prices, strategy=None, **kw):
    return simulate_portfolio(strategy or AlwaysIn(), prices, assets=list(prices), **kw)


def test_one_percent_risk_rule_sizes_jumpy_assets_smaller():
    # A jumpy asset: ~2.5% average daily move -> stop 3 x 2.5% = 7.5% away, plus the one-day buffer of
    # 2 x 2.5% = 5% -> size about 1% / 12.8% = 7.9% of the account.
    prices = book(JUMPY=wiggle(60, 0.025))
    res = run(prices)
    move = prices["JUMPY"]["Close"].pct_change().abs().rolling(config.STOP_ATR_DAYS).mean()
    first_trade = res.trades.iloc[0]
    fall = (config.STOP_ATR_MULTIPLE + config.STOP_FILL_BUFFER_MOVES) * move.loc[first_trade.entry]
    assert res.risk.sized_by_risk_rule == 1 and res.risk.sized_by_cap == 0
    # The 1% includes the one-day buffer and the cost of buying and of selling at the stop.
    c = config.COST_PER_TRADE
    loss_per_dollar = fall + c + (1 - fall) * c
    assert first_trade.risk == pytest.approx(config.MAX_RISK_PER_TRADE, rel=1e-3)
    assert res.weights.loc[first_trade.entry].iloc[0] == pytest.approx(config.MAX_RISK_PER_TRADE / loss_per_dollar,
                                                                       rel=1e-3)


def test_twenty_percent_cap_limits_calm_assets():
    # A calm asset: 0.2% daily move -> 1% rule would allow 1% / 0.6% = 167%. The cap wins: 20%.
    res = run(book(CALM=wiggle(60, 0.002)))
    assert res.risk.sized_by_cap == 1
    # The buy fills at exactly 20% of the account.
    assert res.weights.loc[res.trades.entry.iloc[0]].iloc[0] == pytest.approx(0.20, abs=1e-6)
    assert_over_cap_is_trimmed_next_close(res)


def test_position_that_grows_past_twenty_percent_is_trimmed():
    rising = np.concatenate([wiggle(30, 0.002), wiggle(30, 0.002)[-1] * np.cumprod(np.full(30, 1.02))])
    res = run(book(UP=rising))
    assert res.risk.trims >= 1
    assert res.risk.days_over_cap >= 1
    # Found above 20% at a close -> trimmed at the next close. In between it can only drift by one
    # day's move (2% here), never more.
    assert_over_cap_is_trimmed_next_close(res)
    assert res.weights.max().iloc[0] <= 0.20 * 1.02 + 1e-9


def test_several_positions_trimmed_on_the_same_day_all_end_at_or_below_twenty_percent():
    # Found by the risk-manager review: trimming one position pays costs, which shrinks the account and
    # could push an already-checked position a hair over 20%. With same-close timing every close ends at or
    # below 20%; with next-close timing every over-20% position is back near 18% after the next close.
    base = wiggle(30, 0.002)
    jump = np.concatenate([base, base[-1] * np.cumprod(np.full(30, 1.03))])
    other = np.concatenate([base, base[-1] * np.cumprod(np.full(30, 1.025))])
    prices = book(A=jump, B=other, C=wiggle(60, 0.002))
    old = run(prices, cost_multiplier=5, execution="same_close")
    assert old.risk.trims >= 2
    assert old.risk.max_position_weight <= 0.20 * (1 + 1e-9)
    assert old.weights.max().max() <= 0.20 * (1 + 1e-9)
    res = run(prices, cost_multiplier=5)
    assert res.risk.trims >= 2
    assert_over_cap_is_trimmed_next_close(res)


def test_no_more_than_five_open_positions():
    prices = book(**{f"A{i}": wiggle(60, 0.002) for i in range(7)})
    res = run(prices)
    assert res.risk.max_open_positions == config.MAX_OPEN_POSITIONS
    assert (res.weights > 0).sum(axis=1).max() == 5
    assert res.risk.blocked_by_max_positions == 2  # two assets wanted in and were turned away


def test_stop_exit_limits_the_loss_to_about_one_percent():
    calm = wiggle(40, 0.03)                    # jumpy enough that the 1% rule sets the size
    drop = calm[-1] * np.cumprod(np.full(10, 0.97))  # then a steady slide
    res = run(book(A=np.concatenate([calm, drop])))
    stops = res.trades[res.trades.reason == "stop"]
    assert len(stops) >= 1
    # A slide of 3% a day overshoots the stop a little, and the sale fills one close after the stop is
    # seen, so it slides one more day: a bit more than 1%, but not much.
    assert -0.02 < stops.loss_of_account.min() < -0.005
    stop_seen = res.equity.index.get_loc(stops.exit.iloc[0]) - 1   # the close the stop was hit at
    same = run(book(A=np.concatenate([calm, drop])), execution="same_close")
    assert same.trades[same.trades.reason == "stop"].exit.iloc[0] < stops.exit.iloc[0]
    assert stop_seen >= 0


def test_after_a_stop_we_wait_for_a_fresh_signal():
    calm = wiggle(40, 0.03)
    drop = calm[-1] * np.cumprod(np.full(10, 0.97))
    res = run(book(A=np.concatenate([calm, drop, np.full(20, drop[-1])])))
    assert (res.trades.reason == "stop").sum() == 1
    assert len(res.trades) == 1  # AlwaysIn never switches off, so no re-entry


def test_circuit_breaker_stops_new_trades_after_ten_percent_fall():
    n = 120
    # Five calm assets open on day 21 at 20% each (100% invested). Then all of them gap down 12% in
    # one day (so the stops can't help): the account drops ~12%. Every position is stopped out.
    prices = {}
    for i in range(5):
        p = wiggle(n, 0.002)
        p[40:] *= 0.88
        prices[f"A{i}"] = p
    res = run(book(**prices))
    log = res.risk
    assert len(log.breaker_events) == 1
    event = log.breaker_events[0]
    assert event["drawdown"] <= -config.CIRCUIT_BREAKER_DRAWDOWN
    tripped = res.equity.index.get_loc(event["tripped"])
    resumed = res.equity.index.get_loc(event["resumed"])
    assert resumed - tripped == config.CIRCUIT_BREAKER_REVIEW_DAYS
    # Everything was stopped out in the fall (the sales fill at the close after the trip), so nothing is
    # held from then until the breaker resumes.
    assert (res.weights.iloc[tripped + 1:resumed].sum(axis=1) == 0).all()
    assert event["resumed_by"].startswith("simulated")


def test_circuit_breaker_blocks_entries_then_resumes():
    class InAfterDay45(AlwaysIn):
        """Like AlwaysIn, but the asset marked 'late' only signals from day 45, after the crash."""
        def generate_signals(self, prices):
            s = super().generate_signals(prices)
            if prices.attrs.get("late"):
                s.iloc[:45] = 0.0
            return s

    n = 120
    prices = {}
    for i in range(5):
        p = wiggle(n, 0.002)
        p[40:] *= 0.88
        prices[f"A{i}"] = p
    prices["LATE"] = wiggle(n, 0.002)
    frames = book(**prices)
    frames["LATE"].attrs["late"] = True
    res = run(frames, InAfterDay45())
    event = res.risk.breaker_events[0]
    assert res.risk.blocked_by_breaker >= 1              # LATE wanted in while the breaker was on
    late = res.trades[res.trades.asset == "LATE"]
    assert len(late) == 1 and late.entry.iloc[0] >= event["resumed"]  # and only got in after the review


def test_costs_and_cash_interest_apply_to_the_portfolio():
    prices = book(A=wiggle(42, 0.002))  # bought at day 21's close, and day 41 ends at that same price
    cash = pd.Series(0.0001, index=prices["A"].index)
    res = run(prices, cash_rate=cash)
    assert prices["A"]["Close"].iloc[21] == pytest.approx(prices["A"]["Close"].iloc[-1])
    # Buying 20% costs 0.15% of 20%; the cash part earns 0.01% a day; the asset ends flat.
    assert res.risk.entries == 1
    with_interest = res.equity.iloc[-1]
    without = run(prices).equity.iloc[-1]
    assert without == pytest.approx(1 - 0.20 * config.COST_PER_TRADE, rel=1e-4)
    assert with_interest > without


def assert_over_cap_is_trimmed_next_close(res):
    """The next-close version of the 20% rule: buys never fill above 20%, and any position that closes
    above 20% is cut back to 18% at the very next close."""
    w = res.weights
    for a in w.columns:
        over = w.index[w[a] > config.MAX_POSITION_WEIGHT * (1 + 1e-9)]
        for day in over:
            nxt = w.index.get_loc(day) + 1
            if nxt < len(w):
                assert w[a].iloc[nxt] <= config.TRIM_BACK_TO + 1e-3, (a, day)
    for t in res.trades.itertuples():
        assert w.loc[t.entry, t.asset] <= config.MAX_POSITION_WEIGHT * (1 + 1e-9)


def test_portfolio_does_not_peek_at_the_future(demo_prices):
    prices = {a: demo_prices[a].loc["2005":"2011"] for a in config.PORTFOLIO_ASSETS}
    ok, msg = portfolio_lookahead_check(MATrend(), prices, None, config.PORTFOLIO_ASSETS)
    assert ok, msg


def test_window_starts_in_cash_and_counts_entry_costs(demo_prices):
    prices = {a: demo_prices[a] for a in config.PORTFOLIO_ASSETS}
    res = simulate_portfolio(MATrend(), prices, start="2015-01-01", end="2015-12-31")
    assert res.equity.index[0] >= pd.Timestamp("2015-01-01")
    assert res.returns.iloc[0] == pytest.approx(res.equity.iloc[0] - 1)


def test_hard_floor_stops_new_trades_for_good_after_a_twenty_percent_fall():
    # Five positions at 20% each gap down 12%: the account drops ~12% and the 10% breaker trips.
    # A month later trading resumes, and a second identical gap takes the total fall past 20%.
    n = 200
    prices = {}
    for i in range(5):
        p = wiggle(n, 0.002)
        p[40:] *= 0.88
        p[100:] *= 0.88
        prices[f"A{i}"] = p
    res = run(book(**prices), InAndOut())
    log = res.risk
    assert log.hard_stop is not None
    assert log.hard_stop["drawdown"] <= -config.CIRCUIT_BREAKER_HARD_STOP
    after = res.trades[res.trades.entry > log.hard_stop["tripped"]]
    assert after.empty  # nothing opened after the hard floor, even though the signals wanted in


class InAndOut(AlwaysIn):
    """In, except for one day out every 10 days, so a fresh signal keeps coming after stop-outs."""
    def generate_signals(self, prices):
        s = super().generate_signals(prices)
        s.iloc[config.STOP_ATR_DAYS::10] = 0.0
        return s


# ---- Session 4: the one-day buffer on the 1% rule, and the 22% alert ----------------------------------

def test_buffer_is_set_in_config_and_only_shrinks_positions():
    assert config.STOP_FILL_BUFFER_MOVES == 2.0
    prices = book(JUMPY=wiggle(60, 0.025))
    with_buffer = run(prices).weights.max().iloc[0]
    import lab.config as cfg
    old = cfg.STOP_FILL_BUFFER_MOVES
    try:
        cfg.STOP_FILL_BUFFER_MOVES = 0.0
        without = run(prices).weights.max().iloc[0]
    finally:
        cfg.STOP_FILL_BUFFER_MOVES = old
    # 3 moves vs 3 + 2 moves of room: the buffered position is about 3/5 of the unbuffered one.
    assert with_buffer < without
    assert with_buffer / without == pytest.approx(0.6, abs=0.03)


def test_one_day_delay_on_a_stop_sale_stays_within_one_percent():
    # Jumpy asset (1% rule sets the size), then a slide of one average daily move a day: the stop is hit, the
    # sale fills a day later. Without the buffer that extra day pushed the loss over 1%; with it, it stays under.
    calm = wiggle(40, 0.03)
    drop = calm[-1] * np.cumprod(np.full(10, 0.97))
    res = run(book(A=np.concatenate([calm, drop])))
    stops = res.trades[res.trades.reason == "stop"]
    assert len(stops) == 1
    assert -config.MAX_RISK_PER_TRADE <= stops.loss_of_account.iloc[0] < -0.004
    assert res.risk.stops_over_budget == 0
    assert res.risk.worst_stop_loss == pytest.approx(stops.loss_of_account.iloc[0])
    # The same trade without the buffer really does go over budget (so the buffer is doing the work).
    import lab.config as cfg
    old = cfg.STOP_FILL_BUFFER_MOVES
    try:
        cfg.STOP_FILL_BUFFER_MOVES = 0.0
        unbuffered = run(book(A=np.concatenate([calm, drop])))
    finally:
        cfg.STOP_FILL_BUFFER_MOVES = old
    assert unbuffered.risk.stops_over_budget == 1
    assert unbuffered.risk.worst_stop_loss < -config.MAX_RISK_PER_TRADE


def test_alert_when_a_position_ends_a_day_above_22_percent():
    # A calm asset bought at 20%, then it jumps 30% in one day: it ends that day well above 22% (alert),
    # and is trimmed to 18% at the next close.
    p = wiggle(60, 0.002)
    p[40:] *= 1.30
    res = run(book(A=p))
    alerts = res.risk.alerts
    assert len(alerts) == 1
    day = res.equity.index[40]
    assert alerts[0]["date"] == day and alerts[0]["asset"] == "A" and alerts[0]["weight"] > 0.22
    assert res.weights["A"].iloc[41] == pytest.approx(config.TRIM_BACK_TO, abs=1e-3)
    assert_over_cap_is_trimmed_next_close(res)


def test_no_alert_for_the_normal_one_day_drift_above_20_percent():
    rising = np.concatenate([wiggle(30, 0.002), wiggle(30, 0.002)[-1] * np.cumprod(np.full(30, 1.02))])
    res = run(book(UP=rising))
    assert res.risk.days_over_cap >= 1 and res.risk.alerts == []


def test_never_six_positions_when_a_market_is_shut_for_a_day():
    # Found by the session-4 risk review. Five positions are open. One (A0) is told to sell, but its market is
    # shut the next day, so the sale can't fill. A sixth asset wants in at the same time. It must wait until
    # the sale has actually filled, so there are never 6 positions at a close.
    class OutOnDay40(AlwaysIn):
        def generate_signals(self, prices):
            s = super().generate_signals(prices)
            if prices.attrs.get("seller"):
                s.iloc[40:] = 0.0
            if prices.attrs.get("late"):
                s.iloc[:40] = 0.0
            return s

    n = 70
    frames = book(**{f"A{i}": wiggle(n, 0.002) for i in range(6)})
    frames["A0"].attrs["seller"] = True
    frames["A5"].attrs["late"] = True
    shut = frames["A0"].index[41]                 # A0's market is shut the day its sale would fill
    frames["A0"] = frames["A0"].drop(shut)
    res = run(frames, OutOnDay40())
    held = (res.weights > 0).sum(axis=1)
    assert held.max() <= config.MAX_OPEN_POSITIONS
    assert res.risk.max_open_positions <= config.MAX_OPEN_POSITIONS
    late = res.trades[res.trades.asset == "A5"]
    a0_exit = res.trades[res.trades.asset == "A0"].exit.iloc[0]
    assert len(late) == 1 and late.entry.iloc[0] > a0_exit   # A5 got in, but only after A0 was sold


def test_alert_fires_even_on_a_day_the_asset_market_is_shut():
    # A (20%) sits on a holiday while the other positions crash: A's share of the account jumps above 22% that day.
    n = 60
    frames = book(A=wiggle(n, 0.002), B=wiggle(n, 0.002), C=wiggle(n, 0.002), D=wiggle(n, 0.002))
    for x in "BCD":
        frames[x].iloc[40:, 0] *= 0.6
    holiday = frames["A"].index[40]
    frames["A"] = frames["A"].drop(holiday)
    res = run(frames)
    assert any(al["date"] == holiday and al["asset"] == "A" for al in res.risk.alerts)
