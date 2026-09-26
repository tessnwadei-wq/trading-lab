# Strategy report: `ma_trend`

> **⚠️ DEMO DATA: these numbers are NOT real market results.**
> Real price downloads were blocked where this report was generated, so the lab ran on
> made-up practice prices (`lab/synthetic.py`). The report shows how the tools work; it says
> nothing about how this strategy performs in real markets. Re-run `python run_lab.py` with
> real data (see README) before drawing any conclusion.


*Generated 2026-09-26 by `python run_lab.py`.*

**Rule:** Hold the asset when price is above its 200-day moving average, otherwise hold cash.

**Parameters used:** SPY: `ma_trend(ma_length=200, band=0.0)`; XIU.TO: `ma_trend(ma_length=200, band=0.0)`

**Overall verdict: FAIL**

| Asset | Verdict | Why |
|---|---|---|
| SPY | **FAIL** | It failed 3 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| XIU.TO | **FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

**Ground rules applied:** costs of 0.10% commission + 0.05% slippage on every buy and every sell; decisions made at the close and acted on the next trading day; parameters chosen on 2005-2017 only; 2018+ used once as the out-of-sample test.

**Data sources:** SPY: SYNTHETIC demo data (not real prices); XIU.TO: SYNTHETIC demo data (not real prices); GLD: SYNTHETIC demo data (not real prices); CAD=X: SYNTHETIC demo data (not real prices)

## SPY: S&P 500 ETF (US stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.26 in training (2005-2017) and 0.60 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Costs | ❌ FAIL | Test-period Sharpe after costs 0.60 (double costs 0.55) vs buy-and-hold 0.68 and broad index 0.68. After costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.26; its 5 neighbours: median 0.22, worst 0.18. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 82 trades in total (26 in the test period). Enough to say something. |
| 6 | Drawdown | ❌ FAIL | Worst fall -51.9% (trough 2020-03-24, took 1295 trading days to recover) vs buy-and-hold -47.1%. Deeper than just holding: more pain, not less. |
| 7 | Regime check | ❌ FAIL | Strategy vs buy-and-hold: 2008 financial crisis: -14.3% vs -12.9%; 2020 COVID crash year: +2.1% vs +33.5%; 2022 rate-hike bear market: -0.7% vs -30.7%. Worse on both return AND drawdown in: 2020 COVID crash year. |
| 8 | **Verdict** | **❌ FAIL** | It failed 3 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

### Equity curve

![SPY equity curve](SPY_equity.png)

### Drawdown

