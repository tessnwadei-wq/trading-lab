"""
Moving-average trend filter (a classic, very simple rule).

Rule:  At each day's close, compare the price with its average over the last 200 days.
       * price above the average  -> be invested (1)
       * price at/below average   -> hold cash (0)
       The backtester trades at the NEXT day's close (you can't trade at a close you've
       only just seen).

Source: popularised by, among others, Meb Faber, "A Quantitative Approach to Tactical
Asset Allocation" (2007), which used a 10-month (~200-day) average. Traders have used the
200-day average as a "is the market in an uptrend?" line for decades.

Why it might work: markets tend to trend, and the worst crashes usually happen after
prices have already fallen below their long-term average. The cost: it often sells
after a drop and buys back after a rise ("whipsaws"), and can lag buy-and-hold in
strong bull markets.

Optional "band": only switch when price is band% above/below the average. A small band
reduces whipsaws. The default (0) is the plain rule.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import Strategy


class MATrend(Strategy):
    name = "ma_trend"
    description = "Hold the asset when price is above its 200-day moving average, otherwise hold cash."

    @classmethod
    def default_params(cls) -> dict:
        return {"ma_length": 200, "band": 0.0}

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        close = prices["Close"]
        n, band = int(self.params["ma_length"]), float(self.params["band"])

        # rolling(n).mean() on day t uses days t-n+1 .. t: only the past and today.
        ma = close.rolling(n).mean()

        if band == 0:
            signal = (close > ma).astype(float)
        else:
            # With a band we need memory: stay in the current state until price
            # crosses the upper band (buy) or the lower band (sell).
            upper, lower = ma * (1 + band), ma * (1 - band)
            state = np.where(close > upper, 1.0, np.where(close < lower, 0.0, np.nan))
            signal = pd.Series(state, index=close.index).ffill().fillna(0.0)

        signal[ma.isna()] = np.nan  # warm-up: not enough history yet
        return signal

    def sensitivity_grid(self) -> dict:
        return {
            "ma_length": [100, 125, 150, 175, 200, 225, 250, 275, 300],
            "band": [0.0, 0.01, 0.02, 0.03],
        }
