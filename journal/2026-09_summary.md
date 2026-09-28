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

---

## Update, 2026-09-26 (session 3: honest trade timing)

*Added underneath; earlier sections are kept as written.*

**Experiments this month so far:** 8 (2 synthetic, 6 real). **PASS 0 · FAIL 8 · NEEDS MORE DATA 0.**
**Ideas tested on real data:** still 3 (these are re-runs of the same ideas under a corrected engine, not new ideas);
**3,843 parameter combinations** in `trials.csv` (unchanged). **Test-period looks:** ma_trend 3, overfit_demo 3,
portfolio_ma_trend 4 (see `test_period_looks.csv`; the earlier ones were backfilled from this journal).

| Date | Strategy | Verdict | One-line reason |
|---|---|---|---|
| 2026-09-26 | ma_trend (v3) | FAIL | Trading a day later cost ~0.6 points a year; now loses all six "simple alternative" comparisons on both assets. |
| 2026-09-26 | overfit_demo (v3) | FAIL | The search picked new winners; the SPY one collapsed out of sample (0.86 → 0.26) on 16 trades. |
| 2026-09-26 | portfolio_ma_trend (v3) | FAIL | Loses to equal-weight buy-and-hold and now to the same-risk mix even at normal costs; still BLOCKED for paper trading. |

### Top lessons (session 3)
1. **You can't trade at the price you used to decide.** Trading at the next close is the honest default, and it
   removed the 200-day rule's small edge over the same-risk mix.
2. **Count looks, not just tries.** Every view of the test period is now logged; ours were 2-4 per idea, not 1.
3. **Rules need to be written for how trading actually works.** With next-day fills, the 1% and 20% limits can be
   overshot for a day, so their wording and alerts need to say so.

---

## Update, 2026-09-27 (session 4: risk-rule decisions and the first pre-registered idea)

*Added underneath; earlier sections are kept as written.*

**Experiments this month so far:** 10 (2 synthetic, 8 real). **PASS 0 · FAIL 10 · NEEDS MORE DATA 0.**
**Ideas tested on real data:** 4 (ma_trend, overfit_demo, portfolio_ma_trend, vol_target); **3,845 parameter
combinations** in `trials.csv` (vol_target added 1 per asset: no search). **Test-period looks:** ma_trend 3,
overfit_demo 3, portfolio_ma_trend 5, **vol_target 1** (exactly the one the rules allow).

| Date | Strategy | Verdict | One-line reason |
|---|---|---|---|
| 2026-09-27 | portfolio_ma_trend (v4) | FAIL | One-day buffer brought stop-outs within 1% (0 of 29 over); still loses to buy-and-hold and the same-risk mix; still BLOCKED for paper trading. |
| 2026-09-27 | vol_target | FAIL | Beat the same-risk mix after costs in 2018+ by only 0.1-0.6 points a year while being bumpier; lost to buy-and-hold and SPY per unit of risk; missed the 2020 rebound. |

### Top lessons (session 4)
1. **Freeze the rules before you look.** vol_target's spec, sample-size rule and pass/fail line were committed and pushed
   before its first and only look, so its result can't be tuned away.
2. **An edge in training can mostly vanish out of sample.** vol_target beat the same-risk mix by ~2 points a year in
   2005-2017 and by 0.1-0.6 since 2018, as the published counterpoint (Cederburg et al., 2020) predicted.
3. **Compare risk as well as return.** A strategy that earns a bit more than the mix while being bumpier hasn't really
   won; the Sharpe comparison shows it.
4. **Build the delay into the rule.** Sizing for the one-day wait on stop-sales kept every stop-out within 1%.

---

## Update, 2026-09-28 (session 5: equal-risk check, bonds, time-series momentum, paper-account plumbing)

*Added underneath; earlier sections are kept as written.*

**Experiments this month so far:** 12 (2 synthetic, 10 real). **PASS 0 · FAIL 12 · NEEDS MORE DATA 0.**
**Ideas tested on real data:** 5 (ma_trend, overfit_demo, portfolio_ma_trend, vol_target, ts_momentum); **3,846
parameter combinations** in `trials.csv` (ts_momentum added 1: no search). **Test-period looks:** ma_trend 4,
overfit_demo 4, portfolio_ma_trend 6, vol_target 2, **ts_momentum 2** (the second after an engine bug fix; no strategy change).

| Date | Strategy | Verdict | One-line reason |
|---|---|---|---|
| 2026-09-28 | ideas 1-4 re-run with the equal-risk mix in check 3 | FAIL (no changes) | vol_target's win over the same-risk mix becomes a loss at equal risk (SPY -0.17, XIU.TO -1.49 points a year). |
| 2026-09-28 | ts_momentum (pre-registered) | FAIL | Lost to the fair control on Sharpe (0.47 vs 0.81) and to the equal-risk mix (-1.56 points a year); flat sensitivity grid. |

### Top lessons (session 5)
1. **Judge at equal risk in the period you're judging.** A benchmark sized on old data can be out-risked, and then a
   "win" is just pay for extra risk. The equal-risk mix closed that loophole, and vol_target's only win disappeared.
2. **A fair control isolates one thing.** Holding the same four assets at 20% each, always, showed that the momentum
   signal (with the lab's risk rules) added nothing.
3. **Risk rules interact with strategies.** A stop reset every month sat 1-2% below the price and turned normal dips
   into sales; the frozen spec made that visible and un-fixable after the fact, which is the point.
4. **Build the plumbing before you need it.** The paper account now exists, runs only buy-and-hold, and refuses to run
   on edited or uncommitted files.
