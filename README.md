# Trading Lab

A personal, rules-based **trading research lab** for learning. It tests trading rules on past prices
("backtesting") and then tries hard to prove the results are luck (the "Skeptic").

**No live trading. No real money. No broker connections.** See [CLAUDE.md](CLAUDE.md) for the project rules.

## What's in here (in plain English)

| Folder / file | What it is |
|---|---|
| `run_lab.py` | The one command you run. Loads prices, tests every strategy, writes reports. |
| `lab/data.py` | Gets daily prices (Yahoo Finance → Stooq → your own CSV files) and caches them. |
| `lab/backtest.py` | The simulator: "if we'd followed this rule, what would have happened?" Includes trading costs. |
| `lab/metrics.py` | Scorecard numbers: yearly growth, worst fall, Sharpe ratio, win rate, etc. |
| `lab/skeptic.py` | Runs the 8-point Skeptic Checklist and gives a PASS / FAIL / NEEDS MORE DATA verdict. |
| `lab/report.py` | Writes `reports/<strategy>/report.md` with charts. |
| `lab/config.py` | The ground rules as numbers: costs, the 2018 train/test split, the assets. |
| `strategies/` | One file per trading idea. `ma_trend.py` is the simple example; `overfit_demo.py` shows what *not* to do. |
| `reports/` | The generated reports. Start here to see results. |
| `journal/` | A diary of every experiment: idea, result, verdict, lesson. |
| `tests/` | Automatic checks that the lab itself works (especially that nothing "peeks at the future"). |
| `LEARNING.md` | Glossary: every concept explained for a beginner. |
| `.claude/agents/` | Instructions for five AI helper roles: researcher, quant-coder, skeptic, risk-manager, journal-keeper. |

## ⚠️ About the reports currently in `reports/`
The cloud computer that built this lab was **blocked from downloading prices**, so the reports in this
first version were made with **synthetic (made-up) practice data**. Every report says so in a banner at the top.
They prove the machinery works, but they say nothing about real markets. Follow the steps below
on your own computer to produce real reports. It takes one command once Python is installed.

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
   It downloads prices (first run only; they're cached in `data\cache\`), tests both strategies and
   prints each verdict. Takes under a minute.
7. **Read the results.** Open `reports\ma_trend\report.md` and `reports\overfit_demo\report.md`.
   The easiest way to view them nicely: open the folder in [VS Code](https://code.visualstudio.com/)
   and press `Ctrl+Shift+V` on the report, or push to GitHub and view them there.
8. **Check the lab still works** (do this after any code change):
   ```powershell
   python -m pytest
   ```
   You want to see `passed` and no `failed`.

Useful options:
```powershell
python run_lab.py --strategy ma_trend   # just one strategy
python run_lab.py --refresh             # re-download prices (e.g. to get the latest days)
python run_lab.py --demo                # practice mode with made-up data
```
(On Mac/Linux it's the same, except `python3 -m venv .venv` and `source .venv/bin/activate`.)

## If the download fails

`run_lab.py` tries Yahoo Finance, then Stooq. If both fail (a firewall, or Yahoo changing its site),
it tells you exactly which file it needs. You can then download CSV files yourself and drop them into `data\csv\`.
Your CSV always takes priority over downloads.

| Asset | Save as | Where to get it |
|---|---|---|
| S&P 500 ETF | `data\csv\SPY.csv` | <https://stooq.com/q/d/l/?s=spy.us&i=d> (should download a CSV; if Stooq shows a message instead, use the Yahoo/Investing.com route in the last row) |
| Gold ETF | `data\csv\GLD.csv` | <https://stooq.com/q/d/l/?s=gld.us&i=d> |
| USD/CAD | `data\csv\CAD_X.csv` | <https://stooq.com/q/d/l/?s=usdcad&i=d> |
| TSX 60 ETF | `data\csv\XIU_TO.csv` | Yahoo Finance: search **XIU.TO** → *Historical Data* → set dates from 2005 → *Download*. If there's no download button, use Investing.com (free account): search "iShares S&P/TSX 60", *Historical Data*, *Daily*, *Download*. |

Rules for the files:
- The name must match exactly (note `CAD_X.csv` and `XIU_TO.csv` use an underscore).
- The file needs a **Date** column and a **Close**, **Adj Close** or **Price** column. Yahoo, Stooq and
  Investing.com formats are all understood. If there's an "Adj Close" column it's used, because it includes dividends.
- If a CSV has no dividend adjustment, buy-and-hold will look a bit worse than reality (~1.5–3% a year for stock ETFs).
  Note that in the report.

Then just run `python run_lab.py` again.

## How a result becomes "approved"
Only by passing **every** item on the Skeptic Checklist in [CLAUDE.md](CLAUDE.md), on real data,
including the untouched 2018+ test period. Most ideas fail. That's the point of the lab.

## Collaborating
See [CONTRIBUTING.md](CONTRIBUTING.md). Ideas go in through the **Strategy idea** issue form.
