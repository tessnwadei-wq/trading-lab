# ma_trend, real data, lab v2 (2026-09-26)

- **Idea:** Hold the asset when its price is above its 200-day moving average, otherwise hold cash.
  Source: Meb Faber, "A Quantitative Approach to Tactical Asset Allocation" (2007).
- **Data:** real (Yahoo Finance, dividend-adjusted, committed in `data/csv/`); SPY and XIU.TO, Jan 2005 – 25 Sep 2026.
  Cash earns the 13-week T-bill rate (^IRX). Same rule and parameters as before; what changed is the *lab*:
  cash interest, Sharpe above the cash rate, the same-risk mix benchmark, the renamed check 3 and the new consistency check.
- **Parameters:** ma_length = 200, band = 0. Textbook values, not tuned (1 configuration per asset in `journal/trials.csv`).
- **Earlier real-data run (Tessy's PC, lab v1, cash at 0%), for the record:** SPY $1 → $4.95 vs $9.49 buy-and-hold,
  worst fall -23% vs -55%; failed only the old "Costs" check on both assets. (Not journaled at the time.)
- **Result (lab v2):**

  | | SPY | XIU.TO |
  |---|---|---|
  | Sharpe (above cash), train → test | 0.56 → 0.64 | 0.16 → 0.68 |
  | Test Sharpe: strategy / double costs / buy-and-hold / SPY | 0.64 / 0.57 / 0.68 / 0.68 | 0.68 / 0.59 / 0.67 / 0.68 |
  | Same-risk mix | 57% SPY + 43% cash | 61% XIU.TO + 39% cash |
  | Test CAGR: strategy / double costs / same-risk mix | 10.3% / 9.4% / 9.7% | 9.2% / 8.2% / 8.9% |
  | Full-period CAGR: strategy vs same-risk mix | 8.2% vs 7.4% | 5.1% vs 6.5% |
  | Max drawdown (full): strategy / same-risk mix / buy-and-hold | -21.9% / -35.4% / -55.2% | -26.3% / -32.3% / -47.9% |
  | $1 grew to (full period, after costs) | $5.25 (buy-and-hold $9.49) | — |
  | Trades (total / test) | 63 / 26 | 89 / 27 |

- **Verdict:** **FAIL** (both assets).
  - SPY: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at normal costs (Sharpe 0.64 vs 0.68, short by 0.04); the broad index (SPY) at normal costs (Sharpe 0.64 vs 0.68, short by 0.04); buy-and-hold at double costs (Sharpe 0.57 vs 0.68, short by 0.11); the broad index (SPY) at double costs (Sharpe 0.57 vs 0.68, short by 0.11); the same-risk mix at double costs (yearly return 9.4% vs 9.7%, short by 0.3 percentage points a year)."
  - XIU.TO: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of buy-and-hold at double costs (Sharpe 0.59 vs 0.67, short by 0.08); the broad index (SPY) at double costs (Sharpe 0.59 vs 0.68, short by 0.09); the same-risk mix at double costs (yearly return 8.2% vs 8.9%, short by 0.7 percentage points a year). Warning: consistency (Sharpe jumped 0.16 → 0.68)."
- **Lesson:** Tessy's question was "is the 200-day rule just owning less stock?" Partly yes. On SPY it did slightly
  better than simply holding 57% SPY + 43% cash (10.3% vs 9.7% a year in the test, 8.2% vs 7.4% over the full period,
  with a much smaller worst fall), but the lead disappears at double costs. On XIU.TO the whole-period result is worse
  than the same-risk mix; only the friendly 2018+ period flattered it, which is exactly what the new consistency WARN
  flags. Crediting cash with interest helped the strategy ($4.95 → $5.25 on SPY) but not enough to change any verdict.
- **Report:** [reports/ma_trend/report.md](../reports/ma_trend/report.md)
