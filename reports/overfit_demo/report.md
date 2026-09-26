# Strategy report: `overfit_demo`

*Generated 2026-09-26 by `python run_lab.py`.*

**Rule:** Fast/slow moving-average crossover with a band and a minimum holding period, all four parameters picked by brute-force search on 2005-2017 data.

**Parameters used:** SPY: `overfit_demo(fast=10, slow=150, band=0.02, min_hold=10)`; XIU.TO: `overfit_demo(fast=50, slow=80, band=0.0, min_hold=40)`

**Overall verdict: FAIL**

| Asset | Verdict | Why |
|---|---|---|
| SPY | **FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| XIU.TO | **FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

**Ground rules applied:** costs of 0.10% commission + 0.05% slippage on every buy and every sell; decisions made at the close and acted on the next trading day; parameters chosen on 2005-2017 only; 2018+ used once as the out-of-sample test.

**Data sources:** SPY: downloaded from Yahoo Finance; XIU.TO: downloaded from Yahoo Finance; GLD: downloaded from Yahoo Finance; CAD=X: downloaded from Yahoo Finance

**Parameter search on SPY (training data only):** tried **1,920 combinations** and kept the best: `overfit_demo(fast=10, slow=150, band=0.02, min_hold=10)`, training Sharpe 0.95. The median combination scored 0.62. Picking the top of 1,920 tries almost guarantees a lucky winner; the question is whether it holds up in 2018+.

**Parameter search on XIU.TO (training data only):** tried **1,920 combinations** and kept the best: `overfit_demo(fast=50, slow=80, band=0.0, min_hold=40)`, training Sharpe 0.91. The median combination scored 0.49. Picking the top of 1,920 tries almost guarantees a lucky winner; the question is whether it holds up in 2018+.

## SPY: S&P 500 ETF (US stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.95 in training (2005-2017) and 0.84 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Costs | ❌ FAIL | Test-period Sharpe after costs 0.84 (double costs 0.80) vs buy-and-hold 0.82 and broad index 0.82. After costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.95; its 8 neighbours: median 0.75, worst 0.55. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 31 trades in total (13 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -14.3% (trough 2023-04-26, took 194 trading days to recover) vs buy-and-hold -55.2%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: +0.0% vs -36.9%; 2020 COVID crash year: +13.4% vs +18.2%; 2022 rate-hike bear market: -12.0% vs -18.3%. No stress period where it was worse on both return and drawdown. |
| 8 | **Verdict** | **❌ FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

### Equity curve

![SPY equity curve](SPY_equity.png)

### Drawdown

![SPY drawdown](SPY_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Time in market |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 9.1% | 0.95 | -9.6% | 9.7% | 19 | 61% | 67% |
| Train 2005-2017 | Strategy (double costs) | 8.6% | 0.90 | -10.1% | 9.7% | 19 | 61% | 67% |
| Train 2005-2017 | Buy-and-hold | 8.7% | 0.53 | -55.2% | 19.1% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 8.7% | 0.53 | -55.2% | 19.1% | 1 | - | 100% |
| Test 2018+ | Strategy | 9.6% | 0.84 | -14.3% | 11.7% | 13 | 50% | 72% |
| Test 2018+ | Strategy (double costs) | 9.1% | 0.80 | -15.1% | 11.7% | 13 | 50% | 72% |
| Test 2018+ | Buy-and-hold | 14.6% | 0.82 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.82 | -33.7% | 19.0% | 1 | - | 100% |
| Full period | Strategy | 9.3% | 0.89 | -14.3% | 10.6% | 31 | 60% | 69% |
| Full period | Strategy (double costs) | 8.8% | 0.85 | -15.1% | 10.6% | 31 | 60% | 69% |
| Full period | Buy-and-hold | 11.1% | 0.65 | -55.2% | 19.1% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.1% | 0.65 | -55.2% | 19.1% | 1 | - | 100% |

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![SPY sensitivity](SPY_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | 0.0% | -36.9% | 0.0% | -47.7% |
| 2020 COVID crash year | 13.4% | 18.2% | -14.3% | -33.7% |
| 2022 rate-hike bear market | -12.0% | -18.3% | -12.3% | -24.5% |

## XIU.TO: iShares S&P/TSX 60 ETF (Canadian stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.91 in training (2005-2017) and 0.62 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Costs | ❌ FAIL | Test-period Sharpe after costs 0.62 (double costs 0.58) vs buy-and-hold 0.84 and broad index 0.82. After costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.91; its 5 neighbours: median 0.74, worst 0.71. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 30 trades in total (13 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -33.0% (trough 2020-06-11, took 655 trading days to recover) vs buy-and-hold -47.9%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: -1.8% vs -31.2%; 2020 COVID crash year: -24.6% vs +5.1%; 2022 rate-hike bear market: +3.0% vs -6.5%. No stress period where it was worse on both return and drawdown. |
| 8 | **Verdict** | **❌ FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

### Equity curve

![XIU.TO equity curve](XIU.TO_equity.png)

### Drawdown

![XIU.TO drawdown](XIU.TO_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Time in market |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 10.3% | 0.91 | -13.8% | 11.5% | 18 | 59% | 71% |
| Train 2005-2017 | Strategy (double costs) | 9.8% | 0.87 | -14.3% | 11.5% | 18 | 59% | 71% |
| Train 2005-2017 | Buy-and-hold | 7.5% | 0.50 | -47.9% | 17.8% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 9.0% | 0.55 | -55.2% | 18.9% | 1 | - | 100% |
| Test 2018+ | Strategy | 7.4% | 0.62 | -33.0% | 13.0% | 13 | 67% | 79% |
| Test 2018+ | Strategy (double costs) | 6.9% | 0.58 | -33.2% | 13.0% | 13 | 58% | 79% |
| Test 2018+ | Buy-and-hold | 12.7% | 0.84 | -35.5% | 15.8% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.82 | -33.7% | 19.0% | 1 | - | 100% |
| Full period | Strategy | 9.1% | 0.78 | -33.0% | 12.1% | 30 | 66% | 74% |
| Full period | Strategy (double costs) | 8.6% | 0.75 | -33.2% | 12.1% | 30 | 62% | 74% |
| Full period | Buy-and-hold | 9.6% | 0.63 | -47.9% | 17.0% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.3% | 0.66 | -55.2% | 19.0% | 1 | - | 100% |

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![XIU.TO sensitivity](XIU.TO_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | -1.8% | -31.2% | -12.3% | -46.9% |
| 2020 COVID crash year | -24.6% | 5.1% | -33.0% | -35.5% |
| 2022 rate-hike bear market | 3.0% | -6.5% | -9.9% | -16.4% |

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
