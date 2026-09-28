# Strategy report: `overfit_demo`

*Generated 2026-09-28 by `python run_lab.py`.*

**Rule:** Fast/slow moving-average crossover with a band and a minimum holding period, all four parameters picked by brute-force search on 2005-2017 data.

**Parameters used:** SPY: `overfit_demo(fast=40, slow=210, band=0.03, min_hold=5)`; XIU.TO: `overfit_demo(fast=10, slow=80, band=0.0, min_hold=40)`

**Overall verdict: FAIL**

| Tested on | Verdict | Why |
|---|---|---|
| SPY | **FAIL** | It failed 2 of 8 checks. Main problem (out-of-sample): test Sharpe 0.26 vs training 0.86. Warning: consistency (Sharpe dropped 0.86 → 0.26). |
| XIU.TO | **FAIL** | It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.60 vs 0.67, short by 0.07); the broad index (SPY) at normal costs (Sharpe 0.60 vs 0.68, short by 0.08); the same-risk mix at normal costs (yearly return 8.6% vs 9.0%, short by 0.4 percentage points a year); the equal-risk mix at normal costs (yearly return 8.6% vs 9.5%, short by 0.9 percentage points a year); buy-and-hold at double costs (Sharpe 0.54 vs 0.67, short by 0.13); the broad index (SPY) at double costs (Sharpe 0.54 vs 0.68, short by 0.13); the same-risk mix at double costs (yearly return 8.0% vs 9.0%, short by 1.0 percentage points a year); the equal-risk mix at double costs (yearly return 8.0% vs 9.5%, short by 1.5 percentage points a year). |

**Test-period (2018+) looks for this idea: 4** (this report included; details in *Test-period looks* below).

**Ground rules applied:** costs of 0.10% commission + 0.05% slippage on every buy and every sell; each decision is made from a day's closing price and **traded at the next day's close** (so gains and losses start the day after that); parameters chosen on 2005-2017 only; 2018+ used once as the out-of-sample test. Money in cash earns the 13-week US T-bill rate (^IRX), used for every asset including XIU.TO (a simplification), and Sharpe ratios measure return *above* that cash rate.

**Data sources:** SPY: data/csv/SPY.csv; XIU.TO: data/csv/XIU_TO.csv; GLD: data/csv/GLD.csv; IEF: data/csv/IEF.csv (downloaded from Yahoo Finance today); CAD=X: data/csv/CAD_X.csv; ^IRX: data/csv/IRX.csv

**Parameter search on SPY (training data only):** tried **1,920 combinations** and kept the best: `overfit_demo(fast=40, slow=210, band=0.03, min_hold=5)`, training Sharpe 0.86. The median combination scored 0.55. Picking the top of 1,920 tries almost guarantees a lucky winner; the question is whether it holds up in 2018+. (The search scores every combination with next-close timing, so the winner is picked to suit it: in the *Timing cost* table below, its same-close row is not a fair "before".)

**Parameter search on XIU.TO (training data only):** tried **1,920 combinations** and kept the best: `overfit_demo(fast=10, slow=80, band=0.0, min_hold=40)`, training Sharpe 0.85. The median combination scored 0.42. Picking the top of 1,920 tries almost guarantees a lucky winner; the question is whether it holds up in 2018+. (The search scores every combination with next-close timing, so the winner is picked to suit it: in the *Timing cost* table below, its same-close row is not a fair "before".)

