"""
Made-up "practice" prices, used ONLY when real data can't be downloaded.

Why this exists: the cloud computer that built this lab was not allowed to reach Yahoo
or Stooq. To prove every part of the lab works end to end, we generate fake prices with
roughly realistic behaviour:
  * daily ups and downs of a realistic size,
  * the four assets moving together (or not) roughly like the real ones do,
  * stress periods placed where 2008, 2020 and 2022 happened, so the regime check has
    something to look at.

IMPORTANT: results on this data say NOTHING about real markets. They are for learning
how the tools work. A strategy tested only on demo data can never be approved.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

# Fixed, so every run produces the same fake history. Seed 1 was the first one tried after
# adding rebounds, and gives a fake S&P that behaves broadly like the real one (rises over
# time, worst fall around -50%). The seed was NOT picked to make any strategy look good.
SEED = 1

# Per-asset settings: yearly drift (average return), yearly volatility (size of moves),
# and a starting price. Numbers are loosely inspired by long-run history.
ASSETS = {
    #          drift   vol    start price
    "SPY":    (0.09,  0.17,  90.0),
    "XIU.TO": (0.06,  0.15,  12.0),
    "GLD":    (0.06,  0.17,  43.0),
    "CAD=X":  (0.00,  0.08,  1.22),
}

# How strongly each asset's daily moves go along with the others (correlation).
# Order: SPY, XIU.TO, GLD, CAD=X. CAD=X is negative because when stocks fall, the
# Canadian dollar usually weakens, so USD/CAD goes UP.
CORRELATION = np.array([
    [1.00,  0.75,  0.05, -0.45],
    [0.75,  1.00,  0.15, -0.55],
    [0.05,  0.15,  1.00, -0.20],
    [-0.45, -0.55, -0.20, 1.00],
])

# Stress and recovery periods: (start, end, extra yearly drift for stocks, volatility multiplier).
# Real markets tend to bounce back hard after crashes, so each big fall has a rebound after it.
STRESS = [
    ("2008-06-01", "2009-03-09", -0.60, 2.6),
    ("2009-03-10", "2010-04-23", +0.45, 1.5),
    ("2011-07-25", "2011-10-03", -0.45, 1.8),
    ("2015-08-10", "2016-02-11", -0.25, 1.4),
    ("2018-10-01", "2018-12-24", -0.70, 1.6),
    ("2019-01-02", "2019-12-31", +0.20, 1.0),
    ("2020-02-20", "2020-03-23", -3.50, 4.5),
    ("2020-03-24", "2020-08-31", +1.10, 1.8),
    ("2022-01-03", "2022-10-12", -0.40, 1.5),
    ("2022-10-13", "2023-07-31", +0.25, 1.1),
]


@lru_cache(maxsize=1)
def make_demo_prices(end: str = "2026-09-25") -> dict:
    """Return {ticker: DataFrame with a 'Close' column} of made-up daily prices."""
    rng = np.random.default_rng(SEED)
    dates = pd.bdate_range("2004-01-02", end)  # weekdays only, like a trading calendar
    n, dt = len(dates), 1 / 252

    # Correlated random shocks. Student-t (df=4) gives occasional big days, like real markets.
    raw = rng.standard_t(df=4, size=(n, 4)) / np.sqrt(2.0)
    shocks = raw @ np.linalg.cholesky(CORRELATION).T

    # Build a per-day volatility multiplier and a stock-market drift adjustment.
    vol_mult = np.ones(n)
    stress_drift = np.zeros(n)
    for start, stop, drift, mult in STRESS:
        mask = (dates >= start) & (dates <= stop)
        vol_mult[mask] = mult
        stress_drift[mask] = drift

    out = {}
    for i, (ticker, (mu, sigma, p0)) in enumerate(ASSETS.items()):
        # How much this asset reacts to stock-market stress.
        beta = {"SPY": 1.0, "XIU.TO": 1.0, "GLD": 0.1, "CAD=X": -0.25}[ticker]
        vm = 1 + (vol_mult - 1) * abs(beta)
        daily = (mu + beta * stress_drift) * dt + sigma * vm * np.sqrt(dt) * shocks[:, i]
        close = p0 * np.exp(np.cumsum(daily))
        out[ticker] = pd.DataFrame({"Close": close}, index=pd.DatetimeIndex(dates, name="Date"))
    return out
