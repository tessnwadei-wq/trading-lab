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
3. Costs: does it still beat buy-and-hold after costs? At double costs?
4. Parameter sensitivity: do nearby parameter values also work, or only one "magic" value?
5. Sample size: how many trades? (Under 30 = not enough evidence.)
6. Drawdown: what's the worst peak-to-trough loss, and how long did recovery take?
7. Regime check: results in different periods (e.g. 2008, 2020, 2022).
8. Verdict: PASS / FAIL / NEEDS MORE DATA, with one plain-English sentence why.

## Risk rules (enforced in code from phase 2)

- Max 1% of account at risk per trade.
- Max 5 open positions; max 20% of account in any single position.
- If the account falls 10% from its peak, stop opening new trades and flag for review.

## Communication

- Every pull request includes a "What I learned" section explaining new concepts for a beginner.
- Update LEARNING.md (glossary) whenever a new concept appears.
- Keep code simple and well commented over clever.

## Where things live (for agents)

- `lab/` is the engine: data, backtest, metrics, skeptic, report. `strategies/` holds one file per strategy.
- `python run_lab.py` runs every strategy end to end and writes `reports/<strategy>/report.md`.
- The data split and cost defaults live in `lab/config.py`. Change them there, nowhere else.
- Experiments are logged in `journal/` (see `journal/README.md` for the format).
- Run `python -m pytest` before opening a pull request. It must pass.
