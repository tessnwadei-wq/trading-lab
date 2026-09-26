"""
Writes a markdown report plus PNG charts for one strategy into reports/<strategy>/.

Markdown (.md) is plain text with light formatting; GitHub shows it nicely, and you can
open it in any text editor or in VS Code's preview.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw straight to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from lab import config
from lab.metrics import drawdown_series, max_drawdown_info
from lab.skeptic import AssetEvaluation

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"

# Chart colours: a colour-blind-safe set, one fixed colour per role, same in every chart.
# (Checked with a colour-vision-deficiency validator; every line also gets an end label.)
COLORS = {"strategy": "#2a78d6", "buy_hold": "#eb6834", "index": "#1baf7a", "mix": "#eda100"}
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"

WHO_LABEL = {"strategy": "Strategy", "strategy_2x": "Strategy (double costs)",
             "buy_hold": "Buy-and-hold", "index": "Broad index (SPY)", "mix": "Same-risk mix"}


def who_label(ev: AssetEvaluation, who: str) -> str:
    if who == "buy_hold":
        return ev.benchmark_name[0].upper() + ev.benchmark_name[1:]
    if who == "mix":
        return f"Same-risk mix ({ev.mix_weight:.0%} in, {1 - ev.mix_weight:.0%} cash)"
    return WHO_LABEL[who]
PERIOD_LABEL = {"train": "Train 2005-2017", "test": "Test 2018+", "full": "Full period"}

DEMO_BANNER = (
    "> **⚠️ DEMO DATA: these numbers are NOT real market results.**\n"
    "> Real price downloads were blocked where this report was generated, so the lab ran on\n"
    "> made-up practice prices (`lab/synthetic.py`). The report shows how the tools work; it says\n"
    "> nothing about how this strategy performs in real markets. Re-run `python run_lab.py` with\n"
    "> real data (see README) before drawing any conclusion.\n"
)


# --------------------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------------------
def _style(ax, title):
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold")
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9)


def _shade_test(ax, start, end):
    """Grey background behind the out-of-sample test period, and fix the x-axis range."""
    ax.set_xlim(start, end)
    ax.axvspan(config.TEST_START, end, color="#efeee9", zorder=0)
    ax.text(config.TEST_START, 1.0, "  out-of-sample test →", transform=ax.get_xaxis_transform(),
            va="top", fontsize=8, color=INK_2)


def _end_labels(ax, items):
    """Label each line at its right-hand end, nudging labels apart so they don't overlap."""
    items = sorted(items, key=lambda it: it[0].iloc[-1])
    last_y = None
    for series, text, color in items:
        y = series.iloc[-1]
        # On a log scale, "too close" means within ~12% of each other.
        dy = 9 if last_y is not None and y / last_y < 1.12 else 0
        _end_label(ax, series, text, color, dy)
        last_y = y


def _end_label(ax, series, text, color, dy=0):
    ax.annotate(text, (series.index[-1], series.iloc[-1]), xytext=(4, dy), textcoords="offset points",
                fontsize=8, color=INK, va="center")
    ax.plot(series.index[-1], series.iloc[-1], "o", color=color, markersize=4)


