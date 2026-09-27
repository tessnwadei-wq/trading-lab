"""
Volatility targeting ("hold less when the market is jumpy"). Idea #4.

PRE-REGISTERED: the rules below were frozen in strategies/specs/vol_target.md and committed on their own
(commit SPEC_COMMIT) before any code was written and before any look at 2018+ results. Don't change them:
any change is a new idea with a new spec (see the spec's section 9).

Rule (spec section 3):
  At the close of the LAST TRADING DAY OF EACH MONTH:
    1. vol = standard deviation of the last `vol_days` (21) daily returns x sqrt(252)   (yearly bumpiness)
    2. target weight w = min(1, target_vol / vol), with target_vol = 12% a year. Never above 100%: no borrowing.
    3. Hold w in the asset and 1 - w in cash. The backtester trades at the NEXT close, and between month-ends
       the weight simply drifts with prices (no trades, no costs).
  Calm market (vol 8%) -> 100% invested. Stormy market (vol 40%) -> 30% invested.

Sources: Moreira & Muir (2017), "Volatility-Managed Portfolios", Journal of Finance; Harvey et al. (2018), "The
Impact of Volatility Targeting", Journal of Portfolio Management. Counterpoint: Cederburg et al. (2020), JFE.
Differences from the papers (decided in the spec): no borrowing (weight capped at 100%), target / volatility
rather than target / variance, and a plain 21-day standard deviation.

Why it might work: bumpiness clusters (storms follow storms), but stormy periods haven't paid proportionally more
return, so cutting exposure when volatility jumps might improve return per unit of risk. Why it might not: the
same-risk mix (a constant "X% stock + cash") may do just as well, and after a crash the rule stays cautious while
prices rebound (e.g. 2020).

IMPLEMENTATION NOTE: which day is "the last trading day of the month"? The rule may only use what's known at that
close, and the price file can't say whether tomorrow is a trading day (using the next row would peek at the future).
So a day counts as the month's last trading day if the next weekday (Mon-Fri) is in a new month. If that weekday
turns out to be a holiday (e.g. a month ending on Good Friday or Memorial Day), no decision was made at the true
last trading day, so the rule decides at the first trading day of the new month instead: one day late, and never
using future prices. This is written down here and in the report, and was decided before any test-period look.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lab import config
from strategies.base import Strategy

# The commit that froze the rules (strategies/specs/vol_target.md), made before any test-period look.
SPEC_PATH = "strategies/specs/vol_target.md"
SPEC_COMMIT = "fc6436bb992c237425a67de0cb4f6917b326c867"


def month_end_decision_days(index: pd.DatetimeIndex) -> np.ndarray:
    """
    True on the days the monthly decision is made, using only the calendar up to that day:
      * the next weekday is in a new month (normally the month's last trading day), or
      * it's the first trading day of a month in which no decision was made for the previous month
        (the last weekday of that month was a holiday).
    """
    days = pd.DatetimeIndex(index)
    next_weekday = days + pd.offsets.BDay(1)
    last_day = np.asarray(next_weekday.month != days.month)
    out = last_day.copy()
    months = days.to_period("M")
    for i in range(1, len(days)):
        if months[i] != months[i - 1] and not last_day[i - 1] and not out[i - 1]:
            out[i] = True           # previous month's last weekday was a holiday: decide now, a day late
    return out


class VolTarget(Strategy):
    name = "vol_target"
    description = ("Volatility targeting: at each month-end hold min(100%, 12% / recent 21-day volatility) of the "
                   "asset and the rest in cash (pre-registered, no parameter search).")
    fractional = True                 # holds any weight between 0% and 100%
    sample_size_rule = "rebalances"   # spec section 7: count active rebalances, not round trips
    how_chosen = "pre-registered values (spec strategies/specs/vol_target.md), no search"
    spec_path = SPEC_PATH
    spec_commit = SPEC_COMMIT
    report_note = ("**Implementation note (decided before any test-period look):** the monthly decision is made at a "
                   "day whose next weekday falls in a new month. When that weekday is a holiday (e.g. a month ending "
                   "on Good Friday or Memorial Day), the decision is made at the first trading day of the new month "
                   "instead, one day late, so the rule never needs tomorrow's data. The rules are in the spec; the "
                   "code is `strategies/vol_target.py`.")

    @classmethod
    def default_params(cls) -> dict:
        return {"target_vol": 0.12, "vol_days": 21}

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        close = prices["Close"]
        target_vol, n = float(self.params["target_vol"]), int(self.params["vol_days"])
        # Daily returns up to and including today; rolling(n) on day t uses days t-n+1 .. t only.
        vol = close.pct_change().rolling(n).std() * np.sqrt(config.TRADING_DAYS_PER_YEAR)
        weight = (target_vol / vol).clip(upper=1.0, lower=0.0)
        decide = month_end_decision_days(close.index) & vol.notna().to_numpy()
        # Only month-end decisions count; in between, keep the last decision (the weight then drifts in the engine).
        signal = weight.where(decide).ffill()   # NaN before the first decision = warm-up (cash)
        return signal

    def sensitivity_grid(self) -> dict:
        # Fixed in the spec (section 5). Checks the frozen choice; never used to pick a new one.
        return {"target_vol": [0.08, 0.10, 0.12, 0.14, 0.16], "vol_days": [10, 21, 42, 63]}
