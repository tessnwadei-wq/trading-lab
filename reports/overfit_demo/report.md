# Strategy report: `overfit_demo`

*Generated 2026-09-26 by `python run_lab.py`.*

**Rule:** Fast/slow moving-average crossover with a band and a minimum holding period, all four parameters picked by brute-force search on 2005-2017 data.

**Parameters used:** SPY: `overfit_demo(fast=10, slow=150, band=0.02, min_hold=10)`; XIU.TO: `overfit_demo(fast=50, slow=80, band=0.0, min_hold=40)`

**Overall verdict: FAIL**

| Tested on | Verdict | Why |
|---|---|---|
| SPY | **FAIL** | It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.675 vs 0.677, short by 0.002); the broad index (SPY) at normal costs (Sharpe 0.675 vs 0.677, short by 0.002); buy-and-hold at double costs (Sharpe 0.64 vs 0.68, short by 0.04); the broad index (SPY) at double costs (Sharpe 0.64 vs 0.68, short by 0.04). |
| XIU.TO | **FAIL** | It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.45 vs 0.67, short by 0.21); the broad index (SPY) at normal costs (Sharpe 0.45 vs 0.68, short by 0.22); the same-risk mix at normal costs (yearly return 8.0% vs 9.2%, short by 1.3 percentage points a year); buy-and-hold at double costs (Sharpe 0.42 vs 0.67, short by 0.25); the broad index (SPY) at double costs (Sharpe 0.42 vs 0.68, short by 0.26); the same-risk mix at double costs (yearly return 7.5% vs 9.2%, short by 1.7 percentage points a year). |

**Ground rules applied:** costs of 0.10% commission + 0.05% slippage on every buy and every sell; decisions made at the close from that day's data, with gains and losses counted from the next day; parameters chosen on 2005-2017 only; 2018+ used once as the out-of-sample test. Money in cash earns the 13-week US T-bill rate (^IRX), used for every asset including XIU.TO (a simplification), and Sharpe ratios measure return *above* that cash rate.

**Data sources:** SPY: data/csv/SPY.csv; XIU.TO: data/csv/XIU_TO.csv; GLD: data/csv/GLD.csv; CAD=X: data/csv/CAD_X.csv; ^IRX: data/csv/IRX.csv

**Parameter search on SPY (training data only):** tried **1,920 combinations** and kept the best: `overfit_demo(fast=10, slow=150, band=0.02, min_hold=10)`, training Sharpe 0.87. The median combination scored 0.56. Picking the top of 1,920 tries almost guarantees a lucky winner; the question is whether it holds up in 2018+.

**Parameter search on XIU.TO (training data only):** tried **1,920 combinations** and kept the best: `overfit_demo(fast=50, slow=80, band=0.0, min_hold=40)`, training Sharpe 0.83. The median combination scored 0.41. Picking the top of 1,920 tries almost guarantees a lucky winner; the question is whether it holds up in 2018+.

## SPY: S&P 500 ETF (US stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.87 in training (2005-2017) and 0.68 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Beats the simple alternatives | ❌ FAIL | Beat the same-risk mix at normal costs (yearly return 10.3% vs 8.9%); the same-risk mix at double costs (yearly return 9.8% vs 8.9%). But fell short of buy-and-hold at normal costs (Sharpe 0.675 vs 0.677, short by 0.002); the broad index (SPY) at normal costs (Sharpe 0.675 vs 0.677, short by 0.002); buy-and-hold at double costs (Sharpe 0.64 vs 0.68, short by 0.04); the broad index (SPY) at double costs (Sharpe 0.64 vs 0.68, short by 0.04). (Same-risk mix = 51% in SPY + 49% in cash, sized on 2005-2017 data.) |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.87; its 8 neighbours: median 0.67, worst 0.48. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 31 trades in total (13 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -14.2% (trough 2020-06-11, took 55 trading days to recover) vs buy-and-hold -55.2%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: +1.4% vs -36.9%; 2020 COVID crash year: +13.4% vs +18.2%; 2022 rate-hike bear market: -10.4% vs -18.3%. No stress period where it was worse on both return and drawdown. |
| 8 | Consistency | ✅ PASS | Sharpe went from 0.87 (training) to 0.68 (test), a change of -0.20, within the ±0.4 expected from normal ups and downs. Behaviour was steady. |
| 9 | **Verdict** | **❌ FAIL** | It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.675 vs 0.677, short by 0.002); the broad index (SPY) at normal costs (Sharpe 0.675 vs 0.677, short by 0.002); buy-and-hold at double costs (Sharpe 0.64 vs 0.68, short by 0.04); the broad index (SPY) at double costs (Sharpe 0.64 vs 0.68, short by 0.04). |

