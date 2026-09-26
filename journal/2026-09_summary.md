# September 2026 summary

**Experiments this month:** 2 (both on synthetic demo data). **PASS 0 · FAIL 2 · NEEDS MORE DATA 0.**
**Ideas tested since the lab began:** 2.

| Date | Strategy | Verdict | One-line reason |
|---|---|---|---|
| 2026-09-26 | ma_trend | FAIL | Didn't beat buy-and-hold/SPY on risk-adjusted return after costs; whipsawed in 2020. |
| 2026-09-26 | overfit_demo | FAIL | Deliberately overfit; caught by the out-of-sample collapse (XIU.TO) and the "magic number" sensitivity check (SPY). |

## Top lessons
1. **Buy-and-hold is a tough benchmark.** Sitting in cash to dodge crashes costs a lot in the rebounds, and trading costs add up.
2. **Searching many settings manufactures great-looking backtests.** The skeptic's out-of-sample and sensitivity checks are what expose it.
3. **Synthetic data proves the machinery, not the strategy.** Both verdicts must be redone on real prices.

## Next month
Re-run both strategies on real data (see README "How to run"), then log the real results as new entries (don't overwrite these).