def equity_chart(ev: AssetEvaluation, path: Path):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    _style(ax, f"{ev.ticker}: growth of $1 (log scale, after costs)")
    labels = []
    for who in ("index", "buy_hold", "mix", "strategy"):
        eq = ev.results[("full", who)].equity
        ax.plot(eq.index, eq, color=COLORS[who], linewidth=1.6, label=who_label(ev, who))
        labels.append((eq, f"${eq.iloc[-1]:.2f}", COLORS[who]))
    _end_labels(ax, labels)
    ax.set_yscale("log")
    dollars = matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:g}")
    ax.yaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10, subs=(1, 2, 5)))
    ax.yaxis.set_major_formatter(dollars)
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    start, end = ev.periods["full"]
    _shade_test(ax, start - pd.Timedelta(days=60), end + pd.Timedelta(days=500))
    ax.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0, 0.93))
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def drawdown_chart(ev: AssetEvaluation, path: Path):
    fig, ax = plt.subplots(figsize=(9, 3.4))
    _style(ax, f"{ev.ticker}: drawdown (how far below the previous high)")
    for who in ("buy_hold", "strategy"):
        dd = drawdown_series(ev.results[("full", who)].equity)
        ax.plot(dd.index, dd, color=COLORS[who], linewidth=1.3, label=who_label(ev, who))
    ax.axhline(0, color=INK_2, linewidth=0.8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    start, end = ev.periods["full"]
    _shade_test(ax, start - pd.Timedelta(days=60), end + pd.Timedelta(days=60))
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def sensitivity_chart(ev: AssetEvaluation, path: Path):
    grid = ev.sensitivity
    fig, ax = plt.subplots(figsize=(1.0 + 0.85 * len(grid.columns), 1.2 + 0.42 * len(grid.index)))
    ax.figure.set_facecolor(SURFACE)
    vals = grid.to_numpy(dtype=float)
    im = ax.imshow(vals, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(grid.columns)), [f"{c:g}" for c in grid.columns], fontsize=9, color=INK_2)
    ax.set_yticks(range(len(grid.index)), [f"{r:g}" for r in grid.index], fontsize=9, color=INK_2)
    ax.set_xlabel(grid.columns.name, color=INK_2)
    ax.set_ylabel(grid.index.name, color=INK_2)
    lo, hi = np.nanmin(vals), np.nanmax(vals)
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            dark = (vals[i, j] - lo) / (hi - lo + 1e-9) > 0.6
            ax.text(j, i, f"{vals[i, j]:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if dark else INK)
    ri, ci = list(grid.index).index(ev.chosen[0]), list(grid.columns).index(ev.chosen[1])
    ax.add_patch(plt.Rectangle((ci - 0.5, ri - 0.5), 1, 1, fill=False, edgecolor=INK, linewidth=2.2))
    ax.set_title(f"{ev.ticker}: training Sharpe for nearby settings\n(black box = chosen)",
                 loc="left", fontsize=11, color=INK)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02).ax.tick_params(labelsize=8, colors=INK_2)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------------------
# Markdown helpers
# --------------------------------------------------------------------------------------
def _pct(x, d=1):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x * 100:.{d}f}%"