## SPY: S&P 500 ETF (US stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). Trades happen at the close after the decision: changing a decision day's closing price never changed what was held over the next day (8 days tested). |
| 2 | Out-of-sample | ❌ FAIL | Sharpe was 0.86 in training (2005-2017) and 0.26 in the 2018+ test. Performance collapsed on data it had never seen, a classic sign of luck or overfitting. |
| 3 | Beats the simple alternatives | ❌ FAIL | Fell short of buy-and-hold at normal costs (Sharpe 0.26 vs 0.68, short by 0.41); the broad index (SPY) at normal costs (Sharpe 0.26 vs 0.68, short by 0.41); the same-risk mix at normal costs (yearly return 5.5% vs 9.1%, short by 3.7 percentage points a year); the equal-risk mix at normal costs (yearly return 5.5% vs 11.8%, short by 6.3 percentage points a year); buy-and-hold at double costs (Sharpe 0.24 vs 0.68, short by 0.43); the broad index (SPY) at double costs (Sharpe 0.24 vs 0.68, short by 0.43); the same-risk mix at double costs (yearly return 5.2% vs 9.1%, short by 3.9 percentage points a year); the equal-risk mix at double costs (yearly return 5.2% vs 11.7%, short by 6.5 percentage points a year). (Same-risk mix = 53% in SPY + 47% in cash, sized on 2005-2017 data. Equal-risk mix = 75% in SPY + 25% in cash, the same mix rescaled so its 2018+ volatility matches the strategy's 2018+ volatility.) |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.86; its 8 neighbours: median 0.67, worst 0.62. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ❔ NEEDS MORE DATA | 16 trades in total (8 in the test period). Fewer than 30: too few to tell skill from luck. |
| 6 | Drawdown | ✅ PASS | Worst fall -32.3% (trough 2020-07-24, took 324 trading days to recover) vs buy-and-hold -55.2%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: +1.4% vs -36.9%; 2020 COVID crash year: -16.6% vs +18.2%; 2022 rate-hike bear market: -9.7% vs -18.3%. No stress period where it was worse on both return and drawdown. |
| 8 | Consistency | ⚠️ WARN | Sharpe dropped from 0.86 (training) to 0.26 (test), a change of -0.60, bigger than the ±0.4 that normal ups and downs explain. A swing this big usually means the period drove the result (the market happened to suit or not suit the rule) rather than a steady edge, so don't lean on either number alone. |
| 9 | **Verdict** | **❌ FAIL** | It failed 2 of 8 checks. Main problem (out-of-sample): test Sharpe 0.26 vs training 0.86. Warning: consistency (Sharpe dropped 0.86 → 0.26). |

**Same-risk mix:** 53% in SPY and 47% in cash earning interest, rebalanced monthly. 53% was chosen so its bumpiness (volatility) matched the strategy's **on 2005-2017 data only**, then frozen for 2018+. In the test period its volatility was 9.8% vs the strategy's 14.0%. If the strategy can't earn more than this simple mix, it is just a complicated way of owning less of the asset. Because the two can end up with different bumpiness in 2018+, check 3 also uses the **equal-risk mix** (below).

### Head to head: strategy vs the same-risk mix

The same-risk mix is 53% in SPY + 47% cash, rebalanced monthly, sized on 2005-2017 so it is as bumpy as the strategy was there. At equal risk the fair question is "who earned more?", so the yearly return (CAGR) decides.

| Period | Costs | Strategy CAGR | Mix CAGR | Difference (points a year) | Strategy volatility | Mix volatility | Strategy worst fall | Mix worst fall |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | normal | 9.7% | 5.4% | +4.29 | 10.1% | 9.9% | -13.4% | -33.1% |
| Train 2005-2017 | double | 9.5% | 5.4% | +4.09 | 10.1% | 9.9% | -13.4% | -33.1% |
| **Test 2018+** | normal | 5.5% | 9.1% | **-3.67** | 14.0% | 9.8% | -32.3% | -18.5% |
| **Test 2018+** | double | 5.2% | 9.1% | **-3.92** | 14.0% | 9.8% | -32.5% | -18.5% |
| Full period | normal | 7.9% | 6.9% | +0.96 | 11.9% | 9.8% | -32.3% | -33.1% |
| Full period | double | 7.7% | 6.9% | +0.74 | 11.9% | 9.8% | -32.5% | -33.1% |

**Answer (test period, 2018+):** the strategy did **not** earn more than simply owning less of the asset (normal costs -3.67% a year, double costs -3.92% a year). **But** in the test period the strategy was bumpier than the mix (volatility 14.0% vs 9.8%), so part of any extra return is simply pay for extra risk. Per unit of risk (Sharpe) it scored 0.26 vs the mix's 0.67.

### Head to head: strategy vs the equal-risk mix (2018+)

The equal-risk mix is the same mix rescaled so that **in 2018+** it was exactly as bumpy as the strategy was in 2018+: 75% in SPY + 25% cash. Using test-period volatility is allowed here because this is a yardstick for judging, not a strategy decision. If the strategy can't earn more than this, any win over the same-risk mix came from taking more risk, not from skill.

| Costs | Strategy CAGR | Equal-risk mix CAGR | Difference (points a year) | Strategy volatility | Equal-risk mix volatility | Strategy Sharpe | Equal-risk mix Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|
| normal | 5.5% | 11.8% | **-6.29** | 14.0% | 14.1% | 0.26 | 0.67 |
| double | 5.2% | 11.7% | **-6.54** | 14.0% | 14.1% | 0.24 | 0.67 |

**Answer:** at the same risk, the strategy did **not** earn more than simply owning less of the asset. Check 3 fails.

### Equity curve

![SPY equity curve](SPY_equity.png)

### Drawdown

![SPY drawdown](SPY_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Avg. share invested |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 9.7% | 0.86 | -13.4% | 10.1% | 9 | 62% | 66% |
| Train 2005-2017 | Strategy (double costs) | 9.5% | 0.84 | -13.4% | 10.1% | 9 | 62% | 66% |
| Train 2005-2017 | Buy-and-hold | 9.0% | 0.49 | -55.2% | 19.2% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 9.0% | 0.49 | -55.2% | 19.2% | 1 | - | 100% |
| Train 2005-2017 | Same-risk mix (53% in, 47% cash) | 5.4% | 0.48 | -33.1% | 9.9% | 1 | - | 53% |
| Test 2018+ | Strategy | 5.5% | 0.26 | -32.3% | 14.0% | 8 | 71% | 71% |
| Test 2018+ | Strategy (double costs) | 5.2% | 0.24 | -32.5% | 14.0% | 8 | 57% | 71% |
| Test 2018+ | Buy-and-hold | 14.6% | 0.68 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.68 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Same-risk mix (53% in, 47% cash) | 9.1% | 0.67 | -18.5% | 9.8% | 1 | - | 53% |
| Test 2018+ | Equal-risk mix (75% in, 25% cash) | 11.8% | 0.67 | -25.8% | 14.1% | 1 | - | 75% |
| Full period | Strategy | 7.9% | 0.56 | -32.3% | 11.9% | 16 | 67% | 68% |
| Full period | Strategy (double costs) | 7.7% | 0.54 | -32.5% | 11.9% | 16 | 67% | 68% |
| Full period | Buy-and-hold | 11.3% | 0.57 | -55.2% | 19.1% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.3% | 0.57 | -55.2% | 19.1% | 1 | - | 100% |
| Full period | Same-risk mix (53% in, 47% cash) | 6.9% | 0.56 | -33.1% | 9.8% | 1 | - | 53% |

*Sharpe = return above the cash rate, per unit of volatility. Avg. share invested = how much of the account was in the market on an average day.*

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![SPY sensitivity](SPY_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | 1.4% | -36.9% | 0.0% | -47.7% |
| 2020 COVID crash year | -16.6% | 18.2% | -32.3% | -33.7% |
| 2022 rate-hike bear market | -9.7% | -18.3% | -11.8% | -24.5% |

### Timing cost (when the trade happens)

The lab decides at a day's close and trades at the **next** day's close. Before session 3 it traded at the *same* close it decided on, which you can't do in real life. This table shows the strategy both ways (normal costs). Only the next-close numbers are used by the Skeptic.

| Period | Timing | CAGR | Sharpe | Max drawdown | Trades |
|---|---|---:|---:|---:|---:|
| Train 2005-2017 | Same close (old, optimistic) | 9.2% | 0.82 | -13.4% | 9 |
| Train 2005-2017 | **Next close (used)** | 9.7% | 0.86 | -13.4% | 9 |
| Test 2018+ | Same close (old, optimistic) | 5.9% | 0.30 | -29.1% | 8 |
| Test 2018+ | **Next close (used)** | 5.5% | 0.26 | -32.3% | 8 |
| Full period | Same close (old, optimistic) | 7.8% | 0.56 | -29.1% | 16 |
| Full period | **Next close (used)** | 7.9% | 0.56 | -32.3% | 16 |

**What changed:** over the full period, trading one close later moved yearly return from 7.8% to 7.9% and Sharpe from 0.56 to 0.56, so the old same-close timing understated this strategy by 0.1 percentage points a year.

## XIU.TO: iShares S&P/TSX 60 ETF (Canadian stocks)

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Signals stayed identical when the future was hidden (6 cut-off dates tested). Trades happen at the close after the decision: changing a decision day's closing price never changed what was held over the next day (8 days tested). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.85 in training (2005-2017) and 0.60 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Beats the simple alternatives | ❌ FAIL | Fell short of buy-and-hold at normal costs (Sharpe 0.60 vs 0.67, short by 0.07); the broad index (SPY) at normal costs (Sharpe 0.60 vs 0.68, short by 0.08); the same-risk mix at normal costs (yearly return 8.6% vs 9.0%, short by 0.4 percentage points a year); the equal-risk mix at normal costs (yearly return 8.6% vs 9.5%, short by 0.9 percentage points a year); buy-and-hold at double costs (Sharpe 0.54 vs 0.67, short by 0.13); the broad index (SPY) at double costs (Sharpe 0.54 vs 0.68, short by 0.13); the same-risk mix at double costs (yearly return 8.0% vs 9.0%, short by 1.0 percentage points a year); the equal-risk mix at double costs (yearly return 8.0% vs 9.5%, short by 1.5 percentage points a year). (Same-risk mix = 62% in XIU.TO + 38% in cash, sized on 2005-2017 data. Equal-risk mix = 68% in XIU.TO + 32% in cash, the same mix rescaled so its 2018+ volatility matches the strategy's 2018+ volatility.) |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.85; its 8 neighbours: median 0.64, worst 0.40. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 35 trades in total (17 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -18.7% (trough 2023-09-27, took 266 trading days to recover) vs buy-and-hold -47.9%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs buy-and-hold: 2008 financial crisis: +2.9% vs -31.2%; 2020 COVID crash year: +4.0% vs +5.1%; 2022 rate-hike bear market: -10.1% vs -6.5%. No stress period where it was worse on both return and drawdown. |
| 8 | Consistency | ✅ PASS | Sharpe went from 0.85 (training) to 0.60 (test), a change of -0.25, within the ±0.4 expected from normal ups and downs. Behaviour was steady. |
| 9 | **Verdict** | **❌ FAIL** | It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.60 vs 0.67, short by 0.07); the broad index (SPY) at normal costs (Sharpe 0.60 vs 0.68, short by 0.08); the same-risk mix at normal costs (yearly return 8.6% vs 9.0%, short by 0.4 percentage points a year); the equal-risk mix at normal costs (yearly return 8.6% vs 9.5%, short by 0.9 percentage points a year); buy-and-hold at double costs (Sharpe 0.54 vs 0.67, short by 0.13); the broad index (SPY) at double costs (Sharpe 0.54 vs 0.68, short by 0.13); the same-risk mix at double costs (yearly return 8.0% vs 9.0%, short by 1.0 percentage points a year); the equal-risk mix at double costs (yearly return 8.0% vs 9.5%, short by 1.5 percentage points a year). |

**Same-risk mix:** 62% in XIU.TO and 38% in cash earning interest, rebalanced monthly. 62% was chosen so its bumpiness (volatility) matched the strategy's **on 2005-2017 data only**, then frozen for 2018+. In the test period its volatility was 9.5% vs the strategy's 10.3%. If the strategy can't earn more than this simple mix, it is just a complicated way of owning less of the asset. Because the two can end up with different bumpiness in 2018+, check 3 also uses the **equal-risk mix** (below).

### Head to head: strategy vs the same-risk mix

The same-risk mix is 62% in XIU.TO + 38% cash, rebalanced monthly, sized on 2005-2017 so it is as bumpy as the strategy was there. At equal risk the fair question is "who earned more?", so the yearly return (CAGR) decides.

| Period | Costs | Strategy CAGR | Mix CAGR | Difference (points a year) | Strategy volatility | Mix volatility | Strategy worst fall | Mix worst fall |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | normal | 10.4% | 5.2% | +5.14 | 11.1% | 10.9% | -15.0% | -32.7% |
| Train 2005-2017 | double | 9.9% | 5.2% | +4.68 | 11.1% | 10.9% | -15.3% | -32.8% |
| **Test 2018+** | normal | 8.6% | 9.0% | **-0.41** | 10.3% | 9.5% | -18.7% | -22.5% |
| **Test 2018+** | double | 8.0% | 9.0% | **-1.00** | 10.3% | 9.5% | -19.9% | -22.5% |
| Full period | normal | 9.6% | 6.8% | +2.89 | 10.8% | 10.4% | -18.7% | -32.7% |
| Full period | double | 9.1% | 6.7% | +2.38 | 10.8% | 10.4% | -19.9% | -32.8% |

**Answer (test period, 2018+):** the strategy did **not** earn more than simply owning less of the asset (normal costs -0.41% a year, double costs -1.00% a year). **But** in the test period the strategy was bumpier than the mix (volatility 10.3% vs 9.5%), so part of any extra return is simply pay for extra risk. Per unit of risk (Sharpe) it scored 0.60 vs the mix's 0.68.

### Head to head: strategy vs the equal-risk mix (2018+)

The equal-risk mix is the same mix rescaled so that **in 2018+** it was exactly as bumpy as the strategy was in 2018+: 68% in XIU.TO + 32% cash. Using test-period volatility is allowed here because this is a yardstick for judging, not a strategy decision. If the strategy can't earn more than this, any win over the same-risk mix came from taking more risk, not from skill.

| Costs | Strategy CAGR | Equal-risk mix CAGR | Difference (points a year) | Strategy volatility | Equal-risk mix volatility | Strategy Sharpe | Equal-risk mix Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|
| normal | 8.6% | 9.5% | **-0.93** | 10.3% | 10.4% | 0.60 | 0.68 |
| double | 8.0% | 9.5% | **-1.52** | 10.3% | 10.4% | 0.54 | 0.68 |

**Answer:** at the same risk, the strategy did **not** earn more than simply owning less of the asset. Check 3 fails.

### Equity curve

![XIU.TO equity curve](XIU.TO_equity.png)

### Drawdown

![XIU.TO drawdown](XIU.TO_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Avg. share invested |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 10.4% | 0.85 | -15.0% | 11.1% | 19 | 72% | 70% |
| Train 2005-2017 | Strategy (double costs) | 9.9% | 0.81 | -15.3% | 11.1% | 19 | 72% | 70% |
| Train 2005-2017 | Buy-and-hold | 7.5% | 0.43 | -47.9% | 17.8% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 9.0% | 0.49 | -55.2% | 18.9% | 1 | - | 100% |
| Train 2005-2017 | Same-risk mix (62% in, 38% cash) | 5.2% | 0.42 | -32.7% | 10.9% | 1 | - | 62% |
| Test 2018+ | Strategy | 8.6% | 0.60 | -18.7% | 10.3% | 17 | 62% | 79% |
| Test 2018+ | Strategy (double costs) | 8.0% | 0.54 | -19.9% | 10.3% | 17 | 62% | 79% |
| Test 2018+ | Buy-and-hold | 12.7% | 0.67 | -35.5% | 15.8% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.68 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Same-risk mix (62% in, 38% cash) | 9.0% | 0.68 | -22.5% | 9.5% | 1 | - | 62% |
| Test 2018+ | Equal-risk mix (68% in, 32% cash) | 9.5% | 0.68 | -24.4% | 10.4% | 1 | - | 68% |
| Full period | Strategy | 9.6% | 0.75 | -18.7% | 10.8% | 35 | 71% | 74% |
| Full period | Strategy (double costs) | 9.1% | 0.70 | -19.9% | 10.8% | 35 | 71% | 74% |
| Full period | Buy-and-hold | 9.6% | 0.52 | -47.9% | 17.0% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.3% | 0.57 | -55.2% | 19.0% | 1 | - | 100% |
| Full period | Same-risk mix (62% in, 38% cash) | 6.8% | 0.52 | -32.7% | 10.4% | 1 | - | 62% |

*Sharpe = return above the cash rate, per unit of volatility. Avg. share invested = how much of the account was in the market on an average day.*

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![XIU.TO sensitivity](XIU.TO_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | 2.9% | -31.2% | -9.5% | -46.9% |
| 2020 COVID crash year | 4.0% | 5.1% | -8.7% | -35.5% |
| 2022 rate-hike bear market | -10.1% | -6.5% | -14.7% | -16.4% |

### Timing cost (when the trade happens)

The lab decides at a day's close and trades at the **next** day's close. Before session 3 it traded at the *same* close it decided on, which you can't do in real life. This table shows the strategy both ways (normal costs). Only the next-close numbers are used by the Skeptic.

| Period | Timing | CAGR | Sharpe | Max drawdown | Trades |
|---|---|---:|---:|---:|---:|
| Train 2005-2017 | Same close (old, optimistic) | 9.1% | 0.74 | -15.0% | 19 |
| Train 2005-2017 | **Next close (used)** | 10.4% | 0.85 | -15.0% | 19 |
| Test 2018+ | Same close (old, optimistic) | 9.4% | 0.67 | -16.0% | 17 |
| Test 2018+ | **Next close (used)** | 8.6% | 0.60 | -18.7% | 17 |
| Full period | Same close (old, optimistic) | 9.2% | 0.72 | -16.0% | 35 |
| Full period | **Next close (used)** | 9.6% | 0.75 | -18.7% | 35 |

**What changed:** over the full period, trading one close later moved yearly return from 9.2% to 9.6% and Sharpe from 0.72 to 0.75, so the old same-close timing understated this strategy by 0.4 percentage points a year.

## Over-search counter

The more things you try, the more likely your best result is luck. The lab counts every parameter combination and idea ever tested on real data in [`journal/trials.csv`](../../journal/trials.csv).

**Lab-wide so far:** 4 ideas, 3,845 parameter combinations tested.

| Tested on | Tries for this idea | Training Sharpe | Luck bar (this idea) | Rough chance it's real | Luck bar (whole lab) |
|---|---:|---:|---:|---:|---:|
| SPY | 1,920 | 0.86 | 0.99 | 33% | 1.04 |
| XIU.TO | 1,920 | 0.85 | 0.97 | 34% | 1.02 |

**Reading this:** the *luck bar* is the Sharpe ratio the luckiest of that many *useless* strategies would be expected to show over the training years, by chance alone. A result below its bar is what luck alone would produce. *Rough chance it's real* compares the training Sharpe with the bar (a simplified "deflated Sharpe ratio"; see LEARNING.md). The whole-lab bar is stricter: it asks "if this were the best of everything the lab ever tried, would it stand out?"


## Test-period looks

The 2018+ test period should be looked at **once** per idea. This idea's test results have been seen **4 times** (every look is logged in [`journal/test_period_looks.csv`](../../journal/test_period_looks.csv); re-running with nothing changed isn't a new look).

| # | Date | Why |
|---:|---|---|
| 1 | 2026-09-26 | Session 1 follow-up: first real-data run on Tessy's PC (lab v1, cash at 0%); see journal/2026-09-26_overfit_demo_real-data-v2.md ("same winners as the lab-v1 run") |
| 2 | 2026-09-26 | Session 2: final real-data run of lab v2 (cash interest, same-risk mix) |
| 3 | 2026-09-26 | Session 3: re-run of every strategy after the trade-timing fix (next-close execution); no parameters changed |
| 4 | 2026-09-28 | new check 3 comparison, no strategy changes |

**Why this matters:** each extra look weakens the test a little. None of these looks was used to choose parameters, but a result seen several times is no longer a completely fresh test. A strategy that is changed *because* of what a look showed must be treated as a new idea.


## How the markets differ

Here is how 5 very different markets behaved over the same years. Stocks (SPY, XIU.TO) are what the single-asset strategies trade; GLD and IEF are also in the multi-asset portfolios; CAD=X is shown for comparison only.

| Market | Average yearly return | Best year | Worst year | Worst drawdown | Moves with SPY (correlation) |
|---|---:|---:|---:|---:|---:|
| SPY: S&P 500 ETF (US stocks) | 12.5% | 32.3% (2013) | -36.8% (2008) | -55.2% | +1.00 |
| XIU.TO: iShares S&P/TSX 60 ETF (Canadian stocks) | 9.9% | 31.4% (2009) | -31.1% (2008) | -47.9% | +0.80 |
| GLD: SPDR Gold ETF (gold) | 11.7% | 63.7% (2025) | -28.3% (2013) | -45.6% | +0.07 |
| IEF: iShares 7-10 Year Treasury Bond ETF (US government bonds) | 3.3% | 17.9% (2008) | -15.2% (2022) | -23.9% | -0.28 |
| CAD=X: USD/CAD exchange rate (Canadian dollars per US dollar) | 1.3% | 21.9% (2008) | -14.3% (2007) | -27.6% | -0.24 |

<details><summary>Year-by-year returns (click to open)</summary>

| Year | SPY | XIU.TO | GLD | IEF | CAD=X |
|---|---:|---:|---:|---:|---:|
| 2006 | 15.8% | 19.1% | 22.5% | 2.5% | 0.3% |
| 2007 | 5.1% | 10.8% | 30.5% | 10.4% | -14.3% |
| 2008 | -36.8% | -31.1% | 4.9% | 17.9% | 21.9% |
| 2009 | 26.4% | 31.4% | 24.0% | -6.6% | -13.5% |
| 2010 | 15.1% | 13.9% | 29.3% | 9.4% | -5.0% |
| 2011 | 1.9% | -9.3% | 9.6% | 15.6% | 2.1% |
| 2012 | 16.0% | 7.9% | 6.6% | 3.7% | -2.5% |
| 2013 | 32.3% | 13.1% | -28.3% | -6.1% | 7.0% |
| 2014 | 13.5% | 11.9% | -2.2% | 9.1% | 9.0% |
| 2015 | 1.2% | -7.8% | -10.7% | 1.5% | 19.5% |
| 2016 | 12.0% | 20.3% | 8.0% | 1.0% | -2.8% |
| 2017 | 21.7% | 9.6% | 12.8% | 2.6% | -6.8% |
| 2018 | -4.6% | -7.8% | -1.9% | 1.0% | 8.4% |
| 2019 | 31.2% | 21.8% | 17.9% | 8.0% | -4.1% |
| 2020 | 18.3% | 5.3% | 24.8% | 10.0% | -2.4% |
| 2021 | 28.7% | 28.1% | -4.1% | -3.3% | -0.0% |
| 2022 | -18.2% | -6.3% | -0.8% | -15.2% | 6.3% |
| 2023 | 26.2% | 11.9% | 12.7% | 3.6% | -2.4% |
| 2024 | 24.9% | 20.7% | 26.7% | -0.6% | 8.5% |
| 2025 | 17.7% | 28.9% | 63.7% | 8.0% | -4.6% |
| 2026 | 14.0% | 14.8% | -0.7% | -3.9% | 3.3% |

</details>

**Reading this in plain English:**

- **Correlation** runs from -1 to +1. +1 means "always moves the same way as SPY", 0 means "no relationship", -1 means "always moves the opposite way". Something with low or negative correlation can cushion a stock portfolio when stocks fall.
- **Canadian vs US stocks** (XIU.TO vs SPY, correlation +0.80): they tend to rise and fall together, so holding both diversifies less than it seems.
- **Gold** (GLD, correlation +0.07): largely goes its own way. It's a commodity with no earnings or dividends; people buy it as a store of value, often when they're worried.
- **US government bonds** (IEF, correlation -0.28): a loan to the US government for 7-10 years that pays interest. Bond prices move opposite to interest rates: when rates rise, older bonds paying less are worth less. In most stock crashes (2008, 2020) investors fled to safety, rates fell and IEF *rose*, so it often cushions a stock portfolio. But when inflation forces rates up fast (2022), stocks and bonds can fall together.
- **USD/CAD** (CAD=X, correlation -0.24): this is a *price of a currency*, not an investment that grows. When it goes UP, one US dollar buys more Canadian dollars (the CAD got weaker). It usually moves much less than stocks, which is why forex traders often use leverage (borrowed money), and that's where forex gets dangerous.
- **Worst drawdown** is the biggest peak-to-bottom fall. It's the number that tells you how much pain you'd have had to sit through.


---
*How to read the numbers: see [LEARNING.md](../../LEARNING.md).*
