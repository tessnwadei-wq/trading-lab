"""
Overfit demo: a DELIBERATELY bad research process, so we can watch the skeptic catch it.

What it does:
  Rule family: "Be invested when the fast moving average is more than `band` above the
  slow moving average; once in, stay in for at least `min_hold` days."
  That's 4 knobs. We try EVERY combination on the training data (2005-2017), about 2,000
  of them, and keep whichever had the best Sharpe ratio.

Why that's a trap: with thousands of tries, some combination will look brilliant just by
fitting the random wiggles of that particular history. Those wiggles won't repeat, so the
"best" settings usually disappoint on new data. This is called overfitting (or
"curve fitting", or "data snooping").

What to watch for in the report:
  * training results far better than test (2018+) results,
  * a parameter-sensitivity grid where the chosen cell is a lonely bright spot,
  * a huge number of combinations tried (the skeptic reports it).

Source: this is a teaching example, not a trading idea. See Bailey, Borwein, Lopez de Prado
and Zhu, "Pseudo-Mathematics and Financial Charlatanism" (2014) for the maths behind why
backtest-optimised strategies disappoint.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from lab import config
from lab.backtest import run_backtest
from lab.metrics import result_sharpe
from strategies.base import Strategy

SEARCH_SPACE = {
    "fast": [5, 10, 15, 20, 25, 30, 40, 50],
    "slow": [60, 80, 100, 120, 150, 180, 210, 250],
    "band": [0.0, 0.005, 0.01, 0.02, 0.03, 0.05],
    "min_hold": [1, 5, 10, 20, 40],
}


class OverfitDemo(Strategy):
    name = "overfit_demo"
    description = ("Fast/slow moving-average crossover with a band and a minimum holding period, "
                   "all four parameters picked by brute-force search on 2005-2017 data.")

    def __init__(self, **params):
        super().__init__(**params)
        self.search_results: pd.DataFrame | None = None  # filled in by fit()

    @classmethod
    def default_params(cls) -> dict:
        return {"fast": 20, "slow": 100, "band": 0.0, "min_hold": 1}

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        close = prices["Close"]
        fast = close.rolling(int(self.params["fast"])).mean()
        slow = close.rolling(int(self.params["slow"])).mean()
        want_in = (fast > slow * (1 + float(self.params["band"]))).to_numpy()

        # Apply the minimum holding period with a simple loop (easy to read).
        min_hold = int(self.params["min_hold"])
        out = np.zeros(len(close))
        in_position, held_for = False, 0
        for i in range(len(close)):
            if in_position:
                held_for += 1  # days since we bought
                # Stay in if the rule still says "in", or if we haven't held long enough yet.
                in_position = bool(want_in[i]) or held_for < min_hold
            else:
                in_position, held_for = bool(want_in[i]), 0
            out[i] = 1.0 if in_position else 0.0

        signal = pd.Series(out, index=close.index)
        signal[slow.isna() | fast.isna()] = np.nan
        return signal

    def fit(self, train_prices: pd.DataFrame, cash_rate: pd.Series | None = None) -> "OverfitDemo":
        """
        Brute-force search on TRAINING data only (the caller must pass data up to 2017).
        Returns a new strategy with the best parameters, and remembers every result.
        """
        # Hard guard for the CLAUDE.md rule "never tune parameters on the test period".
        if train_prices.index.max() > config.TRAIN_END:
            raise ValueError("fit() was given data after TRAIN_END: that would be tuning on the test period.")
        rows = []
        for fast, slow, band, min_hold in itertools.product(*SEARCH_SPACE.values()):
            if fast >= slow:
                continue
            candidate = self.with_params(fast=fast, slow=slow, band=band, min_hold=min_hold)
            signal = candidate.generate_signals(train_prices)
            # Score from the first day the rule could act (after its warm-up), like the skeptic does.
            first = train_prices.index.get_loc(signal.first_valid_index()) + 1
            res = run_backtest(train_prices, signal, start=train_prices.index[first], cash_rate=cash_rate)
            rows.append({"fast": fast, "slow": slow, "band": band, "min_hold": min_hold,
                         "sharpe": result_sharpe(res)})
        table = pd.DataFrame(rows).sort_values("sharpe", ascending=False, ignore_index=True)
        best = table.iloc[0]
        fitted = self.with_params(fast=int(best.fast), slow=int(best.slow),
                                  band=float(best.band), min_hold=int(best.min_hold))
        fitted.search_results = table
        return fitted

    def with_params(self, **changes) -> "OverfitDemo":
        new = super().with_params(**changes)
        new.search_results = self.search_results
        return new

    def sensitivity_grid(self) -> dict:
        # Look at the neighbourhood of whatever was chosen, keeping band/min_hold fixed.
        return {"fast": SEARCH_SPACE["fast"], "slow": SEARCH_SPACE["slow"]}
