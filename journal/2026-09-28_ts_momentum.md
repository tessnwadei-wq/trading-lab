# ts_momentum, real data, pre-registered (2026-09-28)

- **Idea:** Time-series momentum on SPY, XIU.TO, GLD and IEF as one account with every risk rule: at each month-end,
  hold an asset (up to 20%, sized by the 1% rule) only if its past 12-month total return beat the T-bill return over the
  same 12 months; otherwise cash for that slot. Source: Moskowitz, Ooi & Pedersen (2012); counterpoints Kim, Tse & Wald
  (2016), Huang et al. (2020). Tessy's session-5 brief, item 3.
- **Pre-registration:** rules frozen in [`strategies/specs/ts_momentum.md`](../strategies/specs/ts_momentum.md), committed
  on their own as **`30c8706d96354ebf52b67911aef0bbe074c0c0bf`** (2026-09-28 16:36 UTC) and pushed to GitHub **before any
  code was written and before any test-period look**.

## Before the look (written before running the test)

Development used demo data and real data cut off at 2017-12-31 only. What the training data (2006-2017) showed while
debugging, recorded here *before* the look so nobody can say it was hidden:

- The signal works as specified (spot check: at end-2008 SPY = cash, IEF and GLD = hold). 49 signal changes in
  2006-2017 (SPY 8, XIU.TO 6, GLD 24, IEF 11).
- **The frozen stop rule dominates the result.** The spec says each month-end resize resets the stop to 3 × the 20-day
  average daily move below the fill price. That is a median of only 1.7% below SPY's price (0.9% for IEF), so normal
  dips stop positions out mid-month: 205 stop-outs in 2006-2017, and about a quarter of all "hold" days were spent in
  cash waiting for the next month-end. Training result: Sharpe **0.02** (CAGR 1.0%, volatility 3.8%) vs the fair
  control's **0.61** (CAGR 5.8%).
- This is how the pre-registered rules behave, not a bug (tests check each part). The spec is frozen, so it is **not**
  being changed: the one look tests it as written. A version with a different stop rule would be a new idea.

*Correction (2026-09-28, after the look):* the development script above miscounted GLD's training flips as 24; the lab's
own count is 26, so 51 in total for training (the script lined the four assets up on one shared calendar, which put
blank rows next to two of GLD's flips). The signals themselves are identical; only that scratch count was wrong.

## The one look

- **Command:** `python run_lab.py --strategy ts_momentum --reason "ts_momentum pre-registered test"` → look #1 in
  `test_period_looks.csv`. (A second run only fixed report wording; identical numbers, so not a new look.)
- **Data:** real (`data/csv/`), 2005 – 25 Sep 2026; first signal Jan 2006; cash earns the T-bill rate.
- **Parameters:** 12-month lookback, no skip, T-bill hurdle, monthly (from the paper). **No search:** 1 configuration in
  `trials.csv`.
- **Result (test period 2018+, after costs, next-close execution):**

  | | Strategy | Fair control (20% each, always) | Equal-risk mix (43% basket) | Equal-weight buy-and-hold | SPY |
  |---|---:|---:|---:|---:|---:|
  | CAGR, normal costs | 4.7% | 9.2% | 6.3% | 10.8% | 14.6% |
  | Sharpe, normal costs | **0.47** | **0.81** | 0.81 | 0.80 | 0.68 |
  | Sharpe, double costs | **0.26** | **0.80** | 0.80 | 0.80 | 0.68 |
  | Volatility | 4.2% | 7.9% | 4.3% | 9.9% | 19.0% |
  | Worst fall | -8.0% | -14.1% | -7.7% | -17.5% | -33.7% |
  | Average share invested | 36% | 80% | 43% | 100% | 100% |

  - vs the equal-risk mix: **-1.56** points a year (normal costs), **-2.45** (double).
  - Training → test Sharpe: 0.02 → 0.47. Signal changes: 96 in total, 45 in the test period, 8.7 test years.
  - Stress periods vs equal-weight buy-and-hold: 2008 +2.6% vs -13.3%; 2020 -0.2% vs +15.3%; 2022 -4.4% vs -10.1%.
  - Sensitivity grid (training Sharpe, lookback × skip): every setting between -0.20 and +0.07. Nothing works on
    2006-2017, so the "hill" is flat at zero.
  - Risk rules, full period: 317 stop-outs (average loss 0.47% of the account), **15 over the 1% budget, worst 2.39%**;
    374 monthly resizes; 599 trims; 0 alerts over 22%; circuit breaker never triggered (worst fall -8.2%).

- **Verdict:** **FAIL**, word for word: "It failed 2 of 8 checks. Main problem (beats the simple alternatives): it fell
  short of equal-weight buy-and-hold at normal costs (Sharpe 0.47 vs 0.80, short by 0.34); ..." (all ten check-3
  comparisons were lost) plus check 4 (parameter sensitivity: training Sharpe 0.02, neighbours' median -0.03, worst
  -0.20). Check 8 WARN (Sharpe jumped 0.02 → 0.47).
- **The pre-registered "what would prove it wrong" test (spec section 8):** **triggered.** In 2018+ it lost to the fair
  control on Sharpe (0.47 vs 0.81; 0.26 vs 0.80 at double costs) and to the equal-risk mix on return (-1.56 / -2.45
  points a year).
- **In plain English:** the momentum signal, wrapped in the lab's risk rules, did not add anything. Just holding the
  four assets at 20% each did much better per unit of risk. The main reason is visible in the training data before the
  look: stops sitting about 1-2% below the price, reset every month, turned ordinary wobbles into sales, and the asset
  then sat in cash until the next month-end. So the strategy was only 36% invested on average and paid for ~300
  round trips. It did protect in crashes (2008 +2.6% while the basket lost 13%), but it missed the 2020 rebound.
- **No tweaks.** Following the spec (section 9), this idea is closed as FAIL. A wider or non-resetting stop, volatility
  scaling, a different lookback or dropping the risk rules would each be a **new idea** with a new spec and a new look.
  The fairest next test is probably "the same signal, with the stop rule designed for a monthly strategy", pre-registered.
- **Lesson:** a risk rule designed for one kind of strategy (a daily trend filter with a stop that stays put) can quietly
  change what a different strategy does. With monthly resets, the stop became the main trading rule. Checking how the
  rules interact belongs in the spec, before the look.
- **Test-period looks for this idea:** 1.
- **Report:** [reports/ts_momentum/report.md](../reports/ts_momentum/report.md)

*Correction (2026-09-28, after the risk-manager review):* the review found that monthly resizes were sized without
allowing for the same day's trading costs, so a top-up could land a hair above 20% (e.g. 20.002%). The engine now
sizes all of a day's resizes together, exactly (`same_day_trades` in `lab/portfolio.py`). No strategy setting
changed. Re-running it was look #2 ("engine bug fix from the session-5 risk review ..."). Nothing important moved:
2018+ Sharpe 0.46 vs the fair control's 0.81 (0.27 vs 0.80 at double costs), -1.58 / -2.46 points a year vs the
equal-risk mix, training Sharpe 0.01, 17 of 317 stop-outs over the 1% budget (worst 2.39%). **Verdict unchanged: FAIL**
(checks 3 and 4). The tables above are from look #1; the report shows look #2.
