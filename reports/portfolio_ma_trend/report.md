# Strategy report: `portfolio_ma_trend`

*Generated 2026-09-26 by `python run_lab.py`.*

**Rule:** Hold the asset when price is above its 200-day moving average, otherwise hold cash. Run on SPY, XIU.TO, GLD at the same time as one account, with the CLAUDE.md risk rules enforced (see *Risk manager* below).

**Parameters used:** Portfolio: `ma_trend(ma_length=200, band=0.0) on SPY, XIU.TO, GLD`

**Overall verdict: FAIL**

| Tested on | Verdict | Why |
|---|---|---|
| Portfolio | **FAIL** | It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of equal-weight buy-and-hold at normal costs (Sharpe 0.84 vs 0.88, short by 0.03); equal-weight buy-and-hold at double costs (Sharpe 0.71 vs 0.87, short by 0.16); the same-risk mix at double costs (yearly return 6.2% vs 6.5%, short by 0.3 percentage points a year). Warning: consistency (Sharpe jumped 0.38 → 0.84). |

**Ground rules applied:** costs of 0.10% commission + 0.05% slippage on every buy and every sell; decisions made at the close from that day's data, with gains and losses counted from the next day; parameters chosen on 2005-2017 only; 2018+ used once as the out-of-sample test. Money in cash earns the 13-week US T-bill rate (^IRX), used for every asset including XIU.TO (a simplification), and Sharpe ratios measure return *above* that cash rate.

**Data sources:** SPY: data/csv/SPY.csv; XIU.TO: data/csv/XIU_TO.csv; GLD: data/csv/GLD.csv; CAD=X: data/csv/CAD_X.csv; ^IRX: data/csv/IRX.csv

**Compared with:** equal-weight buy-and-hold of SPY/XIU.TO/GLD (1/3 each, rebalanced monthly), the broad index (SPY), and a same-risk mix of that equal-weight basket plus cash. **Simplification:** XIU.TO is in Canadian dollars and its returns are added as if in the same currency (currency moves are ignored).

## Risk manager

The portfolio enforces the CLAUDE.md risk rules in code (`lab/portfolio.py`). Numbers are for the full period at normal costs.

| Rule | Setting | How often it limited a trade | Worst case seen |
|---|---|---|---|
| Max risk per trade | 1% of the account (costs included), with a stop 3 × the 20-day average daily move below entry | Set the size of **11 of 233** entries (5%); the stop closed 17 trades | Worst closed trade lost 0.83% of the account (stop-outs averaged 0.47%) |
| Max position size | 20% of the account (trimmed back to 18%) | Capped the size of **222 of 233** entries (95%); trimmed a grown position 185 times | Largest position at any close: 20.0% |
| Max open positions | 5 | Blocked 0 entries | Most open at once: 3 (only 3 assets, so this rule can never bind yet) |
| Circuit breaker | Stop new trades after a 10% fall from the peak, review for 21 trading days; stop for good after a 20% fall from the all-time high | Blocked 0 entries; triggered **0** times; hard floor never hit | Worst fall: -7.6% |

**Circuit breaker: never triggered.** The account never fell 10% from its peak.

**In plain English:** the 1% rule works by choosing the position size so that hitting the stop (plus the costs of buying and selling) loses about 1% of the account. For these assets the stop distance was usually under 5%, so the 1% rule would have allowed a position bigger than 20%; the 20% cap was then the rule that actually set the size. A loss can exceed 1% if a price gaps straight through the stop between closes.

**Not yet tested on real data:** the 5-position limit (only 3 assets so far) and the circuit breaker (never triggered). Both are checked with made-up prices in `tests/test_portfolio.py`. The 1-month automatic restart after the 10% breaker is a backtest stand-in for a human review; before any paper trading it must become a manual reset that Tessy approves.

![Portfolio exposure](portfolio_exposure.png)


## Portfolio results

### Skeptic Checklist

| # | Check | Result | What the skeptic found |
|---|---|---|---|
| 1 | Look-ahead bias | ✅ PASS | Each asset's signals, and the whole portfolio's daily value, stayed identical when the future was hidden (6 cut-off dates per asset, 4 for the portfolio). |
| 2 | Out-of-sample | ✅ PASS | Sharpe was 0.38 in training (2005-2017) and 0.84 in the 2018+ test. The edge roughly held up on unseen data. |
| 3 | Beats the simple alternatives | ❌ FAIL | Beat the broad index (SPY) at normal costs (Sharpe 0.84 vs 0.68); the same-risk mix at normal costs (yearly return 6.9% vs 6.5%); the broad index (SPY) at double costs (Sharpe 0.71 vs 0.68). But fell short of equal-weight buy-and-hold at normal costs (Sharpe 0.84 vs 0.88, short by 0.03); equal-weight buy-and-hold at double costs (Sharpe 0.71 vs 0.87, short by 0.16); the same-risk mix at double costs (yearly return 6.2% vs 6.5%, short by 0.3 percentage points a year). (Same-risk mix = 32% in the assets + 68% in cash, sized on 2005-2017 data.) |
| 4 | Parameter sensitivity | ✅ PASS | Chosen setting's training Sharpe 0.38; its 5 neighbours: median 0.46, worst 0.43. Nearby settings work too, so it isn't a single magic number. |
| 5 | Sample size | ✅ PASS | 233 trades in total (88 in the test period). Enough to say something. |
| 6 | Drawdown | ✅ PASS | Worst fall -7.6% (trough 2009-01-21, took 215 trading days to recover) vs equal-weight buy-and-hold -37.8%. Shallower than just holding. |
| 7 | Regime check | ✅ PASS | Strategy vs equal-weight buy-and-hold: 2008 financial crisis: -3.3% vs -21.9%; 2020 COVID crash year: +6.9% vs +16.5%; 2022 rate-hike bear market: -4.5% vs -8.4%. No stress period where it was worse on both return and drawdown. |
| 8 | Consistency | ⚠️ WARN | Sharpe jumped from 0.38 (training) to 0.84 (test), a change of +0.47, bigger than the ±0.4 that normal ups and downs explain. A swing this big usually means the period drove the result (the market happened to suit or not suit the rule) rather than a steady edge, so don't lean on either number alone. |
| 9 | **Verdict** | **❌ FAIL** | It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of equal-weight buy-and-hold at normal costs (Sharpe 0.84 vs 0.88, short by 0.03); equal-weight buy-and-hold at double costs (Sharpe 0.71 vs 0.87, short by 0.16); the same-risk mix at double costs (yearly return 6.2% vs 6.5%, short by 0.3 percentage points a year). Warning: consistency (Sharpe jumped 0.38 → 0.84). |

