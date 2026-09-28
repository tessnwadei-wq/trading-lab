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

# ---- Trade timing (execution) ------------------------------------------------------
# We only have closing prices. A decision made from day t's close can't be traded AT that same close:
# the close is the last price of the day, and by the time you've seen it the market has shut.
# So every trade happens at the NEXT day's close (t+1), and gains or losses count from then on.
#   "next_close"  the default, used everywhere: backtests, portfolio, benchmarks, the Skeptic.
#   "same_close"  the old, slightly optimistic behaviour (trade at the very close you decided on).
#                 Kept ONLY for the "Timing cost" comparison table in each report. Never judge a
#                 strategy with it.
EXECUTION = "next_close"
EXECUTION_MODES = ("next_close", "same_close")

# ---- Assets ------------------------------------------------------------------
TRADED_ASSETS = ["SPY", "XIU.TO"]      # strategies are tested on these
BROAD_INDEX = "SPY"                    # the "broad index" every strategy is compared against
COMPARISON_ASSETS = ["GLD", "IEF", "CAD=X"]  # used in the "How the markets differ" section (GLD, IEF also in portfolios)

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
    "IEF": "iShares 7-10 Year Treasury Bond ETF (US government bonds)",
    "CAD=X": "USD/CAD exchange rate (Canadian dollars per US dollar)",
    "^IRX": "13-week US Treasury bill yield (the cash interest rate)",
}

# ---- Skeptic thresholds --------------------------------------------------------
MIN_TRADES = 30  # fewer trades than this = not enough evidence

# Sample size for ALWAYS-PARTLY-INVESTED strategies (e.g. vol_target), which almost never make a full round trip.
# Pre-registered in strategies/specs/vol_target.md (section 7) before any results: PASS needs at least
# MIN_ACTIVE_REBALANCES "active rebalances" (a weight change of at least ACTIVE_REBALANCE_MIN_CHANGE) over the full
# period AND a test period of at least MIN_TEST_YEARS years. Otherwise NEEDS MORE DATA.
ACTIVE_REBALANCE_MIN_CHANGE = 0.05   # 5 percentage points: smaller changes barely differ from a constant mix
MIN_ACTIVE_REBALANCES = 30           # the same bar as MIN_TRADES
MIN_TEST_YEARS = 5

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
# The lab's portfolio universe. IEF (US 7-10 year Treasury bonds) was added in session 5.
PORTFOLIO_ASSETS = ["SPY", "XIU.TO", "GLD", "IEF"]
# Strategies also run as a multi-asset portfolio, each with its OWN asset list, frozen when the idea was tested.
# Adding an asset to the universe must never quietly change an idea that was already tested, so
# portfolio_ma_trend keeps the three assets it was tested on.
PORTFOLIO_STRATEGIES = {"ma_trend": ["SPY", "XIU.TO", "GLD"],
                        "ts_momentum": ["SPY", "XIU.TO", "GLD", "IEF"]}   # session 5, pre-registered

MAX_RISK_PER_TRADE = 0.01        # a stopped-out trade should normally lose no more than 1% of the account,
                                 # INCLUDING the extra day a stop-sale waits for (see STOP_FILL_BUFFER_MOVES)
# 20% rule, as enforced: no buy may take a position above 20%; anything found above 20% at a close is
# trimmed to 18% at the next close (18%, not 20%, so a rising position isn't trimmed by a sliver, and
# charged costs, every day).
MAX_POSITION_WEIGHT = 0.20
TRIM_BACK_TO = 0.18
# Alert (logged and shown in the report) whenever a position ENDS a day above 22%: the one-day wait for a trim
# should only ever let a position drift a little above 20%, so 22% means something unusual happened.
POSITION_ALERT_WEIGHT = 0.22
MAX_OPEN_POSITIONS = 5
CIRCUIT_BREAKER_DRAWDOWN = 0.10  # after a 10% fall from the peak, open no new trades until a review

# What "until a review" means depends on the mode (see lab/breaker.py):
#  * paper/live mode (future): new trades stay blocked until Tessy runs `python reset_circuit_breaker.py`,
#    which logs who reset it, when, and why. Nothing restarts by itself.
#  * backtest mode: nobody can press "reset" inside a simulation, so we ASSUME the review takes a fixed
#    CIRCUIT_BREAKER_REVIEW_DAYS trading days, after which trading resumes and today's value becomes the
#    new peak. This is an explicit modelling assumption, printed in every portfolio report.
# Why 21: about one calendar month, i.e. "Tessy reviews the lab once a month" (common sense, a normal
# monthly review cadence). It was NOT chosen by looking at results: on 2005-2017 training data the
# portfolio's breaker never triggered, so N could not have been tuned there, and the test period was
# never used to pick it.
CIRCUIT_BREAKER_REVIEW_DAYS = 21
# Hard floor: if the account ever falls 20% below its ALL-TIME high, stop opening trades for good. In a
# backtest there is no restart at all; in paper mode only a manual reset (with a reason) restarts it.
CIRCUIT_BREAKER_HARD_STOP = 0.20

# The exit distance used to measure risk: a protective stop placed STOP_ATR_MULTIPLE times the
# "average daily move" (average absolute daily % change over STOP_ATR_DAYS days) below the entry
# price. 3 x a 20-day average move is a common textbook setting (an ATR stop); it was NOT tuned.
STOP_ATR_DAYS = 20
STOP_ATR_MULTIPLE = 3.0

# ONE-DAY BUFFER for the 1% rule (session 4, Tessy's decision). A stop is only seen at a close and the sale
# fills at the NEXT close, so the price can gap past the stop and keep falling for a day. Positions are sized
# as if the stop were STOP_FILL_BUFFER_MOVES "average daily moves" further away than it really is, so a normal
# stop-out still loses no more than 1% of the account. (The stop itself stays at 3 moves below entry.)
# Why 2: chosen from training data (2005-2017) and common sense, never the test period.
#   * Common sense: on SPY, XIU.TO and GLD a one-day fall bigger than 2 average daily moves happens on only
#     about 7% of days (bigger than 1 move: about 18%).
#   * Training data: of the portfolio's 21 stop-outs in 2005-2017, 81% filled within 2 average daily moves
#     past the stop (67% within 1, 95% within 3). 3 would treat nearly every stop-out as a worst case and
#     make positions much smaller for little gain; 1 leaves one stop-out in three over budget.
# It is a buffer for NORMAL days, not a guarantee: a crash day can still gap through it.
STOP_FILL_BUFFER_MOVES = 2.0
