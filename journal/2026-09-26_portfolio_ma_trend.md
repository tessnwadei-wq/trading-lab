# portfolio_ma_trend (2026-09-26)

- **Idea:** The 200-day moving-average rule run on SPY, XIU.TO and GLD at once, as one account, with the CLAUDE.md
  risk rules enforced (1% risk per trade via a 3 × 20-day average-daily-move stop, 20% max position trimmed back to 18%,
  5 max positions, 10% circuit breaker with a 21-day simulated review, 20% hard floor). First phase-2 experiment.
- **Data:** real (`data/csv/`), 2005 – 25 Sep 2026; cash earns the T-bill rate; XIU.TO's currency ignored.
- **Parameters:** ma_length = 200, band = 0 (textbook). Risk settings are textbook/CLAUDE.md values, not tuned.
- **Result:**

  | | Portfolio | Equal-weight buy-and-hold | Same-risk mix (32% + cash) | SPY |
  |---|---|---|---|---|
  | Sharpe, train → test | 0.38 → 0.84 | 0.58 → 0.88 | 0.57 → 0.88 | 0.50 → 0.68 |
  | Test CAGR | 6.9% (6.2% double costs) | 14.3% | 6.5% | 14.6% |
  | Max drawdown (full period) | **-7.6%** | -37.8% | -13.3% | -55.2% |
  | Avg. share invested | 40% | 100% | 32% | 100% |
  | Trades (total / test) | 233 / 88 | | | |

  Risk manager: 233 entries; the 20% cap set the size of 222, the 1% rule 11; 185 trims; 17 stop exits; worst closed
  trade -0.83% of the account; at most 3 positions open; circuit breaker never triggered.
- **Verdict:** **FAIL**: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of
  equal-weight buy-and-hold at normal costs (Sharpe 0.84 vs 0.88, short by 0.03); equal-weight buy-and-hold at double
  costs (Sharpe 0.71 vs 0.87, short by 0.16); the same-risk mix at double costs (yearly return 6.2% vs 6.5%, short by
  0.3 percentage points a year). Warning: consistency (Sharpe jumped 0.38 → 0.84)."
- **Risk-manager review:** BLOCKED for paper trading (research use is fine). It found a real bug: positions could
  close at 20.0007% after another position's trim, fixed by repeating the trim pass. It also found two gaps: the 1% risk
  excluded trading costs (now included), and the breaker restarted itself with no floor (a 20% hard floor was added).
  Still open before any paper trading: the breaker's automatic restart must become a manual reset Tessy approves, and
  the 5-position limit is untested on real data.
- **Honesty note:** while building the engine, the 2018+ result of this portfolio was looked at three times: before
  the trim-buffer fix, before the risk-manager fixes, and in the final run. None of the changes touched strategy
  parameters and none were chosen to improve results (they fixed bookkeeping and rule enforcement). The verdict was
  FAIL each time.
- **Lesson:** Risk rules do what they promise: worst fall -7.6% vs -37.8%. But with 3 assets × 20% max, the account is
  never more than ~60% invested, so the portfolio behaves like "a third in assets, the rest in cash", and the plain
  same-risk mix did just as well at double costs with no trading at all. Most "limiting" came from the 20% cap, not
  the 1% rule.
- **Report:** [reports/portfolio_ma_trend/report.md](../reports/portfolio_ma_trend/report.md)
