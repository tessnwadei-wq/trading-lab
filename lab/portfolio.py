"""
Portfolio backtest (phase 2): one strategy run across several assets at once, with the
CLAUDE.md risk rules enforced in code.

TRADE TIMING: every decision is made at a day's close using only prices known then, and is
FILLED AT THE NEXT CLOSE of that asset's market (config.EXECUTION = "next_close"). So a decision
is an ORDER that waits one day. (The old "same_close" timing, filling at the very close you
decided on, is kept only for the report's "Timing cost" comparison.)

How a day works, in plain English:
  1. Update each position's value with the day's price move; cash earns the T-bill rate.
  2. FILL YESTERDAY'S ORDERS at today's close: sells first, then buys, then trims.
  3. EXITS (decided now, filled tomorrow). Sell a position if its price has fallen to its
     protective stop (see "risk" below), or if the strategy's signal says "out".
  4. CIRCUIT BREAKER (lab/breaker.py). If the account is 10% or more below its peak, stop opening
     new trades and log it. In real (paper) trading only a manual reset by Tessy restarts it. A
     backtest can't wait for a person, so it ASSUMES a review of config.CIRCUIT_BREAKER_REVIEW_DAYS
     (21) trading days, after which trading resumes and the current value becomes the new peak.
     Existing positions keep their normal exits while the breaker is on.
     HARD FLOOR: if the account is ever 20% below its all-time high, new trades stop for good
     in a backtest, so repeated 10% falls can't quietly add up.
  5. ENTRIES (decided now, filled tomorrow). For each asset whose signal says "in" and that we
     don't hold, place a buy order, unless 5 positions would then be open or the breaker is on.
     Its size, as a share of the account, is the SMALLER of:
       * the 1% risk rule: size = 1% / (exit distance + one-day buffer + buying and selling costs)
         (so if the stop is hit, and the sale fills a day later, a normal stop-out still loses no more
         than about 1% of the account, costs included; see config.STOP_FILL_BUFFER_MOVES), and
       * the 20% cap: 20% of the account.
     The order is "buy <size> of my account at the close", so it is worked out with the account
     value at the close it fills at, and it never fills above 20%.
  6. TRIMS (decided now, filled tomorrow). The 20% rule as enforced: "No buy that would take a position
     above 20%. Anything above 20% at a close is trimmed to 18% at the next close." (Cutting back to
     exactly 20% would mean selling a sliver, and paying costs, almost every day.) Because the trim fills
     a day later, a position can sit a little above 20% for one close; the report counts how often
     (days_over_cap). ALERT: any position that ENDS a day above 22% (config.POSITION_ALERT_WEIGHT) is
     logged in RiskLog.alerts and listed in the report, because that should only happen after an unusual
     one-day jump.

What "risk" means here (the 1% rule): risk is what we lose if the trade goes wrong and we
exit. So every trade needs an exit point decided in advance: a protective stop. We place it
STOP_ATR_MULTIPLE (3) x the asset's "average daily move" below the price we paid. The average
daily move is the average size of the last 20 daily % changes, a close-price version of the
"Average True Range" (ATR) that traders use.
Why volatility-based: a fixed distance (say 5%) would be far too tight for a jumpy asset and
far too loose for a calm one. Tying the distance to how much the asset normally moves means
calm assets get bigger positions and jumpy assets smaller ones, so each trade risks about
the same 1%. The stop is fixed at entry (it does not trail the price up).
After a stop-out we wait for a FRESH signal (the signal must switch off and on again) before
buying that asset again, otherwise we'd just buy back the next day.

Simplifications (written down so nobody forgets them):
  * A stop is checked at the close, not during the day, and the sale fills at the NEXT close.
    If the price gaps through the stop, or keeps falling for that extra day, the loss can be
    bigger than 1%. The report shows the worst real loss per trade.
  * XIU.TO is priced in Canadian dollars. We add up returns as if every asset were in the
    same currency (like a currency-hedged investor). Currency moves are ignored.
  * Every asset uses the US T-bill rate for cash (see lab/cash.py).
  * An asset can only be traded on days its own market was open; an order waits for that day.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from lab import config
from lab.backtest import BacktestResult, buy_and_hold, execution_lag, fixed_mix
from lab.breaker import CircuitBreaker
from lab.cash import align_cash
from lab.skeptic import (PriceRoseProbe, Subject, _probe_days, _shocked, evaluate_subject, lookahead_check,
                         sensitivity_grid)

BENCHMARK_NAME = "equal-weight buy-and-hold"


@dataclass
class RiskLog:
    """How often each risk rule changed what the strategy wanted to do."""
    entries: int = 0                  # positions opened
    sized_by_risk_rule: int = 0       # 1% risk rule gave a size below the 20% cap, so it set the size
    sized_by_cap: int = 0             # 1% rule would have allowed more than 20%: the cap set the size
    limited_by_cash: int = 0          # not enough cash left for the full size
    blocked_by_max_positions: int = 0  # wanted to enter, but 5 positions were already open
    blocked_by_breaker: int = 0       # wanted to enter, but the circuit breaker was on
    trims: int = 0                    # a position grew past 20% and was cut back
    stop_exits: int = 0
    signal_exits: int = 0
    max_open_positions: int = 0
    max_position_weight: float = 0.0  # largest share of the account in one position at a close (market open)
    days_over_cap: int = 0            # position-days a position closed above 20% (next_close: its trim fills
                                      # at the NEXT close, so a position can sit above 20% for one close)
    worst_trade_loss: float = 0.0     # worst closed-trade loss, as a share of the account at entry
    worst_stop_loss: float = 0.0      # worst loss of a trade closed by its stop, as a share of the account
    stops_over_budget: int = 0        # stop-outs that lost more than the 1% budget
    alerts: list = field(default_factory=list)  # {"date", "asset", "weight"}: a position ENDED a day above 22%
    breaker_events: list = field(default_factory=list)  # {"tripped", "drawdown", "resumed"}
    hard_stop: dict = None            # {"tripped", "drawdown"} if the 20% hard floor was ever hit


@dataclass
class PortfolioResult(BacktestResult):
    risk: RiskLog = None
    weights: pd.DataFrame = None      # share of the account in each asset, each day


def _prepare(strategy, prices: dict, assets: list, cash_rate):
    """Line every asset up on one calendar. Signals and stop distances use each asset's own history."""
    raw = pd.DataFrame({a: prices[a]["Close"] for a in assets})
    traded = raw.notna()
    closes = raw.ffill()
    signals = pd.DataFrame({a: strategy.generate_signals(prices[a]) for a in assets})
    signals = signals.reindex(closes.index).ffill().fillna(0.0)
    avg_move = pd.DataFrame({a: prices[a]["Close"].pct_change().abs().rolling(config.STOP_ATR_DAYS).mean()
                             for a in assets}).reindex(closes.index).ffill()
    return closes, traded, signals, avg_move, align_cash(cash_rate, closes.index)


