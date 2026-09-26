# overfit_demo, real data, lab v3: next-close trade timing (2026-09-26)

- **Idea:** Deliberately bad process (teaching example): fast/slow moving-average crossover with a band and a minimum
  holding period, all four knobs chosen by brute force (1,920 combinations per asset) on 2005-2017.
  Source: Bailey et al., "Pseudo-Mathematics and Financial Charlatanism" (2014).
- **Data:** real (`data/csv/`), SPY and XIU.TO, 2005 – 25 Sep 2026; cash earns the T-bill rate.
- **What changed:** trades now fill at the next close. The search itself is unchanged (same 1,920 combinations, training
  data only), but it now scores every combination with next-close timing, so it **picked new winners**:
  SPY `fast=40, slow=210, band=0.03, min_hold=5` (was `10, 150, 0.02, 10`);
  XIU.TO `fast=10, slow=80, band=0.0, min_hold=40` (was `50, 80, 0.0, 40`).
  (The look log's reason for this run says "no parameters changed". That's true of the rules and the search, not of
  the search's output. The log is append-only, so the correction is here.)
- **Result:**

  | | SPY before | SPY after | XIU.TO before | XIU.TO after |
  |---|---|---|---|---|
  | Sharpe, train → test | 0.87 → 0.68 | 0.86 → **0.26** | 0.83 → 0.45 | 0.85 → 0.60 |
  | Test CAGR: strategy / same-risk mix | 10.3% / 8.9% | 5.5% / 9.1% | 8.0% / 9.2% | 8.6% / 9.0% |
  | Max drawdown (full) | -14.2% | -32.3% | -33.0% | -18.7% |
  | Trades (total / test) | 31 / 13 | **16** / 8 | 30 / 13 | 35 / 17 |
  | Luck bar (best of 1,920) → rough chance it's real | 0.98 → 36% | 0.99 → 33% | 0.97 → 32% | 0.97 → 34% |

- **Verdict:** **FAIL** (both assets).
  - SPY: "It failed 2 of 8 checks. Main problem (out-of-sample): test Sharpe 0.26 vs training 0.86. Warning: consistency (Sharpe dropped 0.86 → 0.26)." (Also NEEDS MORE DATA on sample size: 16 trades.)
  - XIU.TO: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.60 vs 0.67, short by 0.07); ..." (full sentence in the report).
- **Lesson:** A tiny change to the engine changed which of 1,920 combinations "won", and the new SPY winner collapsed
  out of sample (0.86 → 0.26) on only 16 trades. That's the overfitting lesson again: the winner of a big search is
  mostly a product of noise, so any small change reshuffles the ranking. Its training Sharpe is still below the luck
  bar. In the *Timing cost* table the same-close row looks *worse* than next-close, but only because the parameters were
  searched for next-close timing, so that row isn't a fair "before".
- **Test-period looks for this idea:** 3. (A second run the same day, only to fix report wording, showed identical
  numbers and was correctly not counted.)
- **Report:** [reports/overfit_demo/report.md](../reports/overfit_demo/report.md)
