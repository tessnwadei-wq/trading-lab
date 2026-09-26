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

---

## Update, 2026-09-26 (session 2: real data, lab v2)

*Added underneath; the summary above is kept as written.*

**Experiments this month so far:** 5 (2 synthetic, 3 real). **PASS 0 · FAIL 5 · NEEDS MORE DATA 0.**
**Ideas tested on real data:** 3 (ma_trend, overfit_demo, portfolio_ma_trend), **3,843 parameter combinations**
(see `trials.csv`; 3,840 of them are overfit_demo's deliberate search).

| Date | Strategy | Verdict | One-line reason |
|---|---|---|---|
| 2026-09-26 | ma_trend (real, v2) | FAIL | Trails buy-and-hold on Sharpe; beats the same-risk mix on SPY only at normal costs. XIU.TO: consistency WARN. |
| 2026-09-26 | overfit_demo (real, v2) | FAIL | Best-of-1,920 training Sharpe sits below its luck bar; loses to buy-and-hold in 2018+. |
| 2026-09-26 | portfolio_ma_trend | FAIL | Risk rules cut the worst fall to -7.6%, but it's mostly cash; loses to equal-weight buy-and-hold and, at double costs, the same-risk mix. |

### Top lessons (session 2)
1. **Compare at equal risk.** A strategy that's in cash 20-60% of the time should be judged against "that much of the
   asset + cash", not only against 100% of the asset. The 200-day rule is only a little better than that simple mix.
2. **Cash isn't free money, but it isn't zero either.** Crediting T-bill interest helped the trend rules, and measuring
   Sharpe above the cash rate lowered everyone's score. Neither changed a verdict.
3. **Risk rules shrink drawdowns by shrinking exposure.** With 3 assets and a 20% cap, the portfolio is never more than
   ~60% invested, so its returns look like a cautious mix.
4. **A big jump from training to test is a warning, not a win** (XIU.TO 0.16 → 0.68).