**Same-risk mix:** 32% in the assets (equal weights) and 68% in cash earning interest, rebalanced monthly. 32% was chosen so its bumpiness (volatility) matched the strategy's **on 2005-2017 data only**, then frozen for 2018+. In the test period its volatility was 4.1% vs the strategy's 4.8%. If the strategy can't earn more than this simple mix, it is just a complicated way of owning less of the asset.

### Equity curve

![Portfolio equity curve](Portfolio_equity.png)

### Drawdown

![Portfolio drawdown](Portfolio_drawdown.png)

### Metrics

| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Avg. share invested |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Train 2005-2017 | Strategy | 2.7% | 0.38 | -7.6% | 4.5% | 148 | 17% | 38% |
| Train 2005-2017 | Strategy (double costs) | 2.0% | 0.23 | -8.3% | 4.5% | 148 | 17% | 38% |
| Train 2005-2017 | Equal-weight buy-and-hold | 8.6% | 0.58 | -37.8% | 13.8% | 1 | - | 100% |
| Train 2005-2017 | Broad index (SPY) | 9.1% | 0.50 | -55.2% | 19.2% | 1 | - | 100% |
| Train 2005-2017 | Same-risk mix (32% in, 68% cash) | 3.6% | 0.57 | -13.3% | 4.4% | 1 | - | 32% |
| Test 2018+ | Strategy | 6.9% | 0.84 | -7.1% | 4.8% | 88 | 21% | 42% |
| Test 2018+ | Strategy (double costs) | 6.2% | 0.71 | -7.6% | 4.8% | 88 | 17% | 42% |
| Test 2018+ | Equal-weight buy-and-hold | 14.3% | 0.88 | -24.8% | 12.9% | 1 | - | 100% |
| Test 2018+ | Broad index (SPY) | 14.6% | 0.68 | -33.7% | 19.0% | 1 | - | 100% |
| Test 2018+ | Same-risk mix (32% in, 68% cash) | 6.5% | 0.88 | -8.3% | 4.1% | 1 | - | 32% |
| Full period | Strategy | 4.4% | 0.57 | -7.6% | 4.6% | 233 | 20% | 40% |
| Full period | Strategy (double costs) | 3.8% | 0.43 | -8.3% | 4.7% | 233 | 19% | 40% |
| Full period | Equal-weight buy-and-hold | 11.0% | 0.70 | -37.8% | 13.4% | 1 | - | 100% |
| Full period | Broad index (SPY) | 11.4% | 0.57 | -55.2% | 19.1% | 1 | - | 100% |
| Full period | Same-risk mix (32% in, 68% cash) | 4.8% | 0.70 | -13.3% | 4.3% | 1 | - | 32% |

*Sharpe = return above the cash rate, per unit of volatility. Avg. share invested = how much of the account was in the market on an average day.*

### Parameter sensitivity (training data only)

Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.

![Portfolio sensitivity](Portfolio_sensitivity.png)

### Stress periods

| Stress period | Strategy return | Equal-weight buy-and-hold return | Strategy worst fall | Equal-weight buy-and-hold worst fall |
|---|---:|---:|---:|---:|
| 2008 financial crisis | -3.3% | -21.9% | -6.8% | -37.8% |
| 2020 COVID crash year | 6.9% | 16.5% | -5.7% | -24.8% |
| 2022 rate-hike bear market | -4.5% | -8.4% | -4.9% | -17.2% |

## Over-search counter

The more things you try, the more likely your best result is luck. The lab counts every parameter combination and idea ever tested on real data in [`journal/trials.csv`](../../journal/trials.csv).

**Lab-wide so far:** 3 ideas, 3,843 parameter combinations tested.

| Tested on | Tries for this idea | Training Sharpe | Luck bar (this idea) | Rough chance it's real | Luck bar (whole lab) |
|---|---:|---:|---:|---:|---:|
| Portfolio | 1 | 0.38 | 0.00 | 91% | 1.04 |

**Reading this:** the *luck bar* is the Sharpe ratio the luckiest of that many *useless* strategies would be expected to show over the training years, by chance alone. A result below its bar is what luck alone would produce. *Rough chance it's real* compares the training Sharpe with the bar (a simplified "deflated Sharpe ratio"; see LEARNING.md). The whole-lab bar is stricter: it asks "if this were the best of everything the lab ever tried, would it stand out?"


---
*How to read the numbers: see [LEARNING.md](../../LEARNING.md).*
