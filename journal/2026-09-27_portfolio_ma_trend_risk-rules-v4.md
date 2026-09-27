# portfolio_ma_trend, real data, lab v4: Tessy's risk-rule decisions (2026-09-27)

- **Idea:** unchanged: the 200-day moving-average rule on SPY, XIU.TO and GLD as one account with the CLAUDE.md risk
  rules. Source: Meb Faber (2007). No strategy parameter changed.
- **What changed (Tessy's decisions on the session-3 risk review):**
  1. **1% rule, one-day buffer.** Positions are sized as if the stop were 2 more average daily moves away
     (`STOP_FILL_BUFFER_MOVES = 2` in `lab/config.py`), so a stop-out normally stays within 1% even though the sale
     fills a close later. Chosen from training data (81% of the 21 stop-outs in 2005-2017 filled within 2 moves past
     the stop) and common sense (a one-day fall bigger than 2 average moves happens on ~7% of days). Not tuned on 2018+.
  2. **20% rule reworded** to what the code does: "No buy that would take a position above 20%. Anything above 20% at a
     close is trimmed to 18% at the next close." Plus an **alert** (logged, printed, in the report) when a position ends a
     day above 22%.
  3. **Human-only circuit-breaker reset.** CLAUDE.md: "Agents must never run, script or suggest automating
     `reset_circuit_breaker.py`. Only Tessy resets it." The command refuses to run from a script, needs a typed `RESET`,
     and for the 20% hard floor also `HARD FLOOR` and the name again. The reset log is hash-chained and its size and
     fingerprint are kept in the breaker state, so an edited or shortened log blocks resets (tests in
     `tests/test_breaker.py`).
  4. Fixes from the risk review: a pending sale no longer frees a slot for a 6th position (possible on a market holiday);
     the 22% alert also checks days an asset's own market is shut.
- **Worst real loss per trade (full period, share of the account):**

  | | Before (session 3, no buffer) | After (one-day buffer) |
  |---|---|---|
  | Entries sized by the 1% rule (rest capped at 20%) | 11 of 233 | 63 of 233 |
  | Worst stop-out | 1.00% | **0.99%** |
  | Stop-outs over 1% | 1 of 29 | **0 of 29** |
  | Closed trades over 1% (any exit) | 4 | **1** |
  | Worst closed trade (any exit) | 1.14% | 1.13% |
  | Largest position at a close / position alerts above 22% | 20.4% / (no alert yet) | 20.4% / **0** |

  The one trade still over 1% is a *signal* exit, not a stop: XIU.TO, bought 8 June 2020, "sell" decided 10 June, filled
  11 June on a -3.95% day (lost 1.13%). The buffer covers normal days; a gap like that can still go past 1%.
- **Result:** Sharpe train → test 0.37 → 0.71 (was 0.34 → 0.74); test CAGR 6.1% vs equal-weight buy-and-hold 14.3% and
  same-risk mix (31% in) 6.3%; full-period max drawdown -7.9%; 233 trades; circuit breaker never triggered.
- **Verdict:** **FAIL**, unchanged (check 3: loses to equal-weight buy-and-hold and to the same-risk mix).
- **Risk-manager review (session 4): still BLOCKED for paper trading** (research use is fine). Of the seven session-3 items:
  - Resolved (5): the 1% rule's meaning (buffer); the 20% wording and 22% alert; the human-only reset; the append-only
    reset log (for accidental or casual edits; deliberate edits to both the log and the state file are only caught by
    comparing with git); the 6th-position bug on a market holiday (on made-up data; only 3 real assets so far).
  - Still open (2): **a strategy that passes the whole Skeptic Checklist**, and **the paper-trading runner** (refuse to
    start if the breaker's state file or reset log is missing or doesn't match git, and an end-to-end test: trip →
    blocked → manual reset → resume).
  - The reviewer also noted: the "person at a terminal" check is a speed bump that a program could fake; the real
    protection is the CLAUDE.md rule. Claude wrote the new CLAUDE.md risk wording, so **Tessy should read and approve it**
    before merging.
- **Lesson:** Rules have to be written for how trading actually happens (orders fill a day later). Writing the delay
  into the sizing turned "1%, usually" into "1%, on normal days", and it took an adversarial review to find a
  holiday-only bug that no normal test would hit.
- **Test-period looks for this idea:** 5 (one new, logged: "Session 4 Part A: risk-rule changes ...").
- **Report:** [reports/portfolio_ma_trend/report.md](../reports/portfolio_ma_trend/report.md)
