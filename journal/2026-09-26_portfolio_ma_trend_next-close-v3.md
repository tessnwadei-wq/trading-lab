# portfolio_ma_trend, real data, lab v3: next-close timing + manual-reset breaker (2026-09-26)

- **Idea:** The 200-day moving-average rule on SPY, XIU.TO and GLD as one account with the CLAUDE.md risk rules.
  Source: Meb Faber (2007). Same rule and risk settings as session 2.
- **Data:** real (`data/csv/`), 2005 – 25 Sep 2026; cash earns the T-bill rate; XIU.TO's currency ignored.
- **What changed:** every order (entry, stop sale, signal sale, trim) now fills at the close *after* the decision.
  The circuit breaker moved to `lab/breaker.py`: in a backtest it assumes a 21-trading-day review (written in the
  report); in paper mode only a logged manual reset restarts it.
- **Result:**

  | | Before (same close) | After (next close) |
  |---|---|---|
  | Sharpe, train → test | 0.38 → 0.84 | 0.34 → 0.74 |
  | Test CAGR: portfolio / equal-weight buy-and-hold / same-risk mix | 6.9% / 14.3% / 6.5% | 6.4% / 14.3% / 6.5% |
  | Full-period CAGR | 4.4% | 4.1% |
  | Max drawdown (full) | -7.6% | -7.9% |
  | Trades (total / test) | 233 / 88 | 233 / 88 |
  | Worst closed trade, % of account | -0.83% | **-1.14%** |
  | Largest position at a close | 20.0% | **20.4%** (150 position-days above 20%, each trimmed at the next close) |
  | Circuit breaker | never triggered | never triggered |

- **Verdict:** **FAIL**: "It failed 1 of 8 checks. Main problem (beats the simple alternatives): it fell short of
  equal-weight buy-and-hold at normal costs (Sharpe 0.74 vs 0.87, short by 0.13); the same-risk mix at normal costs
  (yearly return 6.4% vs 6.5%, short by 0.04 percentage points a year); equal-weight buy-and-hold at double costs
  (Sharpe 0.63 vs 0.87, short by 0.24); the broad index (SPY) at double costs (Sharpe 0.63 vs 0.68, short by 0.04);
  the same-risk mix at double costs (yearly return 5.8% vs 6.5%, short by 0.6 percentage points a year)."
  The consistency WARN is gone (0.34 → 0.74 is a change of +0.40, right at the limit), because honest timing lowered
  the test Sharpe more than the training Sharpe.
- **Risk-manager review (session 3): still BLOCKED for paper trading** (research use is fine). The original blocker,
  the self-restarting breaker, is fixed in design: paper mode never restarts by itself, and a reset needs a name and a
  reason and is logged. Still needed before paper trading:
  1. A strategy that passes the whole Skeptic Checklist (this one fails check 3).
  2. Tessy decides the 1% rule's meaning: "planned risk 1%" (real losses can exceed it: worst was 1.14% because a stop
     sale fills a day later), or add a one-day buffer to the sizing.
  3. Reword the 20% rule to what's enforced ("no buy above 20%; anything above 20% at a close is cut to 18% at the next
     close") and add an alert above ~22%.
  4. Build the paper-trading runner with the breaker in paper mode; refuse to start if its state file is missing or
     edited; test trip → blocked → manual reset → resume end to end.
  5. Make the reset human-only: a typed confirmation, a rule that agents never run it, and an extra step for the 20% hard floor.
  6. A test that the reset log is only ever added to.
  7. Test the 5-position limit with more than 5 real assets (including a day one market is shut, where the reviewer
     found a possible 6th position for one day).
- **Lesson:** Honest timing costs the portfolio ~0.3 points a year and is enough to lose to the plain same-risk mix
  even at normal costs. Timing also shows up in the risk numbers: a rule checked at one close and acted on at the
  next can be overshot for a day, so the rules have to be written for how trading actually works.
- **Test-period looks for this idea:** 4 (three in session 2, one now).
- **Report:** [reports/portfolio_ma_trend/report.md](../reports/portfolio_ma_trend/report.md)
