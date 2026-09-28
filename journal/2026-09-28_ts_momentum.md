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