**Same-risk mix:** 51% in SPY and 49% in cash earning interest, rebalanced monthly. 51% was chosen so its bumpiness (volatility) matched the strategy's **on 2005-2017 data only**, then frozen for 2018+. In the test period its volatility was 9.5% vs the strategy's 11.7%. If the strategy can't earn more than this simple mix, it is just a complicated way of owning less of the asset.

### Equity curve

![SPY equity curve](SPY_equity.png)

### Drawdown

![SPY drawdown](SPY_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Avg. share invested |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 9.5% | 0.87 | -9.1% | 9.7% | 19 | 61% | 67% |
| Train 2005-2017 | Strategy (double costs) | 9.0% | 0.82 | -9.7% | 9.7% | 19 | 61% | 67% |
| Train 2005-2017 | Buy-and-hold | 8.7% | 0.47 | -55.2% | 19.1% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 8.7% | 0.47 | -55.2% | 19.1% | 1 | - | 100% |
| Train 2005-2017 | Same-risk mix (51% in, 49% cash) | 5.1% | 0.46 | -32.1% | 9.5% | 1 | - | 51% |
| Test 2018+ | Strategy | 10.3% | 0.68 | -14.2% | 11.7% | 13 | 50% | 72% |
| Test 2018+ | Strategy (double costs) | 9.8% | 0.64 | -14.5% | 11.7% | 13 | 50% | 72% |
| Test 2018+ | Buy-and-hold | 14.6% | 0.68 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.68 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Same-risk mix (51% in, 49% cash) | 8.9% | 0.67 | -18.0% | 9.5% | 1 | - | 51% |
| Full period | Strategy | 9.9% | 0.78 | -14.2% | 10.6% | 31 | 60% | 69% |
| Full period | Strategy (double costs) | 9.4% | 0.74 | -14.5% | 10.6% | 31 | 60% | 69% |
| Full period | Buy-and-hold | 11.1% | 0.56 | -55.2% | 19.1% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.1% | 0.56 | -55.2% | 19.1% | 1 | - | 100% |
| Full period | Same-risk mix (51% in, 49% cash) | 6.7% | 0.55 | -32.1% | 9.5% | 1 | - | 51% |

*Sharpe = return above the cash rate, per unit of volatility. Avg. share invested = how much of the account was in the market on an average day.*

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![SPY sensitivity](SPY_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | 1.4% | -36.9% | 0.0% | -47.7% |
| 2020 COVID crash year | 13.4% | 18.2% | -14.2% | -33.7% |
| 2022 rate-hike bear market | -10.4% | -18.3% | -10.9% | -24.5% |

## XIU.TO: iShares S&P/TSX 60 ETF (Canadian stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.83 in training (2005-2017) and 0.45 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Beats the simple alternatives | ❌ FAIL | Fell short of buy-and-hold at normal costs (Sharpe 0.45 vs 0.67, short by 0.21); the broad index (SPY) at normal costs (Sharpe 0.45 vs 0.68, short by 0.22); the same-risk mix at normal costs (yearly return 8.0% vs 9.2%, short by 1.3 percentage points a year); buy-and-hold at double costs (Sharpe 0.42 vs 0.67, short by 0.25); the broad index (SPY) at double costs (Sharpe 0.42 vs 0.68, short by 0.26); the same-risk mix at double costs (yearly return 7.5% vs 9.2%, short by 1.7 percentage points a year). (Same-risk mix = 65% in XIU.TO + 35% in cash, sized on 2005-2017 data.) |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.83; its 5 neighbours: median 0.66, worst 0.62. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 30 trades in total (13 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -33.0% (trough 2020-06-11, took 649 trading days to recover) vs buy-and-hold -47.9%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: -1.0% vs -31.2%; 2020 COVID crash year: -24.6% vs +5.1%; 2022 rate-hike bear market: +4.0% vs -6.5%. No stress period where it was worse on both return and drawdown. |
| 8 | Consistency | ✅ PASS | Sharpe went from 0.83 (training) to 0.45 (test), a change of -0.38, within the ±0.4 expected from normal ups and downs. Behaviour was steady. |
| 9 | **Verdict** | **❌ FAIL** | It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.45 vs 0.67, short by 0.21); the broad index (SPY) at normal costs (Sharpe 0.45 vs 0.68, short by 0.22); the same-risk mix at normal costs (yearly return 8.0% vs 9.2%, short by 1.3 percentage points a year); buy-and-hold at double costs (Sharpe 0.42 vs 0.67, short by 0.25); the broad index (SPY) at double costs (Sharpe 0.42 vs 0.68, short by 0.26); the same-risk mix at double costs (yearly return 7.5% vs 9.2%, short by 1.7 percentage points a year). |

**Same-risk mix:** 65% in XIU.TO and 35% in cash earning interest, rebalanced monthly. 65% was chosen so its bumpiness (volatility) matched the strategy's **on 2005-2017 data only**, then frozen for 2018+. In the test period its volatility was 9.9% vs the strategy's 13.0%. If the strategy can't earn more than this simple mix, it is just a complicated way of owning less of the asset.

### Equity curve

![XIU.TO equity curve](XIU.TO_equity.png)

### Drawdown

![XIU.TO drawdown](XIU.TO_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Avg. share invested |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 10.5% | 0.83 | -13.8% | 11.5% | 18 | 59% | 71% |
| Train 2005-2017 | Strategy (double costs) | 10.1% | 0.80 | -14.3% | 11.5% | 18 | 59% | 71% |
| Train 2005-2017 | Buy-and-hold | 7.5% | 0.43 | -47.9% | 17.8% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 9.0% | 0.49 | -55.2% | 18.9% | 1 | - | 100% |
| Train 2005-2017 | Same-risk mix (65% in, 35% cash) | 5.4% | 0.42 | -33.7% | 11.3% | 1 | - | 65% |
| Test 2018+ | Strategy | 8.0% | 0.45 | -33.0% | 13.0% | 13 | 67% | 79% |
| Test 2018+ | Strategy (double costs) | 7.5% | 0.42 | -33.2% | 13.0% | 13 | 58% | 79% |
| Test 2018+ | Buy-and-hold | 12.7% | 0.67 | -35.5% | 15.8% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.68 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Same-risk mix (65% in, 35% cash) | 9.2% | 0.68 | -23.5% | 9.9% | 1 | - | 65% |
| Full period | Strategy | 9.5% | 0.67 | -33.0% | 12.1% | 30 | 66% | 74% |
| Full period | Strategy (double costs) | 9.0% | 0.63 | -33.2% | 12.1% | 30 | 62% | 74% |
| Full period | Buy-and-hold | 9.6% | 0.52 | -47.9% | 17.0% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.3% | 0.57 | -55.2% | 19.0% | 1 | - | 100% |
| Full period | Same-risk mix (65% in, 35% cash) | 7.0% | 0.52 | -33.7% | 10.8% | 1 | - | 65% |

*Sharpe = return above the cash rate, per unit of volatility. Avg. share invested = how much of the account was in the market on an average day.*

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![XIU.TO sensitivity](XIU.TO_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | -1.0% | -31.2% | -12.3% | -46.9% |
| 2020 COVID crash year | -24.6% | 5.1% | -33.0% | -35.5% |
| 2022 rate-hike bear market | 4.0% | -6.5% | -9.9% | -16.4% |

## Over-search counter

The more things you try, the more likely your best result is luck. The lab counts every parameter combination and idea ever tested on real data in [`journal/trials.csv`](../../journal/trials.csv).

**Lab-wide so far:** 3 ideas, 3,843 parameter combinations tested.

| Tested on | Tries for this idea | Training Sharpe | Luck bar (this idea) | Rough chance it's real | Luck bar (whole lab) |
|---|---:|---:|---:|---:|---:|
| SPY | 1,920 | 0.87 | 0.98 | 36% | 1.03 |
| XIU.TO | 1,920 | 0.83 | 0.97 | 32% | 1.02 |

**Reading this:** the *luck bar* is the Sharpe ratio the luckiest of that many *useless* strategies would be expected to show over the training years, by chance alone. A result below its bar is what luck alone would produce. *Rough chance it's real* compares the training Sharpe with the bar (a simplified "deflated Sharpe ratio"; see LEARNING.md). The whole-lab bar is stricter: it asks "if this were the best of everything the lab ever tried, would it stand out?"


## How the markets differ

The lab will eventually trade more than stocks, so here is how four very different markets behaved over the same years. Nothing here is traded yet.

| Market | Average yearly return | Best year | Worst year | Worst drawdown | Moves with SPY (correlation) |
|---|---:|---:|---:|---:|---:|
| SPY: S&P 500 ETF (US stocks) | 12.5% | 32.3% (2013) | -36.8% (2008) | -55.2% | +1.00 |
| XIU.TO: iShares S&P/TSX 60 ETF (Canadian stocks) | 9.9% | 31.4% (2009) | -31.1% (2008) | -47.9% | +0.80 |
| GLD: SPDR Gold ETF (gold) | 11.7% | 63.7% (2025) | -28.3% (2013) | -45.6% | +0.07 |
| CAD=X: USD/CAD exchange rate (Canadian dollars per US dollar) | 1.3% | 21.9% (2008) | -14.3% (2007) | -27.6% | -0.24 |

<details><summary>Year-by-year returns (click to open)</summary>

| Year | SPY | XIU.TO | GLD | CAD=X |
|---|---:|---:|---:|---:|
| 2006 | 15.8% | 19.1% | 22.5% | 0.3% |
| 2007 | 5.1% | 10.8% | 30.5% | -14.3% |
| 2008 | -36.8% | -31.1% | 4.9% | 21.9% |
| 2009 | 26.4% | 31.4% | 24.0% | -13.5% |
| 2010 | 15.1% | 13.9% | 29.3% | -5.0% |
| 2011 | 1.9% | -9.3% | 9.6% | 2.1% |
| 2012 | 16.0% | 7.9% | 6.6% | -2.5% |
| 2013 | 32.3% | 13.1% | -28.3% | 7.0% |
| 2014 | 13.5% | 11.9% | -2.2% | 9.0% |
| 2015 | 1.2% | -7.8% | -10.7% | 19.5% |
| 2016 | 12.0% | 20.3% | 8.0% | -2.8% |
| 2017 | 21.7% | 9.6% | 12.8% | -6.8% |
| 2018 | -4.6% | -7.8% | -1.9% | 8.4% |
| 2019 | 31.2% | 21.8% | 17.9% | -4.1% |
| 2020 | 18.3% | 5.3% | 24.8% | -2.4% |
| 2021 | 28.7% | 28.1% | -4.1% | -0.0% |
| 2022 | -18.2% | -6.3% | -0.8% | 6.3% |
| 2023 | 26.2% | 11.9% | 12.7% | -2.4% |
| 2024 | 24.9% | 20.7% | 26.7% | 8.5% |
| 2025 | 17.7% | 28.9% | 63.7% | -4.6% |
| 2026 | 14.0% | 14.8% | -0.7% | 3.3% |

</details>

**Reading this in plain English:**

- **Correlation** runs from -1 to +1. +1 means "always moves the same way as SPY", 0 means "no relationship", -1 means "always moves the opposite way". Something with low or negative correlation can cushion a stock portfolio when stocks fall.
- **Canadian vs US stocks** (XIU.TO vs SPY, correlation +0.80): they tend to rise and fall together, so holding both diversifies less than it seems.
- **Gold** (GLD, correlation +0.07): largely goes its own way. It's a commodity with no earnings or dividends; people buy it as a store of value, often when they're worried.
- **USD/CAD** (CAD=X, correlation -0.24): this is a *price of a currency*, not an investment that grows. When it goes UP, one US dollar buys more Canadian dollars (the CAD got weaker). It usually moves much less than stocks, which is why forex traders often use leverage (borrowed money), and that's where forex gets dangerous.
- **Worst drawdown** is the biggest peak-to-bottom fall. It's the number that tells you how much pain you'd have had to sit through.


---
*How to read the numbers: see [LEARNING.md](../../LEARNING.md).*
