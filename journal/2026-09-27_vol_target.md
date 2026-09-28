# vol_target, real data, pre-registered (2026-09-27)

- **Idea:** Volatility targeting: at each month-end hold `min(100%, 12% ÷ last-21-day volatility)` of the asset, the
  rest in cash; traded at the next close. Tessy's question: *is "holding less when markets are jumpy" better than
  simply owning less stock (the same-risk mix)?* Source: [issue #4](https://github.com/tessnwadei-wq/trading-lab/issues/4);
  Moreira & Muir (2017), Harvey et al. (2018); counterpoint Cederburg et al. (2020).
- **Pre-registration:** rules frozen in [`strategies/specs/vol_target.md`](../strategies/specs/vol_target.md), committed
  on their own as **`fc6436bb992c237425a67de0cb4f6917b326c867`** (2026-09-26 23:53 UTC) and pushed to GitHub **before any
  code was written and before any test-period look**. Code was developed on demo data and on 2005-2017 real data only.
  The implementation note on month-end holidays (decide a day late if the last weekday is a holiday) was also written
  before the look.
- **Data:** real (`data/csv/`), SPY and XIU.TO, 2005 – 25 Sep 2026; cash earns the T-bill rate.
- **Parameters:** `target_vol` 12%, `vol_days` 21, monthly, capped at 100% (from issue #4 and the papers). **No search:**
  `trials.csv` has 1 configuration per asset.
- **The one look:** `python run_lab.py --reason "vol_target pre-registered test"` → look #1 in
  `test_period_looks.csv`. (A second run only re-worded the report; its numbers were identical, so it wasn't a new look.)
- **Result (test period 2018+, after costs, next-close execution):**

  | | SPY | XIU.TO |
  |---|---|---|
  | Sharpe, train → test | 0.62 → 0.66 | 0.56 → 0.58 |
  | CAGR: strategy / same-risk mix / buy-and-hold | 10.9% / 10.3% / 14.6% | 9.7% / 9.4% / 12.7% |
  | vs same-risk mix, normal costs | **+0.58** points a year | **+0.29** points a year |
  | vs same-risk mix, double costs | **+0.32** points a year | **+0.12** points a year |
  | Same-risk mix | 63% SPY + 37% cash | 66% XIU.TO + 34% cash |
  | Volatility: strategy vs mix | 12.9% vs 11.8% | 12.9% vs 10.1% |
  | Sharpe: strategy / mix / buy-and-hold | 0.66 / 0.67 / 0.68 | 0.58 / 0.68 / 0.67 |
  | Training-period lead over the mix | +2.14 points a year | +1.91 points a year |
  | Worst fall (full period) vs buy-and-hold | -28.5% vs -55.2% | -29.7% vs -47.9% |
  | 2020 (crash and V-shaped rebound) vs buy-and-hold | +2.2% vs +18.2% | -6.6% vs +5.1% |
  | Active rebalances (≥ 5 points), total / test | 158 / 67 | 131 / 51 |

- **Verdict:** **FAIL** on both assets (check 3).
  - SPY, word for word: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of
    buy-and-hold at normal costs (Sharpe 0.66 vs 0.68, short by 0.01); the broad index (SPY) at normal costs (Sharpe 0.66
    vs 0.68, short by 0.01); buy-and-hold at double costs (Sharpe 0.64 vs 0.68, short by 0.03); the broad index (SPY) at
    double costs (Sharpe 0.64 vs 0.68, short by 0.03)."
  - XIU.TO, word for word: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of
    buy-and-hold at normal costs (Sharpe 0.58 vs 0.67, short by 0.09); the broad index (SPY) at normal costs (Sharpe 0.58
    vs 0.68, short by 0.10); buy-and-hold at double costs (Sharpe 0.56 vs 0.67, short by 0.11); the broad index (SPY) at
    double costs (Sharpe 0.56 vs 0.68, short by 0.11)."
- **The pre-registered "what would prove it wrong" test (spec section 8):** *not* triggered. In 2018+ it earned more
  than the same-risk mix after costs, at normal and double costs, on both assets. But the spec also said every other
  Skeptic check applies, and it lost to buy-and-hold and SPY per unit of risk, so the idea fails.
- **Answer to Tessy's question, in plain English:** a little, maybe, but not convincingly. In 2005-2017 it beat simply
  owning less stock by about 2 points a year. Since 2018 that lead shrank to 0.1-0.6 points a year, and it came with
  *more* bumpiness than the mix (the mix was sized on training data). Per unit of risk it was level with the mix on SPY
  (0.66 vs 0.67) and clearly behind on XIU.TO (0.58 vs 0.68). That's the pattern Cederburg et al. (2020) warned about:
  most of the benefit disappears out of sample. The issue's other worry came true too: in 2020 it cut back after the
  crash and missed much of the rebound.
- **No tweaks.** Following the spec (section 9): this idea is closed as FAIL. A different target, window, drift band,
  variance scaling, leverage, adding GLD, or "only use it on SPY" would each be a **new idea** with a new spec, a new
  trials row and a new test-period look. Nobody may change `strategies/vol_target.py` or its spec to rescue this result.
- **Lesson:** Pre-registration made this an honest test: the rules, the sample-size rule and the pass/fail line were
  all public before the look, so the result can't be argued away. And a strategy can pass the test you cared most about
  (beating the same-risk mix) and still fail overall, because the others (buy-and-hold, the index) matter too.
- **Test-period looks for this idea:** 1.
- **Report:** [reports/vol_target/report.md](../reports/vol_target/report.md)
