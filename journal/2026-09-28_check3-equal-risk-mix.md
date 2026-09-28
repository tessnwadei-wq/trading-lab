# Check 3 gets the equal-risk mix: re-run of every existing idea (2026-09-28)

- **What changed:** the Skeptic's check 3 ("Beats the simple alternatives") now also compares each strategy with the
  **equal-risk mix**: the same-risk mix rescaled so that its 2018+ volatility equals the strategy's 2018+ volatility,
  compared on yearly return (CAGR) at normal and double costs. Losing to it FAILs check 3. Why: `vol_target` "beat" the
  same-risk mix in session 4 only while being bumpier than it (a loophole: more risk usually earns more). Using
  test-period volatility is allowed because the equal-risk mix is a yardstick for judging, not a strategy decision.
- **Strategy settings changed:** none. Data unchanged (`data/csv/`, up to 25 Sep 2026).
- **Looks:** one per idea, reason "new check 3 comparison, no strategy changes" (`test_period_looks.csv`): ma_trend #4,
  overfit_demo #4, vol_target #2, portfolio_ma_trend #6. The new comparison is new 2018+ information, so it counts as a
  look even though the strategies' own numbers didn't move. No strategy was changed because of these looks.
- **Result (2018+, strategy CAGR minus equal-risk mix CAGR, points a year, normal / double costs):**

  | Idea | Asset | Same-risk mix (old) | Equal-risk mix (new) | Equal-risk mix size |
  |---|---|---:|---:|---|
  | ma_trend | SPY | -0.2 / -1.1 | **-1.34 / -2.27** | 67% SPY |
  | ma_trend | XIU.TO | -0.6 / -1.5 | **-0.91 / -1.87** | 65% XIU.TO |
  | overfit_demo | SPY | -3.67 / -3.92 | **-6.29 / -6.54** | 75% SPY |
  | overfit_demo | XIU.TO | -0.4 / -1.0 | **-0.93 / -1.52** | 68% XIU.TO |
  | vol_target | SPY | **+0.58 / +0.32** | **-0.17 / -0.43** | 69% SPY |
  | vol_target | XIU.TO | **+0.29 / +0.12** | **-1.49 / -1.66** | 84% XIU.TO |
  | portfolio_ma_trend | Portfolio | -0.2 / -0.8 | **-0.85 / -1.43** | 37% in the three assets |

- **Verdict changes:** none. Every idea was already FAIL and stays FAIL. What did change: vol_target's only win (over
  the same-risk mix) disappears. At the same risk as the strategy, simply owning more of the asset and less cash
  earned more on both SPY and XIU.TO.
- **Lesson:** compare at equal risk *in the period you're judging*. A benchmark sized on older data can be quietly
  out-risked, and then any "win" is just pay for extra risk.
- **Reports:** [ma_trend](../reports/ma_trend/report.md), [overfit_demo](../reports/overfit_demo/report.md),
  [vol_target](../reports/vol_target/report.md), [portfolio_ma_trend](../reports/portfolio_ma_trend/report.md)
