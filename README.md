# Trading Lab

A personal, rules-based **trading research lab** for learning. It tests trading rules on past prices
("backtesting") and then tries hard to prove the results are luck (the "Skeptic").

**No live trading. No real money. No broker connections.** See [CLAUDE.md](CLAUDE.md) for the project rules.

## What's in here (in plain English)

| Folder / file | What it is |
|---|---|
| `run_lab.py` | The one command you run. Loads prices, tests every strategy, writes reports. |
| `data/csv/` | **The price files the lab uses** (SPY, XIU_TO, GLD, CAD_X and IRX), committed to git so everyone gets the same numbers. |
| `lab/data.py` | Reads `data/csv/`; downloads a missing file (Yahoo Finance → Stooq) and re-downloads everything with `--refresh`. |
| `lab/cash.py` | Interest on cash: the T-bill rate earned whenever a strategy is out of the market. |
| `lab/backtest.py` | The simulator: "if we'd followed this rule, what would have happened?" Includes trading costs and cash interest. Decisions made at a day's close are traded at the **next** day's close. |
| `lab/portfolio.py` | Phase 2: one strategy on several assets as one account, with the CLAUDE.md risk rules enforced. |
| `lab/breaker.py` | The drawdown circuit breaker. In a backtest it assumes a 21-trading-day review; in paper trading it waits for a manual reset. |
| `reset_circuit_breaker.py` | The manual reset for paper trading (a later phase): `--who` and `--reason` are required and every reset is logged. |
| `lab/metrics.py` | Scorecard numbers: yearly growth, worst fall, Sharpe ratio (above the cash rate), win rate, etc. |
| `lab/skeptic.py` | Runs the Skeptic Checklist (PASS / WARN / FAIL per check) and gives a PASS / FAIL / NEEDS MORE DATA verdict. |
| `lab/trials.py` | The over-search counter: how many things the lab has tried (`journal/trials.csv`), the "luck bar", and every look at the 2018+ test period (`journal/test_period_looks.csv`). |
| `lab/report.py` | Writes `reports/<strategy>/report.md` with charts. |
| `lab/config.py` | The ground rules as numbers: costs, the 2018 train/test split, the assets. |
| `strategies/` | One file per trading idea. `ma_trend.py` is the simple example; `overfit_demo.py` shows what *not* to do. |
| `reports/` | The generated reports. Start here to see results. |
| `journal/` | A diary of every experiment: idea, result, verdict, lesson. |
| `tests/` | Automatic checks that the lab itself works (especially that nothing "peeks at the future"). |
| `.github/workflows/tests.yml` | Runs the tests automatically on GitHub for every pull request (offline, never downloads). |
| `LEARNING.md` | Glossary: every concept explained for a beginner. |
| `.claude/agents/` | Instructions for five AI helper roles: researcher, quant-coder, skeptic, risk-manager, journal-keeper. |

