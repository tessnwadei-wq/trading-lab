"""
One place for the lab's ground rules, so every script uses the same numbers.

If you change something here, it changes for every strategy. That is on purpose:
it stops us quietly giving one strategy cheaper costs or a friendlier date range.
"""

import pandas as pd

# ---- Dates -----------------------------------------------------------------
START_DATE = "2005-01-01"

# Everything up to and including TRAIN_END is the "training" period. We are allowed to
# look at it as often as we like and to choose parameters on it.
TRAIN_END = pd.Timestamp("2017-12-31")

# Everything from TEST_START onward is the "out-of-sample test" period. We look at it
# ONCE per idea, after all choices are frozen. Peeking and re-tuning would make it useless.
TEST_START = pd.Timestamp("2018-01-01")

# ---- Trading costs -----------------------------------------------------------
# Charged every time we buy or sell, as a fraction of the amount traded.
COMMISSION = 0.0010  # 0.10% broker fee / spread
SLIPPAGE = 0.0005    # 0.05% "we got a slightly worse price than the chart shows"
COST_PER_TRADE = COMMISSION + SLIPPAGE  # 0.15% each way

# ---- Assets ------------------------------------------------------------------
TRADED_ASSETS = ["SPY", "XIU.TO"]      # strategies are tested on these
BROAD_INDEX = "SPY"                    # the "broad index" every strategy is compared against
COMPARISON_ASSETS = ["GLD", "CAD=X"]   # downloaded for the "How the markets differ" section only

ASSET_NAMES = {
    "SPY": "S&P 500 ETF (US stocks)",
    "XIU.TO": "iShares S&P/TSX 60 ETF (Canadian stocks)",
    "GLD": "SPDR Gold ETF (gold)",
    "CAD=X": "USD/CAD exchange rate (Canadian dollars per US dollar)",
}

# ---- Skeptic thresholds --------------------------------------------------------
MIN_TRADES = 30  # fewer trades than this = not enough evidence

# Stress periods for the regime check: (label, start, end)
REGIMES = [
    ("2008 financial crisis", "2008-01-01", "2008-12-31"),
    ("2020 COVID crash year", "2020-01-01", "2020-12-31"),
    ("2022 rate-hike bear market", "2022-01-01", "2022-12-31"),
]

TRADING_DAYS_PER_YEAR = 252