def metrics_table(ev: AssetEvaluation) -> str:
    lines = ["| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Avg. share invested |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for p in ("train", "test", "full"):
        for who in ("strategy", "strategy_2x", "buy_hold", "index", "mix"):
            r = ev.metrics.loc[(p, who)]
            lines.append(f"| {PERIOD_LABEL[p]} | {who_label(ev, who)} | {_pct(r.cagr)} | {r.sharpe:.2f} | "
                         f"{_pct(r.max_drawdown)} | {_pct(r.volatility)} | {int(r.n_trades)} | "
                         f"{_pct(r.win_rate, 0) if who.startswith('strategy') else '-'} | {_pct(r.time_in_market, 0)} |")
    return "\n".join(lines)


def regime_md(ev: AssetEvaluation) -> str:
    bh = who_label(ev, "buy_hold")
    lines = [f"| Stress period | Strategy return | {bh} return | Strategy worst fall | {bh} worst fall |",
             "|---|---:|---:|---:|---:|"]
    for r in ev.regimes.itertuples():
        lines.append(f"| {r.period} | {_pct(r.strategy_return)} | {_pct(r.buy_hold_return)} | "
                     f"{_pct(r.strategy_max_dd)} | {_pct(r.buy_hold_max_dd)} |")
    return "\n".join(lines)


def timing_md(ev: AssetEvaluation) -> list[str]:
    """The "Timing cost" section: same-close (old, optimistic) vs next-close (the lab's rule) execution."""
    t = ev.timing
    if t is None:
        return []
    lines = ["### Timing cost (when the trade happens)", "",
             "The lab decides at a day's close and trades at the **next** day's close. Before session 3 it traded "
             "at the *same* close it decided on, which you can't do in real life. This table shows the strategy "
             "both ways (normal costs). Only the next-close numbers are used by the Skeptic.", "",
             "| Period | Timing | CAGR | Sharpe | Max drawdown | Trades |", "|---|---|---:|---:|---:|---:|"]
    names = {"same_close": "Same close (old, optimistic)", "next_close": "**Next close (used)**"}
    for p in ("train", "test", "full"):
        for ex in ("same_close", "next_close"):
            r = t.loc[(p, ex)]
            lines.append(f"| {PERIOD_LABEL[p]} | {names[ex]} | {_pct(r.cagr)} | {r.sharpe:.2f} | "
                         f"{_pct(r.max_drawdown)} | {int(r.n_trades)} |")
    lines += ["", timing_sentence(ev), ""]
    return lines


def timing_sentence(ev: AssetEvaluation) -> str:
    """One plain-English sentence on what the honest timing changed (full period)."""
    old, new = ev.timing.loc[("full", "same_close")], ev.timing.loc[("full", "next_close")]
    d_cagr, d_sharpe = new.cagr - old.cagr, new.sharpe - old.sharpe
    if abs(d_cagr) < 0.0005 and abs(d_sharpe) < 0.005:
        return ("**What changed:** almost nothing: over the full period, trading a day later left yearly return "
                f"({_pct(new.cagr)}) and Sharpe ({new.sharpe:.2f}) about the same.")
    word = "flattered" if d_sharpe < 0 else "understated"
    return (f"**What changed:** over the full period, trading one close later moved yearly return from "
            f"{_pct(old.cagr)} to {_pct(new.cagr)} and Sharpe from {old.sharpe:.2f} to {new.sharpe:.2f}, so the old "
            f"same-close timing {word} this strategy by {abs(d_cagr) * 100:.1f} percentage points a year.")


def checklist_md(ev: AssetEvaluation) -> str:
    icon = {"PASS": "✅ PASS", "WARN": "⚠️ WARN", "FAIL": "❌ FAIL", "NEEDS MORE DATA": "❔ NEEDS MORE DATA"}
    lines = ["| # | Check | Result | What the skeptic found |", "|---|---|---|---|"]
    for c in ev.checks:
        lines.append(f"| {c.number} | {c.name} | {icon[c.status]} | {c.finding} |")
    lines.append(f"| {len(ev.checks) + 1} | **Verdict** | **{icon[ev.verdict]}** | {ev.reason} |")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# "How the markets differ" section
# --------------------------------------------------------------------------------------
def markets_section(prices: dict) -> str:
    closes = pd.DataFrame({t: p["Close"] for t, p in prices.items()})
    yearly = closes.resample("YE").last().pct_change().dropna(how="all")
    first_year = closes.apply(lambda s: s.dropna().index[0]).max().year
    yearly = yearly[yearly.index.year > first_year]
    daily = closes.pct_change()
    corr = daily.corr()["SPY"]

    lines = ["## How the markets differ", "",
             "The lab will eventually trade more than stocks, so here is how four very different "
             "markets behaved over the same years. Nothing here is traded yet.", "",
             "| Market | Average yearly return | Best year | Worst year | Worst drawdown | Moves with SPY (correlation) |",
             "|---|---:|---:|---:|---:|---:|"]
    for t in closes.columns:
        s = closes[t].dropna()
        eq = s / s.iloc[0]
        yr = yearly[t].dropna()
        lines.append(f"| {t}: {config.ASSET_NAMES.get(t, t)} | {_pct(yr.mean())} | "
                     f"{_pct(yr.max())} ({yr.idxmax().year}) | {_pct(yr.min())} ({yr.idxmin().year}) | "
                     f"{_pct(max_drawdown_info(eq)['max_dd'])} | {corr[t]:+.2f} |")

    lines += ["", "<details><summary>Year-by-year returns (click to open)</summary>", "",
              "| Year | " + " | ".join(closes.columns) + " |",
              "|---|" + "---:|" * len(closes.columns)]
    for idx, row in yearly.iterrows():
        lines.append(f"| {idx.year} | " + " | ".join(_pct(v) for v in row) + " |")
    lines += ["", "</details>", "",
              "**Reading this in plain English:**", "",
              "- **Correlation** runs from -1 to +1. +1 means \"always moves the same way as SPY\", 0 means "
              "\"no relationship\", -1 means \"always moves the opposite way\". Something with low or negative "
              "correlation can cushion a stock portfolio when stocks fall.",
              f"- **Canadian vs US stocks** (XIU.TO vs SPY, correlation {corr['XIU.TO']:+.2f}): they tend to rise "
              "and fall together, so holding both diversifies less than it seems.",
              f"- **Gold** (GLD, correlation {corr['GLD']:+.2f}): largely goes its own way. It's a commodity with "
              "no earnings or dividends; people buy it as a store of value, often when they're worried.",
              f"- **USD/CAD** (CAD=X, correlation {corr['CAD=X']:+.2f}): this is a *price of a currency*, not an "
              "investment that grows. When it goes UP, one US dollar buys more Canadian dollars (the CAD got "
              "weaker). It usually moves much less than stocks, which is why forex traders often use leverage "
              "(borrowed money), and that's where forex gets dangerous.",
              "- **Worst drawdown** is the biggest peak-to-bottom fall. It's the number that tells you how much "
              "pain you'd have had to sit through.", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# Over-search counter and risk manager sections
# --------------------------------------------------------------------------------------
def trials_section(evaluations: list[AssetEvaluation], idea: str, is_demo: bool) -> str:
    from lab import trials

    lab_total = trials.totals()
    lines = ["## Over-search counter", "",
             "The more things you try, the more likely your best result is luck. The lab counts every "
             "parameter combination and idea ever tested on real data in "
             "[`journal/trials.csv`](../../journal/trials.csv).", "",
             f"**Lab-wide so far:** {lab_total['ideas']} ideas, {lab_total['configurations']:,} parameter "
             "combinations tested.", ""]
    if is_demo:
        return "\n".join(lines + ["*(Demo data: practice runs aren't counted and no luck check is made.)*", ""])
    lines += ["| Tested on | Tries for this idea | Training Sharpe | Luck bar (this idea) | Rough chance it's real | "
              "Luck bar (whole lab) |", "|---|---:|---:|---:|---:|---:|"]
    for ev in evaluations:
        s, e = ev.periods["train"]
        years = (pd.Timestamp(e) - pd.Timestamp(s)).days / 365.25
        n = max(trials.trials_for(idea, ev.ticker), 1)
        sr = ev.metrics.loc[("train", "strategy"), "sharpe"]
        lines.append(f"| {ev.ticker} | {n:,} | {sr:.2f} | {trials.luck_bar(n, years):.2f} | "
                     f"{trials.chance_real(sr, n, years):.0%} | "
                     f"{trials.luck_bar(max(lab_total['configurations'], 1), years):.2f} |")
    lines += ["", "**Reading this:** the *luck bar* is the Sharpe ratio the luckiest of that many *useless* "
              "strategies would be expected to show over the training years, by chance alone. A result below "
              "its bar is what luck alone would produce. *Rough chance it's real* compares the training Sharpe "
              "with the bar (a simplified \"deflated Sharpe ratio\"; see LEARNING.md). The whole-lab bar is "
              "stricter: it asks \"if this were the best of everything the lab ever tried, would it stand out?\"", ""]
    return "\n".join(lines)


def looks_section(idea: str, is_demo: bool) -> str:
    """How many times this idea's 2018+ test results have been seen (journal/test_period_looks.csv)."""
    from lab import trials

    if is_demo:
        return ""
    looks = trials.looks_for(idea)
    lines = ["## Test-period looks", "",
             f"The 2018+ test period should be looked at **once** per idea. This idea's test results have been seen "
             f"**{len(looks)} time{'s' if len(looks) != 1 else ''}** (every look is logged in "
             "[`journal/test_period_looks.csv`](../../journal/test_period_looks.csv); re-running with nothing "
             "changed isn't a new look).", "",
             "| # | Date | Why |", "|---:|---|---|"]
    for i, r in enumerate(looks, 1):
        lines.append(f"| {i} | {r['date']} | {r['reason']} |")
    if len(looks) > 1:
        lines += ["", "**Why this matters:** each extra look weakens the test a little. None of these looks was used to "
                  "choose parameters, but a result seen several times is no longer a completely fresh test. A strategy "
                  "that is changed *because* of what a look showed must be treated as a new idea."]
    return "\n".join(lines + [""])


def looks_line(idea: str, is_demo: bool) -> str:
    from lab import trials

    if is_demo:
        return ""
    n = len(trials.looks_for(idea))
    return (f"**Test-period (2018+) looks for this idea: {n}** "
            f"(this report included; details in *Test-period looks* below).")


def risk_manager_section(ev: AssetEvaluation) -> str:
    res = ev.results[("full", "strategy")]
    log = res.risk
    closed = res.trades[res.trades["closed"]]
    e = max(log.entries, 1)
    stops = closed[closed["reason"] == "stop"]
    lines = ["## Risk manager", "",
             "The portfolio enforces the CLAUDE.md risk rules in code (`lab/portfolio.py`). Numbers are for the "
             "full period at normal costs.", "",
             "| Rule | Setting | How often it limited a trade | Worst case seen |", "|---|---|---|---|",
             f"| Max risk per trade | A stopped-out trade should normally lose no more than "
             f"{config.MAX_RISK_PER_TRADE:.0%} of the account (costs included), even though the stop-sale fills a day "
             f"later. Stop: {config.STOP_ATR_MULTIPLE:g} × the {config.STOP_ATR_DAYS}-day average daily move below "
             f"entry; sized as if {config.STOP_FILL_BUFFER_MOVES:g} more moves away (the one-day buffer) | "
             f"Set the size of **{log.sized_by_risk_rule} of {log.entries}** entries ({log.sized_by_risk_rule / e:.0%}); "
             f"the stop closed {log.stop_exits} trades, **{log.stops_over_budget}** of them lost more than "
             f"{config.MAX_RISK_PER_TRADE:.0%} | Worst stop-out lost {-log.worst_stop_loss:.2%} of the account"
             + (f" (stop-outs averaged {-stops['loss_of_account'].mean():.2%})" if len(stops) else "")
             + f"; worst closed trade of any kind {-log.worst_trade_loss:.2%} |",
             f"| Max position size | No buy that would take a position above {config.MAX_POSITION_WEIGHT:.0%}. "
             f"Anything above {config.MAX_POSITION_WEIGHT:.0%} at a close is trimmed to {config.TRIM_BACK_TO:.0%} at the "
             f"next close. Alert above {config.POSITION_ALERT_WEIGHT:.0%} | Capped the size of **{log.sized_by_cap} of "
             f"{log.entries}** entries ({log.sized_by_cap / e:.0%}); trimmed a grown position {log.trims} times | "
             f"Largest position at any close: {log.max_position_weight:.1%} ({log.days_over_cap} position-days closed "
             f"above {config.MAX_POSITION_WEIGHT:.0%}, each trimmed at the next close); "
             f"**{len(log.alerts)}** alert{'s' if len(log.alerts) != 1 else ''} above {config.POSITION_ALERT_WEIGHT:.0%} |",
             f"| Max open positions | {config.MAX_OPEN_POSITIONS} | Blocked {log.blocked_by_max_positions} entries | "
             f"Most open at once: {log.max_open_positions} (only {len(res.weights.columns)} assets, so this rule "
             f"{'can never bind yet' if len(res.weights.columns) <= config.MAX_OPEN_POSITIONS else 'can bind'}) |",
             f"| Circuit breaker | Stop new trades after a {config.CIRCUIT_BREAKER_DRAWDOWN:.0%} fall from the peak "
             f"until a review (backtest assumption: the review takes {config.CIRCUIT_BREAKER_REVIEW_DAYS} trading days); "
             f"stop for good after a {config.CIRCUIT_BREAKER_HARD_STOP:.0%} fall from the all-time high | Blocked {log.blocked_by_breaker} "
             f"entries; triggered **{len(log.breaker_events)}** times; hard floor "
             f"{'**HIT on ' + str(log.hard_stop['tripped'].date()) + '**' if log.hard_stop else 'never hit'} | Worst fall: "
             f"{ev.metrics.loc[('full', 'strategy'), 'max_drawdown']:.1%} |", ""]
    if log.hard_stop:
        lines += [f"**🛑 FLAG FOR REVIEW: the hard floor was hit on {log.hard_stop['tripped'].date()} "
                  f"({log.hard_stop['drawdown']:.1%} from the all-time high). No new trades were opened after that.**", ""]
    if log.alerts:
        lines += [f"**⚠️ POSITION ALERT: a position ended the day above {config.POSITION_ALERT_WEIGHT:.0%} "
                  f"{len(log.alerts)} time{'s' if len(log.alerts) != 1 else ''}.** Each was trimmed to "
                  f"{config.TRIM_BACK_TO:.0%} at the next close.", "",
                  "| Day | Asset | Share of the account at the close |", "|---|---|---:|"]
        lines += [f"| {a['date'].date()} | {a['asset']} | {a['weight']:.1%} |" for a in log.alerts[:20]]
        if len(log.alerts) > 20:
            lines.append(f"| ... | {len(log.alerts) - 20} more | |")
        lines.append("")
    else:
        lines += [f"**Position alerts (above {config.POSITION_ALERT_WEIGHT:.0%} at a close): none.**", ""]
    if log.breaker_events:
        lines += ["**⚠️ FLAG FOR REVIEW: the circuit breaker triggered.**", "",
                  "| Triggered | Fall from peak | Trading resumed | How |", "|---|---:|---|---|"]
        for b in log.breaker_events:
            lines.append(f"| {b['tripped'].date()} | {b['drawdown']:.1%} | "
                         f"{b['resumed'].date() if b['resumed'] is not None else 'still paused at end of data'} | "
                         f"{b.get('resumed_by') or '-'} |")
        lines.append("")
    else:
        lines += [f"**Circuit breaker: never triggered.** The account never fell {config.CIRCUIT_BREAKER_DRAWDOWN:.0%} "
                  "from its peak.", ""]
    lines += ["**In plain English:** the 1% rule works by choosing the position size so that hitting the stop "
              "(plus the costs of buying and selling) loses about 1% of the account. Every order fills at the close "
              "*after* the decision, so a stopped-out price can keep falling for a day before the sale fills. The "
              f"**one-day buffer** allows for that: positions are sized as if the stop were "
              f"{config.STOP_FILL_BUFFER_MOVES:g} more average daily moves away (chosen from 2005-2017 data and "
              "common sense; see `STOP_FILL_BUFFER_MOVES` in `lab/config.py`). A big gap through the stop can still "
              "cost more than 1%, which is why the table counts stop-outs over budget. For these assets the room "
              "needed was usually under 5-7%, so the 1% rule would still have allowed a position bigger than 20%; "
              "the 20% cap was then the rule that actually set the size.", "",
              f"**Circuit breaker assumption (backtest only):** a person can't press \"reset\" inside a simulation, "
              f"so after a {config.CIRCUIT_BREAKER_DRAWDOWN:.0%} fall the backtest assumes a review of "
              f"**{config.CIRCUIT_BREAKER_REVIEW_DAYS} trading days** (about a month; `CIRCUIT_BREAKER_REVIEW_DAYS` in "
              "`lab/config.py`, chosen by common sense, not by looking at results), then resumes. In paper trading "
              "nothing restarts by itself: new trades stay blocked until **Tessy, in person,** runs `python "
              "reset_circuit_breaker.py --who <name> --reason \"...\"` and types `RESET` to confirm (plus an extra "
              "confirmation for the 20% hard floor). Agents never run, script or suggest automating it. Every reset "
              "is appended to `journal/circuit_breaker_resets.csv`, a log that can only be added to.", "",
              f"**Not yet tested on real data:** the {config.MAX_OPEN_POSITIONS}-position limit (only "
              f"{len(res.weights.columns)} assets so far){' and the circuit breaker (never triggered)' if not log.breaker_events else ''}. "
              "All the risk rules are also checked with made-up prices in `tests/test_portfolio.py` and "
              "`tests/test_breaker.py`.",
              "", f"![Portfolio exposure](portfolio_exposure.png)", ""]
    return "\n".join(lines)


def exposure_chart(ev: AssetEvaluation, path: Path):
    """Stacked area: share of the account in each asset over time (the rest is cash)."""
    w = ev.results[("full", "strategy")].weights
    fig, ax = plt.subplots(figsize=(9, 3.4))
    _style(ax, "Portfolio: share of the account in each asset (the rest is cash)")
    colors = [COLORS["strategy"], COLORS["buy_hold"], COLORS["index"], COLORS["mix"]]
    ax.stackplot(w.index, w.T.to_numpy(), labels=list(w.columns), colors=colors[:len(w.columns)],
                 edgecolor=SURFACE, linewidth=0.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_ylim(0, 1)
    start, end = ev.periods["full"]
    _shade_test(ax, start - pd.Timedelta(days=60), end + pd.Timedelta(days=60))
    ax.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0, 0.93), ncol=len(w.columns))
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------------------
# The full report
# --------------------------------------------------------------------------------------
def ground_rules(cash_note: str) -> str:
    return ("**Ground rules applied:** costs of "
            f"{config.COMMISSION:.2%} commission + {config.SLIPPAGE:.2%} slippage on every buy and every sell; "
            "each decision is made from a day's closing price and **traded at the next day's close** (so gains and "
            "losses start the day after that); "
            "parameters chosen on 2005-2017 only; 2018+ used once as the out-of-sample test. " + cash_note)


CASH_NOTE_OK = ("Money in cash earns the 13-week US T-bill rate (^IRX), used for every asset including XIU.TO "
                "(a simplification), and Sharpe ratios measure return *above* that cash rate.")
CASH_NOTE_MISSING = ("**⚠️ Cash interest data (^IRX) was missing, so cash earned 0% and Sharpe ratios use a 0% cash "
                     "rate.** Run `python run_lab.py --refresh` to fetch data/csv/IRX.csv.")


def _asset_section(ev: AssetEvaluation, out_dir: Path) -> list[str]:
    t = ev.ticker.replace("=", "_")
    equity_chart(ev, out_dir / f"{t}_equity.png")
    drawdown_chart(ev, out_dir / f"{t}_drawdown.png")
    sensitivity_chart(ev, out_dir / f"{t}_sensitivity.png")
    s, e = ev.periods["test"]
    mix_note = (f"**Same-risk mix:** {ev.mix_weight:.0%} in {'the assets (equal weights)' if ev.ticker == 'Portfolio' else ev.ticker}"
                f" and {1 - ev.mix_weight:.0%} in cash earning interest, rebalanced monthly. {ev.mix_weight:.0%} was chosen "
                "so its bumpiness (volatility) matched the strategy's **on 2005-2017 data only**, then frozen for 2018+. "
                f"In the test period its volatility was {ev.metrics.loc[('test', 'mix'), 'volatility']:.1%} vs the "
                f"strategy's {ev.metrics.loc[('test', 'strategy'), 'volatility']:.1%}. If the strategy can't earn more than "
                "this simple mix, it is just a complicated way of owning less of the asset.")
    return [f"### Skeptic Checklist", "", checklist_md(ev), "",
            mix_note, "",
            "### Equity curve", "",
            f"![{ev.ticker} equity curve]({t}_equity.png)", "",
            "### Drawdown", "", f"![{ev.ticker} drawdown]({t}_drawdown.png)", "",
            "### Metrics", "", metrics_table(ev), "",
            "*Sharpe = return above the cash rate, per unit of volatility. Avg. share invested = how much of the "
            "account was in the market on an average day.*", "",
            "### Parameter sensitivity (training data only)", "",
            "Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe "
            "ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.", "",
            f"![{ev.ticker} sensitivity]({t}_sensitivity.png)", "",
            "### Stress periods", "", regime_md(ev), ""] + timing_md(ev)


def _header(title: str, rule: str, evaluations, overall, sources, cash_ok: bool) -> list[str]:
    """Top of every report. `title` is also the idea's name in the journal."""
    is_demo = any(e.is_demo for e in evaluations)
    md = [f"# Strategy report: `{title}`", ""]
    if is_demo:
        md += [DEMO_BANNER, ""]
    md += [f"*Generated {date.today().isoformat()} by `python run_lab.py`.*", "",
           f"**Rule:** {rule}", "",
           "**Parameters used:** " + "; ".join(f"{e.ticker}: `{e.strategy_label}`" for e in evaluations), "",
           f"**Overall verdict: {overall}**", "",
           "| Tested on | Verdict | Why |", "|---|---|---|"]
    for ev in evaluations:
        md.append(f"| {ev.ticker} | **{ev.verdict}** | {ev.reason} |")
    if not is_demo:
        md += ["", looks_line(title, is_demo)]
    md += ["", ground_rules(CASH_NOTE_OK if cash_ok else CASH_NOTE_MISSING), "",
           "**Data sources:** " + "; ".join(f"{t}: {s}" for t, s in sources.items()), ""]
    return md


def write_report(strategy, evaluations: list[AssetEvaluation], overall: str, sources: dict,
                 all_prices: dict, extra_md: str = "", cash_ok: bool = True) -> Path:
    out_dir = REPORTS_DIR / strategy.name
    out_dir.mkdir(parents=True, exist_ok=True)
    is_demo = any(e.is_demo for e in evaluations)

    md = _header(strategy.name, strategy.description, evaluations, overall, sources, cash_ok)
    if extra_md:
        md += [extra_md, ""]
    for ev in evaluations:
        md += [f"## {ev.ticker}: {config.ASSET_NAMES.get(ev.ticker, '')}", ""] + _asset_section(ev, out_dir)

    md += [trials_section(evaluations, strategy.name, is_demo), "",
           looks_section(strategy.name, is_demo), "",
           markets_section(all_prices), "",
           "---", "*How to read the numbers: see [LEARNING.md](../../LEARNING.md).*", ""]
    path = out_dir / "report.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path


def write_portfolio_report(strategy, ev: AssetEvaluation, sources: dict, cash_ok: bool = True) -> Path:
    name = f"portfolio_{strategy.name}"
    out_dir = REPORTS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    assets = list(ev.results[("full", "strategy")].weights.columns)
    rule = (f"{strategy.description} Run on {', '.join(assets)} at the same time as one account, with the "
            "CLAUDE.md risk rules enforced (see *Risk manager* below).")
    md = _header(name, rule, [ev], ev.verdict, sources, cash_ok)
    md += ["**Compared with:** equal-weight buy-and-hold of " + "/".join(assets) + " (1/3 each, rebalanced "
           "monthly), the broad index (SPY), and a same-risk mix of that equal-weight basket plus cash. "
           "**Simplification:** XIU.TO is in Canadian dollars and its returns are added as if in the same currency "
           "(currency moves are ignored).", ""]
    exposure_chart(ev, out_dir / "portfolio_exposure.png")
    md += [risk_manager_section(ev), "", "## Portfolio results", ""] + _asset_section(ev, out_dir)
    md += [trials_section([ev], name, ev.is_demo), "",
           looks_section(name, ev.is_demo), "",
           "---", "*How to read the numbers: see [LEARNING.md](../../LEARNING.md).*", ""]
    path = out_dir / "report.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path
