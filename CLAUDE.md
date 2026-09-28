# Trading Lab: project rules

## Purpose

A learning lab for researching and testing rules-based trading strategies.

Owner and researcher: Tessy (beginner in trading/coding, strong in operations). Explain concepts plainly.

Collaborator: Tessy's brother, who has some past forex trading experience and is in his final year of
university. His role is light and optional: he can read reports, comment on pull requests and submit
ideas through the "Strategy idea" form. Never assume he is available; Tessy makes all decisions.
His ideas go through the same Skeptic Checklist as everyone else's.

## Hard rules

- NO live trading. No real-money broker connections. Paper trading only, and only in a later phase.
- Never commit API keys or secrets. Use a .env file (already in .gitignore) and .env.example.
- No strategy is "approved" until it passes every check in the Skeptic Checklist.
- Always compare a strategy against simple buy-and-hold of the same asset AND a broad index.
- Always include trading costs: default 0.10% per trade, plus 0.05% slippage.
- Never tune parameters on the test period. Train/validate on data before 2018; the 2018-onward data is the out-of-sample test, touched once per idea.

## Skeptic Checklist (every strategy report must answer all of these)

1. Look-ahead bias: does any signal use data not available at the time of the trade?
2. Out-of-sample: how does it perform on 2018+ data vs the training period?
3. Beats the simple alternatives: after costs (normal AND double), does it beat buy-and-hold, the broad index,
   the same-risk mix (asset + cash at the strategy's volatility, sized on training data only) AND the equal-risk mix
   (the same mix rescaled so its 2018+ volatility equals the strategy's 2018+ volatility; a judging yardstick, so using
   test-period volatility is allowed)? Beating the mixes only by taking more risk is not a win: losing to the
   equal-risk mix FAILs check 3.
4. Parameter sensitivity: do nearby parameter values also work, or only one "magic" value?
5. Sample size: how many trades? (Under 30 = not enough evidence.)
6. Drawdown: what's the worst peak-to-trough loss, and how long did recovery take?
7. Regime check: results in different periods (e.g. 2008, 2020, 2022).
8. Consistency: is the test-period Sharpe very different from training, in either direction? (WARN only.)
9. Verdict: PASS / FAIL / NEEDS MORE DATA, with one plain-English sentence why.

Each check is PASS, WARN or FAIL (or NEEDS MORE DATA). A WARN is reported but does not fail a strategy on its own.
Sharpe ratios are measured on returns above the cash (T-bill) rate, and cash earns that rate in every backtest.

## Risk rules (enforced in code from phase 2, in `lab/portfolio.py`)

- Max 1% of account at risk per trade: size positions so that, even with the one-day delay on stop-sales, a
  stopped-out trade normally loses no more than 1% of the account (the one-day buffer, `STOP_FILL_BUFFER_MOVES`).
- Max 5 open positions.
- 20% rule: No buy that would take a position above 20%. Anything above 20% at a close is trimmed to 18% at the next
  close. An alert is logged and shown in the report whenever a position ends a day above 22%.
- If the account falls 10% from its peak, stop opening new trades and flag for review.
- The circuit breaker is human-only. Agents must never run, script or suggest automating `reset_circuit_breaker.py`.
  Only Tessy resets it. (A reset needs a name, a reason and a typed `RESET`, plus an extra confirmation for the 20%
  hard floor; the reset log can only be added to.)

## Communication

- Every pull request includes a "What I learned" section explaining new concepts for a beginner.
- Update LEARNING.md (glossary) whenever a new concept appears.
- Keep code simple and well commented over clever.

## Where things live (for agents)

- `lab/` is the engine: data, backtest, metrics, skeptic, report. `strategies/` holds one file per strategy.
- `python run_lab.py` runs every strategy end to end and writes `reports/<strategy>/report.md`.
- The data split, cost defaults and risk settings live in `lab/config.py`. Change them there, nowhere else.
- Prices live in `data/csv/` and are committed. `python run_lab.py --refresh` re-downloads and overwrites them.
- `lab/portfolio.py` runs a strategy on several assets as one account with the risk rules enforced. Each portfolio idea keeps
  its own frozen asset list (`config.PORTFOLIO_STRATEGIES`): portfolio_ma_trend uses SPY, XIU.TO, GLD; ts_momentum adds IEF.
- Every real-data test is counted in `journal/trials.csv` (the over-search counter). Never delete rows.
- Every look at 2018+ results is logged in `journal/test_period_looks.csv` (`run_lab.py --reason` does it). Log looks
  made any other way by hand. Never delete rows.
- Trades fill at the next day's close (`config.EXECUTION = "next_close"`). `execution="same_close"` exists only for the
  reports' "Timing cost" table; never use it to judge a strategy.
- `paper_trade.py` (engine `lab/paper.py`) is the local paper account. It only allows `buy_and_hold`
  of the 4-asset control mix until a strategy passes the full Skeptic Checklist, enforces every risk rule, refuses to
  run if its files are missing, edited or don't match git, and commits only its own files. Tessy runs it by hand on her
  PC; the tests use throwaway folders.
- The circuit breaker lives in `lab/breaker.py`: a fixed review period in backtests, a manual logged reset
  (`reset_circuit_breaker.py`) in paper mode. Agents must never run, script or suggest automating
  `reset_circuit_breaker.py`. Only Tessy resets it.
- New strategy ideas are pre-registered: the rules are frozen in `strategies/specs/<idea>.md` and committed on their
  own BEFORE any test-period look. Every report for the idea shows that spec's commit ID.
- Strategies may hold any weight from 0% to 100% (fractional positions); costs are charged on the size of each weight
  change. Always-partly-invested strategies use the sample-size rule written in their spec, not the 30-trade rule.
- Experiments are logged in `journal/` (see `journal/README.md` for the format).
- Run `python -m pytest` before opening a pull request. It must pass.