def simulate_portfolio(strategy, prices: dict, cash_rate: pd.Series | None = None, start=None, end=None,
                       cost_multiplier: float = 1.0, assets: list | None = None,
                       execution: str | None = None) -> PortfolioResult:
    """
    Run `strategy` on every asset in `assets` as one account that starts with 1.0 in cash.

    Trade timing (execution, default config.EXECUTION = "next_close"): every decision made at a
    close (exit, stop, entry, trim) becomes an ORDER that is filled at the NEXT close of that
    asset's market. "same_close" (the old, optimistic timing: fill at the close you decided on) is
    kept only for the report's "Timing cost" table.

    Like run_backtest, the measured window starts in cash: the first orders are decided before
    `start` and filled at the close just before it.
    """
    assets = assets or config.PORTFOLIO_ASSETS
    lag = execution_lag(execution)          # 2 = next_close, 1 = same_close
    same_close = lag == 1
    closes, traded, signals, avg_move, cash = _prepare(strategy, prices, assets, cash_rate)

    # Include `lag` trading days before `start`: decide on the first, (next_close) fill on the second.
    idx = closes.index
    i0 = 0 if start is None else max(idx.searchsorted(pd.Timestamp(start)) - lag, 0)
    i1 = len(idx) if end is None else idx.searchsorted(pd.Timestamp(end), side="right")
    dates = idx[i0:i1]
    px, ok, sig = closes.to_numpy()[i0:i1], traded.to_numpy()[i0:i1], signals.to_numpy()[i0:i1]
    move, cash_r = avg_move.to_numpy()[i0:i1], cash.to_numpy()[i0:i1]

    k = len(assets)
    rate = config.COST_PER_TRADE * cost_multiplier
    log = RiskLog()
    breaker = CircuitBreaker(mode="backtest")
    value = [0.0] * k                     # money in each position
    cash_bal = 1.0
    held = [False] * k
    stop = [0.0] * k
    need_fresh = [False] * k              # after a stop-out, wait for the signal to switch off and on
    blocked = [False] * k                 # this entry chance was already counted as blocked
    open_trade = [None] * k               # bookkeeping for the trade list
    # next_close only: orders decided at a close, waiting to be filled at the asset's next close.
    exit_order = [None] * k               # "stop" or "signal"
    entry_order = [None] * k              # {"size", "distance", "loss_per_dollar"}
    trim_order = [False] * k
    trades = []
    equity_hist, weight_hist = [], []

    def sell(a, amount, j, reason=None):
        nonlocal cash_bal
        cash_bal += amount * (1 - rate)
        value[a] -= amount
        open_trade[a]["received"] += amount * (1 - rate)
        if reason:  # a full exit
            t = open_trade[a]
            ret = t["received"] / t["invested"] - 1
            trades.append({"asset": assets[a], "entry": t["entry"], "exit": dates[j], "return": ret,
                           "days": j - t["i"], "closed": True, "reason": reason,
                           "risk": t["risk"], "loss_of_account": (t["received"] - t["invested"]) / t["equity"]})
            log.worst_trade_loss = min(log.worst_trade_loss, trades[-1]["loss_of_account"])
            held[a], value[a], open_trade[a] = False, 0.0, None
            if reason == "stop":
                log.stop_exits += 1
                log.worst_stop_loss = min(log.worst_stop_loss, trades[-1]["loss_of_account"])
                if trades[-1]["loss_of_account"] < -config.MAX_RISK_PER_TRADE * (1 + 1e-9):
                    log.stops_over_budget += 1
            else:
                log.signal_exits += 1

    def buy(a, order, j, equity, sizes_today):
        """
        Open a position of `order["size"]` of the account at this close, if there's cash. True if bought.
        sizes_today = the total size of all buys filling at this close. Every buy's cost shrinks the
        account a little, so we divide by (1 + sizes_today x cost rate): then each position is exactly
        its size AFTER all of today's buying costs, never above 20%.
        """
        nonlocal cash_bal
        size = order["size"]
        amount = size * equity / (1 + sizes_today * rate)
        if amount * (1 + rate) > cash_bal:
            amount = max(cash_bal, 0.0) / (1 + rate)
            log.limited_by_cash += 1
        if amount <= 0:
            return False
        cash_bal -= amount * (1 + rate)
        # The stop is placed below the price we actually paid.
        value[a], held[a], stop[a] = amount, True, px[j, a] * (1 - order["distance"])
        open_trade[a] = {"entry": dates[j], "i": j, "invested": amount * (1 + rate), "received": 0.0,
                         "equity": equity, "risk": amount / equity * order["loss_per_dollar"]}
        log.entries += 1
        return True

    def trim(a, j):
        """Sell x so that (value - x) / (equity - x * rate) = TRIM_BACK_TO."""
        equity = cash_bal + sum(value)
        target = config.TRIM_BACK_TO
        if value[a] > target * equity:
            sell(a, (value[a] - target * equity) / (1 - target * rate), j)
            log.trims += 1

    def over_cap(a, j, equity):
        # (1 + 1e-9): ignore rounding dust, so a position bought at exactly 20% isn't trimmed at once.
        return held[a] and ok[j, a] and value[a] > config.MAX_POSITION_WEIGHT * equity * (1 + 1e-9)

    for j in range(len(dates)):
        # 1. Price moves and interest (nothing to do on the very first day: we start in cash).
        if j > 0:
            for a in range(k):
                if held[a]:
                    value[a] *= px[j, a] / px[j - 1, a]
            cash_bal *= 1 + cash_r[j]

        # 2. next_close: fill yesterday's orders at today's close (exits, then entries, then trims).
        #    An order for an asset whose market is shut today waits for its next open day.
        if not same_close:
            for a in range(k):
                if exit_order[a] and ok[j, a]:
                    sell(a, value[a], j, exit_order[a])
                    exit_order[a] = None
            equity = cash_bal + sum(value)  # every entry today is sized on the same account value
            filling = [a for a in range(k) if entry_order[a] and ok[j, a]]
            sizes_today = sum(entry_order[a]["size"] for a in filling)
            for a in filling:
                buy(a, entry_order[a], j, equity, sizes_today)
                entry_order[a] = None
            for a in range(k):
                if trim_order[a] and ok[j, a]:
                    if held[a]:
                        trim(a, j)
                    trim_order[a] = False

        # 3. DECISIONS at today's close. Exits first: the protective stop, then the "out" signal.
        for a in range(k):
            if held[a] and ok[j, a] and not exit_order[a]:
                reason = "stop" if px[j, a] <= stop[a] else ("signal" if sig[j, a] != 1 else None)
                if reason == "stop":
                    need_fresh[a] = True
                if reason and same_close:
                    sell(a, value[a], j, reason)
                elif reason:
                    exit_order[a] = reason
        for a in range(k):
            if sig[j, a] != 1:
                need_fresh[a] = blocked[a] = False

        # 4. Circuit breaker (see lab/breaker.py), on today's account value.
        breaker.update(j, dates[j], cash_bal + sum(value))

        # 5. Entries.
        equity = cash_bal + sum(value)
        for a in range(k):
            wants_in = (sig[j, a] == 1 and not held[a] and ok[j, a] and not need_fresh[a]
                        and not entry_order[a])
            if not wants_in or np.isnan(move[j, a]) or move[j, a] <= 0:
                continue
            # Positions that could be open after the next fills. A pending SALE still counts as open: its
            # market might be shut tomorrow (a holiday) while the new buy fills, which would briefly make 6
            # positions (found by the session-4 risk review). Waiting a day for the sale to fill is safer.
            n_open = sum(held) + sum(1 for x in entry_order if x)
            if not breaker.allows_new_trades or n_open >= config.MAX_OPEN_POSITIONS:
                if not blocked[a]:
                    blocked[a] = True
                    if not breaker.allows_new_trades:
                        log.blocked_by_breaker += 1
                    else:
                        log.blocked_by_max_positions += 1
                continue
            distance = config.STOP_ATR_MULTIPLE * move[j, a]        # e.g. 3 x 0.8% = 2.4%: where the stop goes
            # One-day buffer: the stop-sale fills a close later, so size as if the stop were 2 more average
            # daily moves away (e.g. 2 x 0.8% = 1.6%). The stop itself stays where it is.
            buffer = config.STOP_FILL_BUFFER_MOVES * move[j, a]
            # Loss per $1 invested if the stop is hit: the price fall (stop + buffer), plus the cost to buy
            # and to sell.
            fall = distance + buffer                                  # e.g. 2.4% + 1.6% = 4.0%
            loss_per_dollar = fall + rate + (1 - fall) * rate         # e.g. 4.0% + 0.15% + 0.14% = 4.3%
            risk_size = config.MAX_RISK_PER_TRADE / loss_per_dollar  # 1% / 4.3% = 23% of the account
            if risk_size < config.MAX_POSITION_WEIGHT:
                size, log.sized_by_risk_rule = risk_size, log.sized_by_risk_rule + 1
            else:
                size, log.sized_by_cap = config.MAX_POSITION_WEIGHT, log.sized_by_cap + 1
            order = {"size": size, "distance": distance, "loss_per_dollar": loss_per_dollar}
            if not same_close:
                entry_order[a] = order
                blocked[a] = False
            elif buy(a, order, j, equity, size):  # (the old engine sized each buy on its own)
                blocked[a] = False

        # 6. Trims: no position may be more than 20% of the account. same_close trims at once (and
        #    repeats, because one trim's costs can nudge an already-checked position over 20%);
        #    next_close sends a trim order, filled at the next close, so a position can sit a little
        #    above 20% for one day before it is cut back.
        equity = cash_bal + sum(value)
        if same_close:
            trimmed = True
            while trimmed:
                trimmed = False
                for a in range(k):
                    if over_cap(a, j, equity):
                        trim(a, j)
                        equity = cash_bal + sum(value)
                        trimmed = True
        else:
            for a in range(k):
                if over_cap(a, j, equity) and not exit_order[a]:
                    trim_order[a] = True

        log.max_open_positions = max(log.max_open_positions, sum(held))
        if equity > 0:  # only count days the asset's market was open (we can't trade when it's shut)
            open_values = [value[a] for a in range(k) if ok[j, a]]
            if open_values:
                log.max_position_weight = max(log.max_position_weight, max(open_values) / equity)
            log.days_over_cap += sum(1 for a in range(k) if over_cap(a, j, equity))
            for a in range(k):  # the 22% alert: a position ended the day well above the 20% limit. Checked even
                # when the asset's own market is shut: its share can still grow if the rest of the account falls.
                if held[a] and value[a] > config.POSITION_ALERT_WEIGHT * equity:
                    log.alerts.append({"date": dates[j], "asset": assets[a], "weight": value[a] / equity})
        equity_hist.append(equity)
        weight_hist.append([v / equity for v in value])

    log.breaker_events, log.hard_stop = breaker.events, breaker.hard_stop
    for a in range(k):  # positions still open at the end
        if held[a]:
            t = open_trade[a]
            trades.append({"asset": assets[a], "entry": t["entry"], "exit": dates[-1],
                           "return": (t["received"] + value[a]) / t["invested"] - 1, "days": len(dates) - 1 - t["i"],
                           "closed": False, "reason": "still open", "risk": t["risk"], "loss_of_account": np.nan})

    # Report from `start` on (drop the set-up days before it, unless there were none).
    first = 0 if start is None else idx.searchsorted(pd.Timestamp(start)) - i0
    equity = pd.Series(equity_hist, index=dates)
    returns = equity.pct_change()
    returns.iloc[0] = equity.iloc[0] - 1
    weights = pd.DataFrame(weight_hist, index=dates, columns=assets)
    cols = ["asset", "entry", "exit", "return", "days", "closed", "reason", "risk", "loss_of_account"]
    trade_df = pd.DataFrame(trades, columns=cols).sort_values("entry", ignore_index=True)
    if first:
        # The account started at 1.0 in cash; the set-up days' buying costs stay in the first return.
        equity, weights = equity.iloc[first:], weights.iloc[first:]
        returns = returns.iloc[first:]
        returns.iloc[0] = equity.iloc[0] - 1
    return PortfolioResult(equity, returns, weights.sum(axis=1), trade_df, cost_multiplier,
                           pd.Series(cash_r[first:], index=equity.index), risk=log, weights=weights)


