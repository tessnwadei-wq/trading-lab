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
COLORS = {"strategy": "#2a78d6", "buy_hold": "#eb6834", "index": "#1baf7a"}
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"

WHO_LABEL = {"strategy": "Strategy", "strategy_2x": "Strategy (double costs)",
             "buy_hold": "Buy-and-hold", "index": "Broad index (SPY)"}
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
    for who in ("index", "buy_hold", "strategy"):
        eq = ev.results[("full", who)].equity
        ax.plot(eq.index, eq, color=COLORS[who], linewidth=1.6, label=WHO_LABEL[who])
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
        ax.plot(dd.index, dd, color=COLORS[who], linewidth=1.3, label=WHO_LABEL[who])
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
    lines = ["| Period | Who | CAGR | Sharpe | Max drawdown | Volatility | Trades | Win rate | Time in market |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for p in ("train", "test", "full"):
        for who in ("strategy", "strategy_2x", "buy_hold", "index"):
            r = ev.metrics.loc[(p, who)]
            lines.append(f"| {PERIOD_LABEL[p]} | {WHO_LABEL[who]} | {_pct(r.cagr)} | {r.sharpe:.2f} | "
                         f"{_pct(r.max_drawdown)} | {_pct(r.volatility)} | {int(r.n_trades)} | "
                         f"{_pct(r.win_rate, 0) if who.startswith('strategy') else '-'} | {_pct(r.time_in_market, 0)} |")
    return "\n".join(lines)


def regime_md(ev: AssetEvaluation) -> str:
    lines = ["| Stress period | Strategy return | Buy-and-hold return | Strategy worst fall | Buy-and-hold worst fall |",
             "|---|---:|---:|---:|---:|"]
    for r in ev.regimes.itertuples():
        lines.append(f"| {r.period} | {_pct(r.strategy_return)} | {_pct(r.buy_hold_return)} | "
                     f"{_pct(r.strategy_max_dd)} | {_pct(r.buy_hold_max_dd)} |")
    return "\n".join(lines)


def checklist_md(ev: AssetEvaluation) -> str:
    icon = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "NEEDS MORE DATA": "⚠️ NEEDS MORE DATA"}
    lines = ["| # | Check | Result | What the skeptic found |", "|---|---|---|---|"]
    for c in ev.checks:
        lines.append(f"| {c.number} | {c.name} | {icon[c.status]} | {c.finding} |")
    lines.append(f"| 8 | **Verdict** | **{icon[ev.verdict]}** | {ev.reason} |")
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
# The full report
# --------------------------------------------------------------------------------------
def write_report(strategy, evaluations: list[AssetEvaluation], overall: str, sources: dict,
                 all_prices: dict, extra_md: str = "") -> Path:
    out_dir = REPORTS_DIR / strategy.name
    out_dir.mkdir(parents=True, exist_ok=True)
    is_demo = any(e.is_demo for e in evaluations)

    md = [f"# Strategy report: `{strategy.name}`", ""]
    if is_demo:
        md += [DEMO_BANNER, ""]
    md += [f"*Generated {date.today().isoformat()} by `python run_lab.py`.*", "",
           f"**Rule:** {strategy.description}", "",
           "**Parameters used:** " + "; ".join(f"{e.ticker}: `{e.strategy_label}`" for e in evaluations), "",
           f"**Overall verdict: {overall}**", "",
           "| Asset | Verdict | Why |", "|---|---|---|"]
    for ev in evaluations:
        md.append(f"| {ev.ticker} | **{ev.verdict}** | {ev.reason} |")
    md += ["", "**Ground rules applied:** costs of "
           f"{config.COMMISSION:.2%} commission + {config.SLIPPAGE:.2%} slippage on every buy and every sell; "
           "decisions made at the close and acted on the next trading day; parameters chosen on 2005-2017 only; "
           "2018+ used once as the out-of-sample test.", "",
           "**Data sources:** " + "; ".join(f"{t}: {s}" for t, s in sources.items()), ""]
    if extra_md:
        md += [extra_md, ""]

    for ev in evaluations:
        t = ev.ticker.replace("=", "_")
        equity_chart(ev, out_dir / f"{t}_equity.png")
        drawdown_chart(ev, out_dir / f"{t}_drawdown.png")
        sensitivity_chart(ev, out_dir / f"{t}_sensitivity.png")
        md += [f"## {ev.ticker}: {config.ASSET_NAMES.get(ev.ticker, '')}", "",
               "### Skeptic Checklist", "", checklist_md(ev), "",
               "### Equity curve", "",
               f"![{ev.ticker} equity curve]({t}_equity.png)", "",
               "### Drawdown", "", f"![{ev.ticker} drawdown]({t}_drawdown.png)", "",
               "### Metrics", "", metrics_table(ev), "",
               "### Parameter sensitivity (training data only)", "",
               "Each cell re-runs the strategy with different settings on 2005-2017 data and shows its Sharpe "
               "ratio. A robust idea looks like a smooth hill; an overfit one looks like a lone bright spot.", "",
               f"![{ev.ticker} sensitivity]({t}_sensitivity.png)", "",
               "### Stress periods", "", regime_md(ev), ""]

    md += [markets_section(all_prices), "",
           "---", "*How to read the numbers: see [LEARNING.md](../../LEARNING.md).*", ""]
    path = out_dir / "report.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path
