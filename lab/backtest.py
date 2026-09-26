"""
The backtest engine: "if we had followed these rules in the past, what would have happened?"

How it works, in plain English:
  1. The strategy looks at each day's CLOSING price and says 1 (be invested) or 0 (hold cash).
  2. TRADE TIMING. We only have closing prices, and you can't trade at a closing price you have only
     just seen: by then the market is shut. So a decision made from day t's close is traded at the
     NEXT day's close (t+1), and gains or losses count from there (the move from t+1 to t+2).
     In code: the position that earns day i's move (close i-1 -> close i) is the decision from
     day i-2. This two-day gap is the most important line in the file: it stops us trading at a
     price we used to make the decision. (Using information you couldn't have had at the time is
     called "look-ahead bias".)
     The old behaviour, execution="same_close" (trade at the very close you decided on, a one-day
     gap), is kept only so reports can show how much it flattered results. See config.EXECUTION.
  3. Each day, if we're invested we earn the asset's daily return; in cash we earn the
     T-bill interest rate (see lab/cash.py), or 0 if that data is missing.
  4. Every time we buy or sell, we pay costs (commission + slippage) on the amount traded.

Simplifications (fine for phase 1, listed so nobody forgets them):
  * Long-only: we can own the asset or hold cash, never bet on it falling (no shorting).
  * One asset at a time, 100% in or 100% out. Position sizing and the risk rules live in
    lab/portfolio.py (phase 2).
  * Trades fill exactly at the next close (plus the slippage cost). In real life you'd send a
    "market-on-close" order during day t+1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from lab import config
from lab.cash import align_cash


@dataclass
class BacktestResult:
    equity: pd.Series      # account value over time, starting at 1.0 (= 100% of starting money)
    returns: pd.Series     # daily % change of the account, after costs
    position: pd.Series    # what we actually held each day (0 or 1)
    trades: pd.DataFrame   # one row per round trip: entry date, exit date, return
    cost_multiplier: float
    cash_returns: pd.Series = None  # the daily cash (T-bill) rate on the same days: Sharpe's yardstick

    def __post_init__(self):
        if self.cash_returns is None:
            self.cash_returns = pd.Series(0.0, index=self.returns.index)

    @property
    def n_trades(self) -> int:
        return len(self.trades)


def execution_lag(execution: str | None) -> int:
    """
    How many days after a decision its position starts earning the asset's move.
      next_close: decide at close t, trade at close t+1, earn the move t+1 -> t+2  => 2
      same_close: decide at close t, trade at close t,   earn the move t   -> t+1  => 1
    """
    execution = execution or config.EXECUTION
    if execution not in config.EXECUTION_MODES:
        raise ValueError(f"execution must be one of {config.EXECUTION_MODES}, not {execution!r}")
    return 2 if execution == "next_close" else 1


def run_backtest(prices: pd.DataFrame, signal: pd.Series,
                 cost_multiplier: float = 1.0,
                 start=None, end=None, cash_rate: pd.Series | None = None,
                 execution: str | None = None) -> BacktestResult:
    """
    Run one backtest.

    prices          DataFrame with a 'Close' column.
    signal          Series of 0/1 (NaN during warm-up = treated as cash) decided at each day's close.
    cost_multiplier 1.0 = normal costs, 2.0 = double costs (a skeptic check).
    start, end      optional: only measure results inside this window. The signal is still
                    computed from all earlier data, just as it would have been in real life.
    cash_rate       optional daily cash return series (from lab.cash.daily_cash_returns).
                    None = cash earns 0%.
    execution       "next_close" (default, from config.EXECUTION) or "same_close" (the old,
                    optimistic timing; only for the report's "Timing cost" comparison).
    """
    close = prices["Close"].astype(float)
    signal = signal.reindex(close.index).fillna(0.0).clip(0, 1)

    # THE KEY STEP: the position earning day i's move was decided at the close of day i-2 and
    # bought at the close of day i-1 (next_close). With same_close it's the decision of day i-1.
    position = signal.shift(execution_lag(execution)).fillna(0.0)

    asset_ret = close.pct_change().fillna(0.0)
    cash_ret = align_cash(cash_rate, close.index)

    if start is not None or end is not None:
        window = slice(start, end)
        position = position.loc[window]
        asset_ret = asset_ret.loc[window]
        cash_ret = cash_ret.loc[window]
    # If we are already invested on the first day of the window, count that as a
    # purchase at the close just before it: the window is judged as if we started with cash.
    prev_position = position.shift(1).fillna(0.0)
    turnover = (position - prev_position).abs()

    cost = turnover * config.COST_PER_TRADE * cost_multiplier
    # Invested share earns the asset's return; the rest sits in cash and earns interest.
    strat_ret = position * asset_ret + (1 - position) * cash_ret - cost
    equity = (1 + strat_ret).cumprod()

    trades = _list_trades(position, equity, strat_ret)
    return BacktestResult(equity, strat_ret, position, trades, cost_multiplier, cash_ret)


def _list_trades(position: pd.Series, equity: pd.Series, strat_ret: pd.Series) -> pd.DataFrame:
    """Turn the daily position series into a list of round-trip trades."""
    rows = []
    pos = position.to_numpy()
    dates = position.index
    rets = strat_ret.to_numpy()
    in_trade, entry_i = False, 0
    for i in range(len(pos)):
        if not in_trade and pos[i] > 0:
            in_trade, entry_i = True, i
        elif in_trade and pos[i] == 0:
            # The exit cost is charged on day i (the day we are back in cash).
            rows.append(_trade_row(dates, rets, entry_i, i, closed=True))
            in_trade = False
    if in_trade:  # still holding at the end of the data
        rows.append(_trade_row(dates, rets, entry_i, len(pos) - 1, closed=False))
    return pd.DataFrame(rows, columns=["entry", "exit", "return", "days", "closed"])


def _trade_row(dates, rets, i0, i1, closed):
    growth = float(np.prod(1 + rets[i0:i1 + 1]))
    return {"entry": dates[i0], "exit": dates[i1], "return": growth - 1,
            "days": i1 - i0, "closed": closed}


def buy_and_hold(prices: pd.DataFrame, start=None, end=None,
                 cost_multiplier: float = 1.0, cash_rate: pd.Series | None = None,
                 execution: str | None = None) -> BacktestResult:
    """
    The benchmark: buy at the start, never sell. (Still pays the cost of the first purchase.)
    The decision to buy doesn't depend on any price, so it can be made in advance and the
    purchase happens at the close just before the window, under either execution setting.
    """
    close = prices["Close"]
    always_in = pd.Series(1.0, index=close.index)
    # A signal of 1 every day means we are invested from the first day of any later window.
    return run_backtest(prices, always_in, cost_multiplier=cost_multiplier, start=start, end=end,
                        cash_rate=cash_rate, execution=execution)


def fixed_mix(closes: pd.DataFrame, weights: dict, start=None, end=None,
              cost_multiplier: float = 1.0, cash_rate: pd.Series | None = None,
              execution: str | None = None) -> BacktestResult:
    """
    A "set and forget" mix: keep fixed percentages in some assets and the rest in cash.

    Used for two benchmarks:
      * the same-risk mix, e.g. {"SPY": 0.6} = 60% SPY + 40% cash earning interest;
      * equal-weight buy-and-hold of several assets, e.g. 1/3 each of SPY, XIU.TO and GLD.

    closes   DataFrame of closing prices, one column per asset.
    weights  {column: share of the account}; the shares may add up to less than 1 (the rest is cash).

    Prices drift the mix away from its targets, so once a month we trade back to the targets and
    pay costs on what we traded. The trade happens at the close before the first trading day of
    each month. Like run_backtest, the window starts in cash and buys at the close before day one.

    Trade timing (execution):
      same_close  each rebalance is sized with the holdings at the very close it trades at.
      next_close  (default) the rebalance is worked out at the PREVIOUS close, as a number of units
                  of each asset, and those units are traded one close later at the new prices. So a
                  little drift is left over, just as in real life. (The first purchase needs no
                  price information, 1.0 in cash times the weights, so it is the same in both.)
    """
    lag = execution_lag(execution)
    closes = closes[list(weights)].ffill()
    rets = closes.pct_change().fillna(0.0)
    cash = align_cash(cash_rate, closes.index)
    if start is not None or end is not None:
        rets, cash = rets.loc[start:end], cash.loc[start:end]

    w = np.array([weights[c] for c in rets.columns], dtype=float)
    r, c = rets.to_numpy(), cash.to_numpy()
    months = rets.index.to_period("M")
    new_month = np.array([i == 0 or months[i] != months[i - 1] for i in range(len(rets))])
    holdings, cash_bal = np.zeros(len(w)), 1.0
    pending = None  # next_close: the rebalance trade worked out at the previous close, in today's money
    equity = np.empty(len(rets))
    rate = config.COST_PER_TRADE * cost_multiplier
    for i in range(len(rets)):
        # --- Trades at the close before day i (holdings are at that close's values here). ---
        if i == 0 or (lag == 1 and new_month[i]):
            # Trade exactly back to the targets, sized at the close we trade at. (The first purchase
            # needs no price information: 1.0 in cash times the weights.) Costs come out of everything.
            total = holdings.sum() + cash_bal
            total -= np.abs(w * total - holdings).sum() * rate
            holdings, cash_bal = w * total, total * (1 - w.sum())
        elif lag == 2 and pending is not None:
            # Trade the units worked out at the previous close, at this close's prices. Money for the
            # trade and its costs comes from cash (which can dip a hair below zero for a day when the
            # mix is 100% invested; it is charged the cash rate for that day).
            cash_bal -= pending.sum() + np.abs(pending).sum() * rate
            holdings = holdings + pending
        pending = None
        # next_close: at this same close, work out the NEXT close's rebalance (if tomorrow's close is
        # the last one before a new month), in units, i.e. as money at today's prices.
        if lag == 2 and i + 1 < len(rets) and new_month[i + 1] and i > 0:
            pending = w * (holdings.sum() + cash_bal) - holdings
        # --- Day i's price moves and interest. ---
        holdings = holdings * (1 + r[i])
        if pending is not None:
            pending = pending * (1 + r[i])        # a fixed number of units, re-priced at the next close
        cash_bal *= 1 + c[i]
        equity[i] = holdings.sum() + cash_bal

    equity = pd.Series(equity, index=rets.index)
    returns = equity.pct_change()
    returns.iloc[0] = equity.iloc[0] - 1
    position = pd.Series(w.sum(), index=rets.index)
    trades = pd.DataFrame([{"entry": rets.index[0], "exit": rets.index[-1], "return": equity.iloc[-1] - 1,
                            "days": len(rets) - 1, "closed": False}])
    return BacktestResult(equity, returns, position, trades, cost_multiplier, cash)
