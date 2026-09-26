"""
Scorecard numbers for a backtest. Every term is explained in LEARNING.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lab import config

DAYS = config.TRADING_DAYS_PER_YEAR


def total_return(equity: pd.Series) -> float:
    """Growth from starting money (1.0) to the end. 0.50 = +50%."""
    return float(equity.iloc[-1] - 1.0)


def cagr(equity: pd.Series) -> float:
    """Compound Annual Growth Rate: the steady yearly return that gives the same end result."""
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    if years <= 0 or equity.iloc[-1] <= 0:
        return 0.0
    return float(equity.iloc[-1] ** (1 / years) - 1)


def volatility(returns: pd.Series) -> float:
    """How bumpy the ride is: yearly standard deviation of daily returns."""
    return float(returns.std() * np.sqrt(DAYS))


def sharpe(returns: pd.Series) -> float:
    """
    Sharpe ratio: return per unit of bumpiness (risk). Higher is better.
    Rough guide: below 0.5 weak, around 1 good, above 2 = suspicious in a backtest.
    (We assume cash earns 0%, to keep it simple.)
    """
    sd = returns.std()
    return float(returns.mean() / sd * np.sqrt(DAYS)) if sd > 0 else 0.0


def drawdown_series(equity: pd.Series) -> pd.Series:
    """For each day: how far below its previous peak is the account? (0 = at a new high.)"""
    peak = equity.cummax().clip(lower=1.0)  # starting money counts as the first peak
    return equity / peak - 1


def max_drawdown_info(equity: pd.Series) -> dict:
    """
    The worst peak-to-trough fall, when it happened, and how long recovery took.
    Recovery = trading days from the trough until the account got back to the old peak.
    """
    dd = drawdown_series(equity)
    trough = dd.idxmin()
    max_dd = float(dd.min())
    if max_dd == 0:
        return {"max_dd": 0.0, "peak": None, "trough": None, "recovered": None, "recovery_days": 0}
    peak_level = equity.cummax().clip(lower=1.0).loc[trough]
    before = equity.loc[:trough]
    at_peak = before[before >= peak_level]
    peak_date = at_peak.index[-1] if len(at_peak) else equity.index[0]
    after = equity.loc[trough:]
    back = after[after >= peak_level]
    recovered = back.index[0] if len(back) else None
    recovery_days = (len(equity.loc[trough:recovered]) - 1) if recovered is not None else None
    return {"max_dd": max_dd, "peak": peak_date, "trough": trough,
            "recovered": recovered, "recovery_days": recovery_days}


def summarize(result) -> dict:
    """All headline numbers for one BacktestResult, as a dict."""
    eq, rets, pos, trades = result.equity, result.returns, result.position, result.trades
    closed = trades[trades["closed"]] if len(trades) else trades
    dd = max_drawdown_info(eq)
    return {
        "total_return": total_return(eq),
        "cagr": cagr(eq),
        "volatility": volatility(rets),
        "sharpe": sharpe(rets),
        "max_drawdown": dd["max_dd"],
        "recovery_days": dd["recovery_days"],
        "n_trades": int(len(trades)),
        "win_rate": float((closed["return"] > 0).mean()) if len(closed) else float("nan"),
        "time_in_market": float(pos.mean()),
    }