## About the data
Since session 2 the price files live in `data/csv/` **and are committed to git**, so the reports can be
regenerated anywhere (including on GitHub's test computers) without downloading anything. The files hold
dividend-adjusted closing prices from Yahoo Finance, from January 2005. `IRX.csv` is different: it's the
13-week US T-bill interest rate in % a year, which the lab uses as the interest earned on cash.

The files don't update themselves. To bring them up to date, run `python run_lab.py --refresh` (below), look at
the new reports, and commit the changed files in `data/csv/` so everyone gets the new data.

## How to run it on Windows (step by step)

You only do steps 1–4 once.

1. **Install Python.** Go to <https://www.python.org/downloads/> and download Python 3.11 or newer.
   Run the installer and **tick "Add python.exe to PATH"** on the first screen, then click *Install Now*.
2. **Get the code.** Either install [GitHub Desktop](https://desktop.github.com/) and use *File → Clone repository*,
   or on the GitHub page click the green **Code** button → **Download ZIP** and unzip it (e.g. to `Documents\trading-lab`).
3. **Open a terminal in the folder.** In File Explorer, open the `trading-lab` folder, click the address bar,
   type `powershell` and press Enter. A blue/black window opens, already "inside" the folder.
4. **Set up a private Python environment and install the tools** (copy each line, paste with right-click, press Enter):
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   If step 2 of that complains about "running scripts is disabled", run this once and try again:
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (answer `Y`).

Every time after that:

5. **Activate the environment** (you'll see `(.venv)` at the start of the line):
   ```powershell
   .venv\Scripts\activate
   ```
6. **Run the lab:**
   ```powershell
   python run_lab.py
   ```
   It reads the prices in `data\csv\`, tests every strategy (plus the multi-asset portfolio) and
   prints each verdict. Takes under a minute.
7. **Read the results.** Open `reports\ma_trend\report.md`, `reports\overfit_demo\report.md` and
   `reports\portfolio_ma_trend\report.md`.
   The easiest way to view them nicely: open the folder in [VS Code](https://code.visualstudio.com/)
   and press `Ctrl+Shift+V` on the report, or push to GitHub and view them there.
8. **Check the lab still works** (do this after any code change):
   ```powershell
   python -m pytest
   ```
   You want to see `passed` and no `failed`.

Useful options:
```powershell
python run_lab.py --strategy ma_trend            # just one strategy
python run_lab.py --strategy portfolio_ma_trend  # just the SPY + XIU.TO + GLD portfolio with risk rules
python run_lab.py --refresh                      # re-download EVERY price file, then run
python run_lab.py --demo                         # practice mode with made-up data
python run_lab.py --reason "why I'm looking"     # recorded in journal/test_period_looks.csv
```

**Every real-data run is a look at the test period.** The reports show 2018+ results, and the rules say those
should be seen once per idea. So each run is logged in `journal/test_period_looks.csv` with the date and your
`--reason`, and each report shows how many looks its idea has had. Re-running with nothing changed gives the same
numbers and isn't counted twice. Commit that file along with the reports.

**When trades happen.** A strategy decides at a day's closing price and the lab trades at the *next* day's close
(you can't trade at a closing price you've only just seen). Each report has a *Timing cost* table showing how much
rosier the results looked with the old "same close" timing.

**Keeping the data current with `--refresh`.** A normal run always uses the files already in `data\csv\`,
so without a refresh the data slowly goes stale. `--refresh` re-downloads every ticker (SPY, XIU.TO, GLD,
CAD=X and the ^IRX cash rate) and **overwrites** its file in `data\csv\`, then runs the lab as usual. If a
download fails, the old file is kept and you see a `WARNING`. After a refresh, commit the updated
`data\csv\` files (GitHub Desktop will list them as changed), so the reports and the files match.
Refreshing adds new days, and Yahoo sometimes revises old ones slightly, so small changes in old results
are normal. The 2018+ test period grows with every refresh.

**If the cash-rate file (`IRX.csv`) is missing**, the lab still runs but prints a warning, cash earns 0%, and
reports say so at the top. Fix it with `python run_lab.py --refresh`.
(On Mac/Linux it's the same, except `python3 -m venv .venv` and `source .venv/bin/activate`.)

## If the download fails

`run_lab.py` tries Yahoo Finance, then Stooq. If both fail (a firewall, or Yahoo changing its site),
it tells you exactly which file it needs. You can then download CSV files yourself and drop them into `data\csv\`.
A file in `data\csv\` is always used as-is (unless you pass `--refresh`).

| Asset | Save as | Where to get it |
|---|---|---|
| S&P 500 ETF | `data\csv\SPY.csv` | <https://stooq.com/q/d/l/?s=spy.us&i=d> (should download a CSV; if Stooq shows a message instead, use the Yahoo/Investing.com route in the last row) |
| Gold ETF | `data\csv\GLD.csv` | <https://stooq.com/q/d/l/?s=gld.us&i=d> |
| USD/CAD | `data\csv\CAD_X.csv` | <https://stooq.com/q/d/l/?s=usdcad&i=d> |
| 13-week T-bill rate (cash interest) | `data\csv\IRX.csv` | Yahoo Finance: search **^IRX** → *Historical Data* → from 2005 → *Download*. |
| TSX 60 ETF | `data\csv\XIU_TO.csv` | Yahoo Finance: search **XIU.TO** → *Historical Data* → set dates from 2005 → *Download*. If there's no download button, use Investing.com (free account): search "iShares S&P/TSX 60", *Historical Data*, *Daily*, *Download*. |

Rules for the files:
- The name must match exactly (note `CAD_X.csv` and `XIU_TO.csv` use an underscore; the older name `XIU.TO.csv` also works).
- The file needs a **Date** column and a **Close**, **Adj Close** or **Price** column. Yahoo, Stooq and
  Investing.com formats are all understood. If there's an "Adj Close" column it's used, because it includes dividends.
- If a CSV has no dividend adjustment, buy-and-hold will look a bit worse than reality (~1.5–3% a year for stock ETFs).
  Note that in the report.

Then just run `python run_lab.py` again.

## Automatic tests on GitHub
Every pull request runs `python -m pytest` on GitHub's computers (see the **Checks** tab on the pull request). A
green tick means the lab still works; a red cross means something broke. The tests never use the internet:
they use the committed files in `data/csv/` or made-up demo data.

## How a result becomes "approved"
Only by passing **every** item on the Skeptic Checklist in [CLAUDE.md](CLAUDE.md), on real data,
including the untouched 2018+ test period. Most ideas fail. That's the point of the lab.

## Collaborating
See [CONTRIBUTING.md](CONTRIBUTING.md). Ideas go in through the **Strategy idea** issue form.
