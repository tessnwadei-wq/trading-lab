"""
Time-series momentum ("hold an asset only while its past year beat cash"). Idea #5, a portfolio-only idea.

PRE-REGISTERED: the rules below were frozen in strategies/specs/ts_momentum.md and committed on their own
(commit SPEC_COMMIT) before any code was written and before any look at 2018+ results. Don't change them:
any change is a new idea with a new spec (see the spec's section 9).

Rule (spec section 3), for each asset on its own trading calendar:
  At the close of the LAST TRADING DAY OF EACH MONTH (same month-end rule as vol_target):
    1. R = the asset's total return over the last 12 months (month-end close vs the month-end close 12 months earlier;
       dividend-adjusted prices, so dividends count).
    2. C = what cash (the T-bill rate) earned over exactly the same days.
    3. Signal = 1 (hold) if R > C, else 0 (cash for that slot).
  The portfolio engine (lab/portfolio.py) turns the signals into trades at the NEXT close, sizes each holding with the
  risk rules (at most 20%, 1% risk per trade), resizes held positions every month-end (rebalance_days below), and
  lets a stopped-out asset back in at the next month-end if its signal is still "hold".

Source: Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum", Journal of Financial Economics.
Differences from the paper (decided in the spec): long-only (cash instead of a short), no volatility scaling or
leverage, four ETFs instead of 58 futures, and every lab risk rule applies.

Why it might work: markets trend over months (slow-moving news, herding), so an asset that has beaten cash over the
last year tends to keep doing so for a while. Why it might not: trends reverse suddenly (2020), each switch costs money
and a month of lag, and later studies say the published profits came mostly from volatility scaling, which we don't do.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lab.cash import align_cash
from strategies.base import Strategy
from strategies.vol_target import month_end_decision_days

# The commit that froze the rules (strategies/specs/ts_momentum.md), made before any code or test-period look.
SPEC_PATH = "strategies/specs/ts_momentum.md"
SPEC_COMMIT = "30c8706d96354ebf52b67911aef0bbe074c0c0bf"


class TSMomentum(Strategy):
    name = "ts_momentum"
    description = ("Time-series momentum on SPY, XIU.TO, GLD and IEF: at each month-end, hold an asset (up to 20% of "
                   "the account, sized by the risk rules) only if its past 12-month total return beat the T-bill return "
                   "over the same 12 months, otherwise hold cash for that slot (pre-registered, no parameter search).")
    sample_size_rule = "signal_changes"   # spec section 7: count month-end signal flips, not round trips
    control_weight = 0.20                 # spec section 6: the fair control holds 20% of each asset, always
    how_chosen = "pre-registered values (spec strategies/specs/ts_momentum.md), no search"
    spec_path = SPEC_PATH
    spec_commit = SPEC_COMMIT
    report_note = ("**Implementation notes (decided in the spec, before any test-period look):** the monthly decision "
                   "is made at a day whose next weekday falls in a new month (a day late if that weekday is a holiday, "
                   "as in `vol_target`). Every month-end, a held asset whose signal stays \"hold\" is resized to a fresh "
                   "target (buying or selling only the difference) and its stop is reset below that fill price; after a "
                   "stop-out the asset may be bought again at the next month-end if its signal is still \"hold\". "
                   "The rules are in the spec; the code is `strategies/ts_momentum.py` and `lab/portfolio.py`.")

    def __init__(self, cash_rate: pd.Series | None = None, **params):
        super().__init__(**params)
        # The daily T-bill return (lab.cash.daily_cash_returns): the hurdle each asset must beat. None = 0%.
        self.cash_rate = cash_rate

    @classmethod
    def default_params(cls) -> dict:
        return {"lookback_months": 12, "skip_months": 0}

    def with_params(self, **changes) -> "TSMomentum":
        return type(self)(cash_rate=self.cash_rate, **{**self.params, **changes})

    def rebalance_days(self, prices: pd.DataFrame) -> pd.Series:
        """The month-end decision days: when the portfolio engine resizes held positions and re-arms after a stop."""
        return pd.Series(month_end_decision_days(prices.index), index=prices.index)

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        close = prices["Close"].astype(float)
        look, skip = int(self.params["lookback_months"]), int(self.params["skip_months"])
        # Growth of $1 left in cash, on this asset's own days. The cash return for day t is known at close t-1
        # (lab/cash.py), so using it up to today's close never peeks.
        cash_index = (1 + align_cash(self.cash_rate, close.index)).cumprod()

        decide = month_end_decision_days(close.index)
        days = close.index[decide]
        # For the k-th decision day: the window runs from decision day k-skip-look to decision day k-skip.
        end = pd.Series(days, index=days).shift(skip)
        start = pd.Series(days, index=days).shift(skip + look)
        ok = end.notna() & start.notna()
        e, s = end[ok], start[ok]
        asset_ret = close.loc[e].to_numpy() / close.loc[s].to_numpy() - 1
        cash_ret = cash_index.loc[e].to_numpy() / cash_index.loc[s].to_numpy() - 1
        hold = pd.Series((asset_ret > cash_ret).astype(float), index=e.index)   # a tie counts as cash

        # Only month-end decisions count; in between, keep the last decision. NaN before the first one = warm-up.
        signal = pd.Series(np.nan, index=close.index)
        signal.loc[hold.index] = hold
        return signal.ffill()

    def sensitivity_grid(self) -> dict:
        # Fixed in the spec (section 5). Checks the frozen choice on training data; never used to pick a new one.
        return {"lookback_months": [6, 9, 12, 15, 18], "skip_months": [0, 1]}
