"""
Interest on cash.

When a strategy is out of the market its money sits in cash, and in real life cash earns
interest: roughly the short-term US Treasury bill ("T-bill") rate. Ignoring that makes
strategies that spend time in cash look worse than they are (in 2023-24 cash paid ~5% a year).

We use the 13-week T-bill yield (Yahoo ticker ^IRX). Yahoo quotes it in % per year, so a
value of 4.07 means 4.07% a year. We turn that into a daily rate:

    daily cash return = (yearly % / 100) / 252 trading days

Two details that keep it honest:
  * No look-ahead: the rate used on day t is the one quoted at the close of day t-1, which
    you would have known when you decided to sit in cash.
  * Different calendars: XIU.TO trades on Canadian holidays and not on some US ones, so the
    rate is lined up to each asset's own trading days and gaps are filled with the last known rate.

SIMPLIFICATION (also noted in lab/config.py): the US rate is used for every asset, including
the Canadian XIU.TO. Canadian T-bill rates have usually been close to US ones.
"""

from __future__ import annotations

import warnings

import pandas as pd

from lab import config

MISSING_WARNING = (
    "Cash interest data (^IRX) is not available, so cash earns 0% in this run and Sharpe ratios are "
    "measured against a 0% cash rate. To fix it, run this on your PC (it downloads data/csv/IRX.csv):\n"
    "    python run_lab.py --refresh"
)


def daily_cash_returns(irx: pd.DataFrame | None) -> pd.Series | None:
    """
    Turn ^IRX prices (a 'Close' column in % per year) into a daily cash return series,
    already lagged by one day so it only uses information known in advance.

    Returns None (and warns loudly) when IRX data is missing: the lab then assumes 0%.
    """
    if irx is None or irx.empty:
        warnings.warn(MISSING_WARNING, stacklevel=2)
        return None
    yearly_pct = irx["Close"].astype(float)
    return (yearly_pct / 100 / config.TRADING_DAYS_PER_YEAR).shift(1).dropna()


def align_cash(cash_rate: pd.Series | None, index: pd.DatetimeIndex) -> pd.Series:
    """
    Line the daily cash rate up with a particular asset's trading days.

    Days the T-bill market was closed reuse the last known rate. With no data at all, cash earns 0.
    """
    if cash_rate is None:
        return pd.Series(0.0, index=index)
    combined = cash_rate.reindex(cash_rate.index.union(index)).ffill()
    return combined.reindex(index).fillna(0.0)
