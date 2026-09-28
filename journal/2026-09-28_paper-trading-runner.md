# Paper-trading runner and risk-manager review (2026-09-28)

- **What:** `paper_trade.py` (engine `lab/paper.py`), a local paper account Tessy runs by hand: $10,000 of pretend
  money, real closing prices, orders decided at one close and filled at the next, costs charged, every risk rule and
  the manual-reset circuit breaker enforced, every order / fill / balance / event logged in `journal/paper/`.
- **Strategy allowed:** only `buy_and_hold` of the 4-asset control mix (SPY, XIU.TO, GLD, IEF at up to 20% each).
  Any other strategy is refused until one passes the full Skeptic Checklist. **A practice run of the plumbing, not a
  strategy test.** Tessy opens the real account herself (`python paper_trade.py --start --refresh`); none was opened
  in this session.
- **Safety checks:** refuses to run if the account file, breaker file or reset log is missing, edited (account checksum,
  log fingerprint, reset-log hash chain, breaker fingerprint without a logged reset) or doesn't match git; refuses a
  new `--start` if an account ever existed (logs or git history). Commits only its own files after each run.
- **End-to-end test** (`tests/test_paper.py`): crash → breaker trips → buys blocked on every run → manual reset (done
  inside the test only, playing Tessy's typed `RESET`) → refused until the reset is committed → trading resumes.

## Risk-manager review (session 5)

- **First pass: BLOCKED**, with two real bugs:
  1. monthly resizes ignored the day's trading costs and landed a hair above 20% (20.002%): the same bug was in the
     backtest engine (it touched ts_momentum; re-run as look #2, verdict unchanged);
  2. deleting the account files and running `--start` opened a fresh, untripped account: a way round the breaker.
  Plus two recommendations: flag a hard-floor trip even when the 10% breaker is already on, and refuse a breaker file
  that changed without a logged reset.
- **All four fixed** (commit `99b577b`), with tests: same-day trades are now sized exactly (`same_day_trades`).
- **Second pass: CLEARED for the `buy_and_hold` practice run only.** One line per rule, from the review:
  1% risk: every buy and resize is sized with the 2-move buffer, stops fill at the next close. Max 5 positions:
  enforced (can't bind with 4 assets). 20% rule: no buy above 20%, trimmed to 18% at the next close, 22% alert.
  10% breaker and 20% hard floor: trip, block buys and top-ups, never restart by themselves. Human-only reset: the
  breaker only changes through a logged reset; a determined faker would leave commits in git history.
- **No real strategy is cleared:** none has passed the Skeptic Checklist (session-4 open item 1 stays open). Session-4
  open item 2 (the runner and its end-to-end test) is **closed**.
- **Design question for Tessy (not a bug):** a position resized to exactly 20% drifts above 20% as soon as its price
  rises, so it's trimmed to 18% the next close and topped back up at the month-end. That churn costs a little every
  month. Options: resize to 19% or 18% instead, or leave it. It's a risk-rule decision, so it's yours.
- **What it proves / doesn't:** it proves the day-to-day mechanics and safety checks work on real closes. It says
  nothing about making money.
