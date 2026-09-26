"""
The backtest engine: "if we had followed these rules in the past, what would have happened?"

How it works, in plain English:
  1. The strategy looks at each day's CLOSING price and says 1 (be invested) or 0 (hold cash).
  2. We act on that decision the NEXT trading day. This one-day delay is the most important
     line in the file: it stops us using a price to make a decision we could only have made
     after seeing that price. (Using future info by accident is called "look-ahead bias".)
  3. Each day, if we're invested we earn the asset's daily return; in cash we earn 0.
  4. Every time we buy or sell, we pay costs (commission + slippage) on the amount traded.

Simplifications (fine for phase 1, listed so nobody forgets them):
  * Long-only: we can own the asset or hold cash, never bet on it falling (no shorting).
  * One asset at a time, 100% in or 100% out. Position sizing rules arrive in phase 2.
  * Cash earns no interest.
  * We trade at the next day's close, a simple and slightly conservative assumption.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from lab import config


@dataclass
class BacktestResult:
    equity: pd.Series      # account value over time, starting at 1.0 (= 100% of starting money)
    returns: pd.Series     # daily % change of the account, after costs
    position: pd.Series    # what we actually held each day (0 or 1)
    trades: pd.DataFrame   # one row per round trip: entry date, exit date, return
    cost_multiplier: float

    @property
    def n_trades(self) -> int:
        return len(self.trades)


def run_backtest(prices: pd.DataFrame, signal: pd.Series,
                 cost_multiplier: float = 1.0,
                 start=None, end=None) -> BacktestResult:
    """
    Run one backtest.

    prices          DataFrame with a 'Close' column.
    signal          Series of 0/1 (NaN during warm-up = treated as cash) decided at each day's close.
    cost_multiplier 1.0 = normal costs, 2.0 = double costs (a skeptic check).
    start, end      optional: only measure results inside this window. The signal is still
                    computed from all earlier data, just as it would have been in real life.
    """
    close = prices["Close"].astype(float)
    signal = signal.reindex(close.index).fillna(0.0).clip(0, 1)

    # THE KEY STEP: today's position is yesterday's decision.
    position = signal.shift(1).fillna(0.0)

    asset_ret = close.pct_change().fillna(0.0)

    if start is not None or end is not None:
        window = slice(start, end)
        position = position.loc[window]
        asset_ret = asset_ret.loc[window]
    # If we are already invested on the first day of the window, count that as a
    # purchase on day one: the window is judged as if we started with cash.
    prev_position = position.shift(1).fillna(0.0)
    turnover = (position - prev_position).abs()

    cost = turnover * config.COST_PER_TRADE * cost_multiplier
    strat_ret = position * asset_ret - cost
    equity = (1 + strat_ret).cumprod()

    trades = _list_trades(position, equity, strat_ret)
    return BacktestResult(equity, strat_ret, position, trades, cost_multiplier)


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
                 cost_multiplier: float = 1.0) -> BacktestResult:
    """The benchmark: buy on day one, never sell. (Still pays the cost of the first purchase.)"""
    close = prices["Close"]
    always_in = pd.Series(1.0, index=close.index)
    # A signal of 1 every day means we are invested from the first day of any later window.
    return run_backtest(prices, always_in, cost_multiplier=cost_multiplier, start=start, end=end)
