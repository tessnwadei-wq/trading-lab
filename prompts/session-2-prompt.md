# Trading Lab: Cloud Session 2 prompt

**Before you paste:** commit and push everything in GitHub Desktop first (the real-data reports, the
price files in `data/csv/`, the updated `.gitignore` and this prompt file). Then start a new cloud
session on `trading-lab` and paste everything below the line.

---

This is session 2 of my Trading Lab. Read `CLAUDE.md`, `README.md` and the latest reports in `reports/`
before starting. Follow all the rules in CLAUDE.md. I'm still a beginner, so explain in plain English.

## Where we are

- Session 1 built the backtester, the Skeptic and two example strategies. It's merged.
- I ran it on my PC with **real Yahoo Finance data**. The price files are now committed in `data/csv/`
  (SPY, XIU.TO, GLD, CAD_X), so use them. This environment may not be able to download data.
- Real results: every strategy failed only check 3 (Costs). The 200-day rule on SPY turned $1 into
  $4.95 vs $9.49 for buy-and-hold, with a worst fall of -23% vs -55%. Win rates were 22-28%.

## This session's work, in priority order

Work through these in order. If you run short of time, stop at a clean point after any numbered item,
make sure the tests pass, and open the PR with what's done. Say clearly what's left.

### 1. Keep the data current
- `data/csv/` is now the main data source and is committed to git.
- Add `python run_lab.py --refresh`: it re-downloads every ticker and **overwrites the files in
  `data/csv/`** (right now a CSV there always wins, so without this the data would go stale).
- Update the README "how to run" section to explain it.

### 2. Cash should earn interest
- Right now the backtest assumes cash earns 0%. In reality, money waiting in cash earns roughly the
  short-term Treasury bill rate.
- Add the 13-week US T-bill yield (Yahoo ticker `^IRX`, saved as `data/csv/IRX.csv`) and credit it
  daily whenever a strategy is in cash. Use it for both SPY and XIU.TO, and write that simplification down.
- If IRX data isn't available in this environment, make the code handle it with a clear warning, and
  tell me the exact command to run on my PC to fetch it.
- Compute the Sharpe ratio on returns **above** the cash rate (the standard way), and explain the change
  in LEARNING.md.

### 3. A fairer comparison: the "same-risk mix"
- My concern: the 200-day rule may just be the same as owning less stock. It moved about 60% as much
  as the index.
- Add a benchmark called **same-risk mix**: X% in the asset and the rest in cash (earning interest),
  where X is chosen so its volatility matches the strategy's. Calculate X on training data only
  (2005-2017), then apply it to the test period, so there's no look-ahead.
- Add it to the metrics table, equity chart and checklist.

### 4. Clearer Skeptic messages, plus one new check
- Rename check 3 to **"Beats the simple alternatives"**: after costs, the strategy must beat buy-and-hold,
  the broad index and the same-risk mix. Report the double-costs result as well.
- Every message must say **exactly which comparison failed, and by how much**. For example: "Beat
  buy-and-hold at normal costs (0.91 vs 0.84) but not the broad index at double costs (0.81 vs 0.82)."
- Add a **WARN** level (PASS / WARN / FAIL). A WARN is shown in the report but doesn't fail the strategy
  on its own.
- New check: **consistency**. WARN if the test-period Sharpe is very different from training in either
  direction (e.g. XIU.TO went 0.25 → 0.91). Explain that a big swing usually means the period drove the
  result rather than a steady edge.

### 5. Risk rules in code (phase 2)
- Build a small **portfolio** backtest that runs one strategy across several assets at once: SPY, XIU.TO
  and GLD.
- Enforce the CLAUDE.md risk rules:
  - at most 1% of the account at risk per trade (define "risk" using a volatility-based exit distance,
    and explain the choice)
  - at most 20% of the account in any one position
  - at most 5 open positions
  - a 10% drawdown circuit breaker: after a 10% fall from the account's peak, open no new trades,
    and log it and flag it in the report
- The risk-manager agent reviews the result, and the report gets a **"Risk manager"** section: how often
  each rule limited a trade, and whether the circuit breaker triggered and when.
- Run `ma_trend` as a portfolio and produce `reports/portfolio_ma_trend/report.md`, with the full
  Skeptic Checklist against buy-and-hold of an equal-weight SPY/XIU.TO/GLD portfolio.

### 6. Automatic tests on GitHub
- Add a GitHub Actions workflow that runs the tests on every pull request (using committed data or
  demo data, never the network).

### 7. Over-search counter (only if time allows)
- Keep a running count of every parameter combination and idea ever tested in `journal/trials.csv`.
- Show the count in each report, with a simple plain-English "the more you search, the more a winner is
  likely luck" adjustment (the deflated Sharpe idea, simplified).

## Finish
- All tests pass, including new tests for cash interest, the same-risk mix and each risk rule.
- Regenerate all reports with the real data in `data/csv/`. Add new journal entries and don't
  overwrite old ones.
- Update LEARNING.md with: risk-free rate, excess return, same-risk benchmark, volatility-based position
  sizing, circuit breaker, and WARN vs FAIL.
- Open a pull request with a plain-English summary of the real results, a **"What I learned"**
  section, and a suggested plan for session 3.
