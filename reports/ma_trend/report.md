# Strategy report: `ma_trend`

*Generated 2026-09-26 by `python run_lab.py`.*

**Rule:** Hold the asset when price is above its 200-day moving average, otherwise hold cash.

**Parameters used:** SPY: `ma_trend(ma_length=200, band=0.0)`; XIU.TO: `ma_trend(ma_length=200, band=0.0)`

**Overall verdict: FAIL**

| Asset | Verdict | Why |
|---|---|---|
| SPY | **FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| XIU.TO | **FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

**Ground rules applied:** costs of 0.10% commission + 0.05% slippage on every buy and every sell; decisions made at the close and acted on the next trading day; parameters chosen on 2005-2017 only; 2018+ used once as the out-of-sample test.

**Data sources:** SPY: downloaded from Yahoo Finance; XIU.TO: downloaded from Yahoo Finance; GLD: downloaded from Yahoo Finance; CAD=X: downloaded from Yahoo Finance

## SPY: S&P 500 ETF (US stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.63 in training (2005-2017) and 0.82 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Costs | ❌ FAIL | Test-period Sharpe after costs 0.82 (double costs 0.74) vs buy-and-hold 0.82 and broad index 0.82. After costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.63; its 5 neighbours: median 0.62, worst 0.59. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 63 trades in total (26 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -23.2% (trough 2009-07-10, took 123 trading days to recover) vs buy-and-hold -55.2%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: -4.5% vs -36.9%; 2020 COVID crash year: +8.7% vs +18.2%; 2022 rate-hike bear market: -16.9% vs -18.3%. No stress period where it was worse on both return and drawdown. |
| 8 | **Verdict** | **❌ FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

### Equity curve

![SPY equity curve](SPY_equity.png)

### Drawdown

![SPY drawdown](SPY_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Time in market |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 6.6% | 0.63 | -23.2% | 11.0% | 38 | 22% | 78% |
| Train 2005-2017 | Strategy (double costs) | 5.6% | 0.55 | -25.7% | 11.0% | 38 | 22% | 78% |
| Train 2005-2017 | Buy-and-hold | 9.0% | 0.55 | -55.2% | 19.2% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 9.0% | 0.55 | -55.2% | 19.2% | 1 | - | 100% |
| Test 2018+ | Strategy | 9.9% | 0.82 | -22.4% | 12.5% | 26 | 28% | 82% |
| Test 2018+ | Strategy (double costs) | 8.9% | 0.74 | -24.9% | 12.6% | 26 | 28% | 82% |
| Test 2018+ | Buy-and-hold | 14.6% | 0.82 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.82 | -33.7% | 19.0% | 1 | - | 100% |
| Full period | Strategy | 7.9% | 0.72 | -23.2% | 11.6% | 63 | 24% | 80% |
| Full period | Strategy (double costs) | 7.0% | 0.64 | -25.7% | 11.7% | 63 | 24% | 80% |
| Full period | Buy-and-hold | 11.3% | 0.66 | -55.2% | 19.1% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.3% | 0.66 | -55.2% | 19.1% | 1 | - | 100% |

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![SPY sensitivity](SPY_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | -4.5% | -36.9% | -4.5% | -47.7% |
| 2020 COVID crash year | 8.7% | 18.2% | -18.1% | -33.7% |
| 2022 rate-hike bear market | -16.9% | -18.3% | -17.3% | -24.5% |

## XIU.TO: iShares S&P/TSX 60 ETF (Canadian stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.25 in training (2005-2017) and 0.91 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Costs | ❌ FAIL | Test-period Sharpe after costs 0.91 (double costs 0.81) vs buy-and-hold 0.84 and broad index 0.82. After costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.25; its 5 neighbours: median 0.32, worst 0.26. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 89 trades in total (27 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -27.0% (trough 2016-04-05, took 1227 trading days to recover) vs buy-and-hold -47.9%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: -12.7% vs -31.2%; 2020 COVID crash year: +0.4% vs +5.1%; 2022 rate-hike bear market: -8.9% vs -6.5%. No stress period where it was worse on both return and drawdown. |
| 8 | **Verdict** | **❌ FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

### Equity curve

![XIU.TO equity curve](XIU.TO_equity.png)

### Drawdown

![XIU.TO drawdown](XIU.TO_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Time in market |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 2.1% | 0.25 | -27.0% | 11.0% | 63 | 18% | 74% |
| Train 2005-2017 | Strategy (double costs) | 0.6% | 0.11 | -37.9% | 11.1% | 63 | 18% | 74% |
| Train 2005-2017 | Buy-and-hold | 6.8% | 0.46 | -47.9% | 18.0% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 9.1% | 0.55 | -55.2% | 19.2% | 1 | - | 100% |
| Test 2018+ | Strategy | 8.8% | 0.91 | -18.0% | 9.8% | 27 | 23% | 82% |
| Test 2018+ | Strategy (double costs) | 7.8% | 0.81 | -21.1% | 9.9% | 27 | 15% | 82% |
| Test 2018+ | Buy-and-hold | 12.7% | 0.84 | -35.5% | 15.8% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.82 | -33.7% | 19.0% | 1 | - | 100% |
| Full period | Strategy | 4.9% | 0.50 | -27.0% | 10.6% | 89 | 20% | 77% |
| Full period | Strategy (double costs) | 3.5% | 0.38 | -37.9% | 10.6% | 89 | 18% | 77% |
| Full period | Buy-and-hold | 9.2% | 0.60 | -47.9% | 17.1% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.4% | 0.66 | -55.2% | 19.1% | 1 | - | 100% |

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![XIU.TO sensitivity](XIU.TO_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | -12.7% | -31.2% | -19.6% | -46.9% |
| 2020 COVID crash year | 0.4% | 5.1% | -14.3% | -35.5% |
| 2022 rate-hike bear market | -8.9% | -6.5% | -12.7% | -16.4% |

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
