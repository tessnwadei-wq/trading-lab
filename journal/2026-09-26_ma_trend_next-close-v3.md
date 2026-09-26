# ma_trend, real data, lab v3: next-close trade timing (2026-09-26)

- **Idea:** Hold the asset when its price is above its 200-day moving average, otherwise hold cash.
  Source: Meb Faber, "A Quantitative Approach to Tactical Asset Allocation" (2007).
- **Data:** real (`data/csv/`), SPY and XIU.TO, Jan 2005 – 25 Sep 2026; cash earns the T-bill rate.
- **What changed (the lab, not the rule):** a decision made at day t's close is now traded at day t+1's close.
  Until now the lab bought and sold at the *same* close it used to decide, which can't be done in real life.
  The old timing is still shown in the report's new *Timing cost* table, for comparison only.
- **Parameters:** ma_length = 200, band = 0. Textbook values, unchanged, not tuned.
- **Result:**

  | | SPY before (same close) | SPY after (next close) | XIU.TO before | XIU.TO after |
  |---|---|---|---|---|
  | Sharpe, train → test | 0.56 → 0.64 | 0.50 → 0.58 | 0.16 → 0.68 | 0.13 → 0.60 |
  | Test CAGR: strategy / same-risk mix | 10.3% / 9.7% | 9.5% / 9.7% | 9.2% / 8.9% | 8.4% / 9.0% |
  | Test Sharpe: buy-and-hold / SPY | 0.68 / 0.68 | 0.68 / 0.68 | 0.67 / 0.68 | 0.67 / 0.68 |
  | Full-period CAGR | 8.2% | 7.6% | 5.1% | 4.6% |
  | Max drawdown (full) | -21.9% | -24.5% | -26.3% | -26.9% |
  | Trades (total / test) | 63 / 26 | 63 / 26 | 89 / 27 | 89 / 27 |

- **Verdict:** **FAIL** (both assets), still failing only check 3.
  - SPY: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.58 vs 0.68, short by 0.10); the broad index (SPY) at normal costs (Sharpe 0.58 vs 0.68, short by 0.10); the same-risk mix at normal costs (yearly return 9.5% vs 9.7%, short by 0.2 percentage points a year); buy-and-hold at double costs (Sharpe 0.51 vs 0.68, short by 0.17); the broad index (SPY) at double costs (Sharpe 0.51 vs 0.68, short by 0.17); the same-risk mix at double costs (yearly return 8.6% vs 9.7%, short by 1.1 percentage points a year)."
  - XIU.TO: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.60 vs 0.67, short by 0.07); the broad index (SPY) at normal costs (Sharpe 0.60 vs 0.68, short by 0.08); the same-risk mix at normal costs (yearly return 8.4% vs 9.0%, short by 0.6 percentage points a year); buy-and-hold at double costs (Sharpe 0.50 vs 0.67, short by 0.17); the broad index (SPY) at double costs (Sharpe 0.50 vs 0.68, short by 0.17); the same-risk mix at double costs (yearly return 7.4% vs 8.9%, short by 1.5 percentage points a year). Warning: consistency (Sharpe jumped 0.13 → 0.60)."
- **Lesson:** Trading one day later cost the 200-day rule about 0.5-0.7 percentage points a year. That was exactly
  the size of its small lead over the same-risk mix, so the lead is gone: it now loses **all six** comparisons in
  check 3 on both assets, even at normal costs. In session 2 it beat the same-risk mix on SPY and beat everything on
  XIU.TO at normal costs; those "wins" were the optimistic timing. A trend rule acts right at the turning points,
  which is where a one-day delay hurts most.
- **Test-period looks for this idea:** 3 (see `journal/test_period_looks.csv`). No parameter was changed because of any look.
- **Report:** [reports/ma_trend/report.md](../reports/ma_trend/report.md)