def portfolio_lookahead_check(strategy, prices: dict, cash_rate, assets: list, n_cuts: int = 4,
                              execution: str | None = None):
    """
    Three tests: (1) each asset's signals (truncation), (2) the whole portfolio (truncation: its
    account value up to a cut-off date must be identical whether or not the later data exists), and
    (3) trade timing: the portfolio must trade at a close AFTER the one it decided on.
    """
    for a in assets:
        ok, msg = lookahead_check(strategy, prices[a])
        if not ok:
            return False, f"{a}: {msg}"
    full = simulate_portfolio(strategy, prices, cash_rate, assets=assets, execution=execution).equity
    for cut in pd.to_datetime(np.linspace(full.index[len(full) // 3].value, full.index[-2].value, n_cuts)):
        cut_prices = {a: prices[a].loc[:cut] for a in assets}
        part = simulate_portfolio(strategy, cut_prices, cash_rate, assets=assets, execution=execution).equity
        common = part.index.intersection(full.index)
        if not np.allclose(part.loc[common], full.loc[common], rtol=1e-10, atol=0):
            bad = common[~np.isclose(part.loc[common], full.loc[common], rtol=1e-10, atol=0)][0]
            return False, f"Portfolio value on {bad.date()} changed when later data was hidden: it peeks at the future."
    ok, timing_msg = portfolio_timing_check(prices, assets, execution)
    if not ok:
        return False, timing_msg
    return True, (f"Each asset's signals, and the whole portfolio's daily value, stayed identical when the future "
                  f"was hidden (6 cut-off dates per asset, {n_cuts} for the portfolio). " + timing_msg)


def portfolio_timing_check(prices: dict, assets: list, execution: str | None = None,
                           n_days: int = 3) -> tuple[bool, str]:
    """
    Trade timing for the portfolio. For a few days k and each asset, push that asset's close on
    day k up x3 and down to a third, using the probe strategy (it reacts to every close). Which
    assets are held after the trades at close k must not change: those trades were decided at
    close k-1. (Sizes may differ a little: an order is for a share of the account, worked out with
    the account value at the close it fills at, like a real "buy 20% of my account" order.)
    """
    probe = PriceRoseProbe()
    n = min(len(prices[a]) for a in assets)
    days = _probe_days(n, n_days, warm_up=config.STOP_ATR_DAYS + 5)
    tested = 0
    for a in assets:
        for k in days:
            day = prices[a].index[k]
            held = []
            for factor in (3.0, 1 / 3):
                p = {b: prices[b].loc[: prices[a].index[k + 2]] for b in assets}
                p[a] = _shocked(prices[a], k, factor)
                w = simulate_portfolio(probe, p, None, assets=assets, execution=execution).weights
                held.append((w.loc[:day] > 0))
            tested += 1
            if not held[0].equals(held[1]):
                return False, (f"Changing {a}'s closing price on {day.date()} changed what the portfolio held right "
                               "after that close: it trades at the same closing price it used to decide (look-ahead).")
    return True, (f"Trades happen at the close after the decision: changing a decision day's closing price never "
                  f"changed what the portfolio held after that close ({tested} asset-days tested).")


def evaluate_portfolio(strategy, prices: dict, cash_rate: pd.Series | None = None, is_demo: bool = False,
                       assets: list | None = None, execution: str | None = None):
    """Run the full Skeptic Checklist on the portfolio version of a strategy."""
    assets = assets or config.PORTFOLIO_ASSETS
    execution = execution or config.EXECUTION
    closes = pd.DataFrame({a: prices[a]["Close"] for a in assets}).ffill()
    equal = {a: 1 / len(assets) for a in assets}
    # First day every asset's signal is ready.
    ready = max(strategy.generate_signals(prices[a]).first_valid_index() for a in assets)
    first_day = closes.index[closes.index.get_loc(ready) + 1]

    def run(s, e, m=1.0, variant=None, ex=execution):
        return simulate_portfolio(variant or strategy, prices, cash_rate, s, e, m, assets, ex)

    subject = Subject(
        ticker="Portfolio", label=f"{strategy.label()} on {', '.join(assets)}", benchmark_name=BENCHMARK_NAME,
        first_day=first_day, last_day=closes.index[-1],
        run_strategy=run,
        run_benchmark=lambda s, e, m=1.0: fixed_mix(closes, equal, s, e, m, cash_rate, execution),
        run_index=lambda s, e, m=1.0: buy_and_hold(prices[config.BROAD_INDEX], s, e, m, cash_rate, execution),
        run_mix=lambda w, s, e, m=1.0: fixed_mix(closes, {a: w / len(assets) for a in assets}, s, e, m, cash_rate,
                                                 execution),
        lookahead=lambda: portfolio_lookahead_check(strategy, prices, cash_rate, assets, execution=execution),
        sensitivity=lambda s, e: sensitivity_grid(strategy, lambda v: run(s, e, 1.0, v)),
        run_same_close=lambda s, e: run(s, e, 1.0, None, "same_close"),
    )
    return evaluate_subject(subject, is_demo)