![SPY drawdown](SPY_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Time in market |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 3.0% | 0.26 | -39.5% | 15.8% | 57 | 16% | 64% |
| Train 2005-2017 | Strategy (double costs) | 1.6% | 0.18 | -44.5% | 15.9% | 57 | 16% | 64% |
| Train 2005-2017 | Buy-and-hold | 8.7% | 0.49 | -35.7% | 20.9% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 8.7% | 0.49 | -35.7% | 20.9% | 1 | - | 100% |
| Test 2018+ | Strategy | 9.0% | 0.60 | -31.7% | 16.0% | 26 | 20% | 69% |
| Test 2018+ | Strategy (double costs) | 8.0% | 0.55 | -32.2% | 16.0% | 26 | 20% | 69% |
| Test 2018+ | Buy-and-hold | 13.3% | 0.68 | -47.1% | 20.8% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 13.3% | 0.68 | -47.1% | 20.8% | 1 | - | 100% |
| Full period | Strategy | 5.5% | 0.40 | -51.9% | 15.9% | 82 | 19% | 66% |
| Full period | Strategy (double costs) | 4.3% | 0.33 | -58.7% | 15.9% | 82 | 17% | 66% |
| Full period | Buy-and-hold | 10.6% | 0.57 | -47.1% | 20.9% | 1 | - | 100% |
| Full period | Broad index (SPY) | 10.6% | 0.57 | -47.1% | 20.9% | 1 | - | 100% |

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![SPY sensitivity](SPY_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | -14.3% | -12.9% | -23.3% | -35.7% |
| 2020 COVID crash year | 2.1% | 33.5% | -31.7% | -26.7% |
| 2022 rate-hike bear market | -0.7% | -30.7% | -7.4% | -42.6% |

## XIU.TO: iShares S&P/TSX 60 ETF (Canadian stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.36 in training (2005-2017) and 0.67 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Costs | ❌ FAIL | Test-period Sharpe after costs 0.67 (double costs 0.61) vs buy-and-hold 0.33 and broad index 0.68. After costs it does not beat simply buying and holding, so it isn't earning its complexity. |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.36; its 5 neighbours: median 0.42, worst 0.30. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 85 trades in total (24 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -50.3% (trough 2019-06-25, took 1156 trading days to recover) vs buy-and-hold -51.9%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: -5.6% vs -41.8%; 2020 COVID crash year: +2.8% vs -6.8%; 2022 rate-hike bear market: -3.2% vs -40.7%. No stress period where it was worse on both return and drawdown. |
| 8 | **Verdict** | **❌ FAIL** | It failed 1 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity. |

### Equity curve

![XIU.TO equity curve](XIU.TO_equity.png)

### Drawdown

![XIU.TO drawdown](XIU.TO_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Time in market |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 4.2% | 0.36 | -44.6% | 13.8% | 61 | 11% | 56% |
| Train 2005-2017 | Strategy (double costs) | 2.6% | 0.25 | -51.9% | 13.8% | 61 | 11% | 56% |
| Train 2005-2017 | Buy-and-hold | 7.0% | 0.44 | -51.9% | 19.2% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 8.7% | 0.49 | -35.7% | 20.9% | 1 | - | 100% |
| Test 2018+ | Strategy | 8.2% | 0.67 | -21.4% | 12.4% | 24 | 22% | 62% |
| Test 2018+ | Strategy (double costs) | 7.3% | 0.61 | -22.8% | 12.4% | 24 | 22% | 62% |
| Test 2018+ | Buy-and-hold | 4.8% | 0.33 | -46.6% | 19.1% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 13.3% | 0.68 | -47.1% | 20.8% | 1 | - | 100% |
| Full period | Strategy | 5.8% | 0.48 | -50.3% | 13.2% | 85 | 14% | 59% |
| Full period | Strategy (double costs) | 4.5% | 0.39 | -57.7% | 13.3% | 85 | 14% | 59% |
| Full period | Buy-and-hold | 6.1% | 0.39 | -51.9% | 19.1% | 1 | - | 100% |
| Full period | Broad index (SPY) | 10.6% | 0.57 | -47.1% | 20.9% | 1 | - | 100% |

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![XIU.TO sensitivity](XIU.TO_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | -5.6% | -41.8% | -19.6% | -50.4% |
| 2020 COVID crash year | 2.8% | -6.8% | -12.4% | -41.9% |
| 2022 rate-hike bear market | -3.2% | -40.7% | -3.2% | -43.6% |

## How the markets differ

The lab will eventually trade more than stocks, so here is how four very different markets behaved over the same years. Nothing here is traded yet.

| Market | Average yearly return | Best year | Worst year | Worst drawdown | Moves with SPY (correlation) |
|---|---:|---:|---:|---:|---:|
| SPY: S&P 500 ETF (US stocks) | 12.5% | 39.0% (2009) | -30.6% (2022) | -47.1% | +1.00 |
| XIU.TO: iShares S&P/TSX 60 ETF (Canadian stocks) | 10.7% | 86.1% (2009) | -41.7% (2008) | -51.9% | +0.73 |
| GLD: SPDR Gold ETF (gold) | 7.8% | 32.8% (2009) | -27.9% (2018) | -50.1% | +0.05 |
| CAD=X: USD/CAD exchange rate (Canadian dollars per US dollar) | -0.6% | 14.5% (2008) | -26.7% (2010) | -43.3% | -0.46 |

<details><summary>Year-by-year returns (click to open)</summary>

| Year | SPY | XIU.TO | GLD | CAD=X |
|---|---:|---:|---:|---:|
| 2006 | -7.2% | 11.3% | 21.7% | -2.3% |
| 2007 | 38.2% | 31.2% | 15.9% | -4.0% |
| 2008 | -12.8% | -41.7% | -2.0% | 14.5% |
| 2009 | 39.0% | 86.1% | 32.8% | -6.5% |
| 2010 | 34.3% | 77.5% | 17.2% | -26.7% |
| 2011 | 14.7% | -12.3% | 24.5% | 9.8% |
| 2012 | 9.1% | -1.4% | 5.3% | 5.8% |
| 2013 | 2.8% | -9.1% | -15.7% | -1.6% |
| 2014 | 8.5% | 20.9% | 11.4% | -19.9% |
| 2015 | 17.3% | 9.5% | 9.3% | 1.5% |
| 2016 | -13.5% | -11.2% | 25.1% | 8.7% |
| 2017 | 0.6% | -4.7% | 6.9% | 10.8% |
| 2018 | 16.5% | 0.5% | -27.9% | 9.8% |
| 2019 | 26.7% | 14.8% | -14.1% | -8.1% |
| 2020 | 33.7% | -6.6% | 8.3% | -3.3% |
| 2021 | 8.7% | 15.2% | 11.7% | 2.8% |
| 2022 | -30.6% | -40.6% | -10.4% | 11.4% |
| 2023 | 20.9% | 55.7% | 19.0% | -4.0% |
| 2024 | 11.4% | -1.4% | 2.8% | 3.7% |
| 2025 | 12.1% | 13.0% | -1.6% | -12.1% |
| 2026 | 32.3% | 17.7% | 23.1% | -1.9% |

</details>

**Reading this in plain English:**

- **Correlation** runs from -1 to +1. +1 means "always moves the same way as SPY", 0 means "no relationship", -1 means "always moves the opposite way". Something with low or negative correlation can cushion a stock portfolio when stocks fall.
- **Canadian vs US stocks** (XIU.TO vs SPY, correlation +0.73): they tend to rise and fall together, so holding both diversifies less than it seems.
- **Gold** (GLD, correlation +0.05): largely goes its own way. It's a commodity with no earnings or dividends; people buy it as a store of value, often when they're worried.
- **USD/CAD** (CAD=X, correlation -0.46): this is a *price of a currency*, not an investment that grows. When it goes UP, one US dollar buys more Canadian dollars (the CAD got weaker). It usually moves much less than stocks, which is why forex traders often use leverage (borrowed money), and that's where forex gets dangerous.
- **Worst drawdown** is the biggest peak-to-bottom fall. It's the number that tells you how much pain you'd have had to sit through.


---
*How to read the numbers: see [LEARNING.md](../../LEARNING.md).*
