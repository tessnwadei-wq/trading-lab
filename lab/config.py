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
COMPARISON_ASSETS = ["GLD", "CAD=X"]   # used in the "How the markets differ" section (GLD also in the portfolio)

# ---- Cash interest -------------------------------------------------------------
# Money waiting in cash earns roughly the short-term US Treasury bill rate. We use the
# 13-week T-bill yield (Yahoo ticker ^IRX, saved as data/csv/IRX.csv), quoted in % a year.
# SIMPLIFICATION: we use the US rate for every asset, including the Canadian XIU.TO, where a
# real investor's Canadian-dollar cash would earn the (usually similar) Canadian T-bill rate.
CASH_TICKER = "^IRX"

ASSET_NAMES = {
    "SPY": "S&P 500 ETF (US stocks)",
    "XIU.TO": "iShares S&P/TSX 60 ETF (Canadian stocks)",
    "GLD": "SPDR Gold ETF (gold)",
    "CAD=X": "USD/CAD exchange rate (Canadian dollars per US dollar)",
    "^IRX": "13-week US Treasury bill yield (the cash interest rate)",
}

# ---- Skeptic thresholds --------------------------------------------------------
MIN_TRADES = 30  # fewer trades than this = not enough evidence

# Consistency check: WARN if the test-period Sharpe differs from the training Sharpe by more
# than this, in either direction. Why 0.4: a Sharpe measured over ~8-13 years has a margin of
# error of roughly +/-0.3 each, so two honest measurements of the SAME edge rarely differ by
# more than ~0.4. A bigger gap suggests the period, not a steady edge, drove the result.
CONSISTENCY_MAX_SHARPE_GAP = 0.4

# Stress periods for the regime check: (label, start, end)
REGIMES = [
    ("2008 financial crisis", "2008-01-01", "2008-12-31"),
    ("2020 COVID crash year", "2020-01-01", "2020-12-31"),
    ("2022 rate-hike bear market", "2022-01-01", "2022-12-31"),
]

TRADING_DAYS_PER_YEAR = 252

# ---- Portfolio and risk rules (CLAUDE.md "Risk rules", enforced in lab/portfolio.py) ----
PORTFOLIO_ASSETS = ["SPY", "XIU.TO", "GLD"]
PORTFOLIO_STRATEGIES = ["ma_trend"]       # strategies also run as a multi-asset portfolio

MAX_RISK_PER_TRADE = 0.01        # lose at most 1% of the account if a trade hits its exit
MAX_POSITION_WEIGHT = 0.20       # at most 20% of the account in any one position
TRIM_BACK_TO = 0.18              # a position that grows past 20% is cut back to 18%, not 20%, so a
                                 # rising position isn't trimmed by a sliver (and charged costs) every day
MAX_OPEN_POSITIONS = 5
CIRCUIT_BREAKER_DRAWDOWN = 0.10  # after a 10% fall from the peak, open no new trades...
CIRCUIT_BREAKER_REVIEW_DAYS = 21  # ...for ~1 month (a simulated "review"), then resume from there
# Hard floor: if the account ever falls 20% below its ALL-TIME high, stop opening trades for good (no
# automatic restart). In real life only Tessy could restart it. Added after the risk-manager review.
CIRCUIT_BREAKER_HARD_STOP = 0.20

# The exit distance used to measure risk: a protective stop placed STOP_ATR_MULTIPLE times the
# "average daily move" (average absolute daily % change over STOP_ATR_DAYS days) below the entry
# price. 3 x a 20-day average move is a common textbook setting (an ATR stop); it was NOT tuned.
STOP_ATR_DAYS = 20
STOP_ATR_MULTIPLE = 3.0
