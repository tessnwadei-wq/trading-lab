"""
Run the whole lab: load data, backtest each strategy, run the skeptic, write reports.

Usage:
    python run_lab.py                         # all strategies, real data
    python run_lab.py --strategy ma_trend     # one strategy
    python run_lab.py --refresh               # re-download prices instead of using the cache
    python run_lab.py --demo                  # made-up practice data (when downloads fail)
"""

from __future__ import annotations

import argparse
import sys

from lab import config
from lab.data import DataUnavailable, load_all
from lab.report import write_report
from lab.skeptic import evaluate, overall_verdict
from strategies.ma_trend import MATrend
from strategies.overfit_demo import OverfitDemo

# Register new strategies here.
STRATEGIES = {
    "ma_trend": MATrend,
    "overfit_demo": OverfitDemo,
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Trading Lab: backtest + skeptic")
    ap.add_argument("--strategy", choices=list(STRATEGIES), help="run only this strategy")
    ap.add_argument("--demo", action="store_true", help="use synthetic practice data")
    ap.add_argument("--refresh", action="store_true", help="re-download prices")
    args = ap.parse_args(argv)

    tickers = config.TRADED_ASSETS + config.COMPARISON_ASSETS
    print("Loading prices...")
    try:
        prices, sources = load_all(tickers, demo=args.demo, refresh=args.refresh)
    except DataUnavailable as exc:
        print(f"\nDATA PROBLEM\n{exc}")
        return 1
    for t in tickers:
        p = prices[t]
        print(f"  {t:7s} {len(p):5d} days  {p.index[0].date()} to {p.index[-1].date()}  ({sources[t]})")

    names = [args.strategy] if args.strategy else list(STRATEGIES)
    for name in names:
        print(f"\n=== {name} ===")
        evaluations, notes = [], []
        for ticker in config.TRADED_ASSETS:
            strategy = STRATEGIES[name]()
            # fit() may choose parameters, and is only EVER given training data.
            fitted = strategy.fit(prices[ticker].loc[:config.TRAIN_END])
            if getattr(fitted, "search_results", None) is not None:
                notes.append(search_note(ticker, fitted))
            ev = evaluate(fitted, prices[ticker], prices[config.BROAD_INDEX], ticker, is_demo=args.demo)
            evaluations.append(ev)
            print(f"  {ticker:7s} {fitted.label():60s} -> {ev.verdict}")
            for c in ev.checks:
                print(f"      {c.number}. {c.name:22s} {c.status}")
        overall = overall_verdict(evaluations)
        path = write_report(fitted, evaluations, overall, sources, prices, extra_md="\n\n".join(notes))
        print(f"  Overall: {overall}. Report: {path.relative_to(path.parents[2])}")
    return 0


def search_note(ticker, fitted) -> str:
    """Explain a parameter search in the report, so the number of tries is never hidden."""
    table = fitted.search_results
    best, median = table.sharpe.iloc[0], table.sharpe.median()
    return (f"**Parameter search on {ticker} (training data only):** tried **{len(table):,} combinations** "
            f"and kept the best: `{fitted.label()}`, training Sharpe {best:.2f}. The median combination "
            f"scored {median:.2f}. Picking the top of {len(table):,} tries almost guarantees a lucky winner; "
            "the question is whether it holds up in 2018+.")


if __name__ == "__main__":
    sys.exit(main())
