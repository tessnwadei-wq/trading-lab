# Experiment journal

The lab's memory. **Every** experiment gets an entry, especially the failures: knowing how many ideas we've
tried is what stops us fooling ourselves with the one that got lucky.

- One file per experiment: `YYYY-MM-DD_<strategy>.md`
- One summary per month: `YYYY-MM_summary.md`
- Never delete or rewrite old entries. Add a dated correction underneath instead.

## Template

```markdown
# <strategy> (YYYY-MM-DD)

- **Idea:** one sentence. Source: ...
- **Data:** real / SYNTHETIC; assets; date range
- **Parameters:** ... (how they were chosen)
- **Result:** train vs test Sharpe, CAGR vs buy-and-hold, max drawdown, trades
- **Verdict:** PASS / FAIL / NEEDS MORE DATA: <skeptic's sentence, word for word>
- **Lesson:** what did we learn?
- **Report:** link
```

## Running tally

| # | Date | Strategy | Data | Verdict |
|---|---|---|---|---|
| 1 | 2026-09-26 | ma_trend | synthetic | FAIL |
| 2 | 2026-09-26 | overfit_demo | synthetic | FAIL |
| 3 | 2026-09-26 | ma_trend (lab v2: cash interest, same-risk mix) | real | FAIL |
| 4 | 2026-09-26 | overfit_demo (lab v2) | real | FAIL |
| 5 | 2026-09-26 | portfolio_ma_trend (SPY + XIU.TO + GLD, risk rules) | real | FAIL |
| 6 | 2026-09-26 | ma_trend (lab v3: next-close trade timing) | real | FAIL |
| 7 | 2026-09-26 | overfit_demo (lab v3: next-close timing; the search picked new winners) | real | FAIL |
| 8 | 2026-09-26 | portfolio_ma_trend (lab v3: next-close timing, manual-reset breaker) | real | FAIL |

Every parameter combination tested on real data is also counted in [`trials.csv`](trials.csv) (the over-search
counter). Add rows, never remove them; `run_lab.py` does this automatically.

Every time 2018+ results are seen, that "look" is logged in [`test_period_looks.csv`](test_period_looks.csv)
(date and reason; `python run_lab.py --reason "..."`). Looks made outside `run_lab.py` must be added by hand.
Circuit-breaker resets (paper trading, later) are logged in `circuit_breaker_resets.csv`.
