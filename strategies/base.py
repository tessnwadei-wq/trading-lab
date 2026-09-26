"""
The simple interface every strategy follows.

A strategy is just:
  * a name,
  * some parameters (the numbers in its rules, e.g. "200" in "200-day average"),
  * a function that looks at prices and says, for each day, 1 = invested or 0 = cash.

Rule for every strategy: the value for day t may only use prices up to and including
day t. The backtester waits one day before acting, so strategies must NOT shift signals
themselves. tests/test_lookahead.py checks this automatically for every strategy.
"""

from __future__ import annotations

import pandas as pd


class Strategy:
    name: str = "base"
    description: str = ""

    def __init__(self, **params):
        # Start from the class defaults, then apply anything passed in.
        self.params = {**self.default_params(), **params}

    @classmethod
    def default_params(cls) -> dict:
        return {}

    def with_params(self, **changes) -> "Strategy":
        """A copy of this strategy with some parameters changed (used for sensitivity tests)."""
        return type(self)(**{**self.params, **changes})

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        """Return a Series of 0/1 (NaN during warm-up), one value per day in `prices`."""
        raise NotImplementedError

    def sensitivity_grid(self) -> dict:
        """
        Two parameters and a list of nearby values for each, e.g.
        {"ma_length": [150, 175, 200, 225, 250], "band": [0, 0.01, 0.02]}.
        The skeptic re-runs the strategy on every combination to look for "magic numbers".
        """
        return {}

    def fit(self, train_prices: pd.DataFrame) -> "Strategy":
        """
        Optional: choose parameters using TRAINING data only. Most strategies don't need
        this and just return themselves. overfit_demo.py uses it to show what not to do.
        """
        return self

    def label(self) -> str:
        return f"{self.name}(" + ", ".join(f"{k}={v}" for k, v in self.params.items()) + ")"
