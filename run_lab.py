"""
Run the whole lab: load data, backtest each strategy, run the skeptic, write reports.

Usage:
    python run_lab.py                              # all strategies + portfolios, data from data/csv/
    python run_lab.py --strategy ma_trend          # one strategy
    python run_lab.py --strategy portfolio_ma_trend  # just the multi-asset portfolio version
    python run_lab.py --refresh                    # re-download every ticker, overwrite data/csv/, then run
    python run_lab.py --demo                       # made-up practice data (when downloads fail)
    python run_lab.py --reason "why I'm running it"  # recorded with each look at the 2018+ test period

Every real-data run writes 2018+ (test-period) results into the reports, so it counts as a LOOK at the
test period and is logged in journal/test_period_looks.csv with today's date and your --reason.
Re-running with nothing changed gives identical numbers and is not counted again.
"""

from __future__ import annotations

import argparse
import sys
import warnings

from lab import config, trials
from lab.cash import daily_cash_returns
from lab.data import DataUnavailable, load_all, load_prices
from lab.portfolio import evaluate_portfolio
from lab.report import write_portfolio_report, write_report
from lab.skeptic import evaluate, overall_verdict
from strategies.ma_trend import MATrend
from strategies.overfit_demo import OverfitDemo

# Register new strategies here.
STRATEGIES = {
    "ma_trend": MATrend,
    "overfit_demo": OverfitDemo,
}
PORTFOLIOS = {f"portfolio_{name}": name for name in config.PORTFOLIO_STRATEGIES}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Trading Lab: backtest + skeptic")
    ap.add_argument("--strategy", choices=list(STRATEGIES) + list(PORTFOLIOS), help="run only this one")
    ap.add_argument("--demo", action="store_true", help="use synthetic practice data")
    ap.add_argument("--refresh", action="store_true",
                    help="re-download every ticker and overwrite the files in data/csv/")
    ap.add_argument("--reason", default="",
                    help="why you're looking at the 2018+ test results (logged in journal/test_period_looks.csv)")
    args = ap.parse_args(argv)
    if not args.demo and not args.reason:
        print("NOTE: this run shows 2018+ test results, which counts as a look at the test period. Next time add "
              '--reason "..." so the log says why.')

    tickers = config.TRADED_ASSETS + config.COMPARISON_ASSETS
    print("Re-downloading prices into data/csv/..." if args.refresh else "Loading prices...")
    try:
        prices, sources = load_all(tickers, demo=args.demo, refresh=args.refresh)
    except DataUnavailable as exc:
        print(f"\nDATA PROBLEM\n{exc}")
        return 1
    for t in tickers:
        p = prices[t]
        print(f"  {t:7s} {len(p):5d} days  {p.index[0].date()} to {p.index[-1].date()}  ({sources[t]})")

    # Cash interest. Missing IRX data is not fatal: cash then earns 0%, with a loud warning.
    try:
        irx, irx_source = load_prices(config.CASH_TICKER, demo=args.demo, refresh=args.refresh)
        print(f"  {'^IRX':7s} {len(irx):5d} days  {irx.index[0].date()} to {irx.index[-1].date()}  ({irx_source})")
    except DataUnavailable:
        irx, irx_source = None, "MISSING (cash earns 0%)"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cash = daily_cash_returns(irx)
    for w in caught:
        print(f"\nWARNING: {w.message}\n")
    all_sources = {**sources, config.CASH_TICKER: irx_source}

    names = [args.strategy] if args.strategy else list(STRATEGIES) + list(PORTFOLIOS)
    for name in names:
        print(f"\n=== {name} ===")
        if name in PORTFOLIOS:
            run_portfolio(name, PORTFOLIOS[name], prices, cash, all_sources, args.demo, args.reason)
            continue
        evaluations, notes = [], []
        for ticker in config.TRADED_ASSETS:
            strategy = STRATEGIES[name]()
            # fit() may choose parameters, and is only EVER given training data.
            fitted = strategy.fit(prices[ticker].loc[:config.TRAIN_END], cash_rate=cash)
            search = getattr(fitted, "search_results", None)
            if search is not None:
                notes.append(search_note(ticker, fitted))
            if not args.demo:
                trials.log_trial(name, ticker, len(search) if search is not None else 1,
                                 "brute-force search on 2005-2017" if search is not None else "fixed textbook values")
            ev = evaluate(fitted, prices[ticker], prices[config.BROAD_INDEX], ticker, is_demo=args.demo, cash_rate=cash)
            evaluations.append(ev)
            print_evaluation(ticker, fitted.label(), ev)
        overall = overall_verdict(evaluations)
        if not args.demo:
            record_look(name, evaluations, args.reason)
        path = write_report(fitted, evaluations, overall, all_sources, prices, extra_md="\n\n".join(notes),
                            cash_ok=cash is not None)
        print(f"  Overall: {overall}. Report: {path.relative_to(path.parents[2])}")
    return 0


def run_portfolio(name, strategy_name, prices, cash, sources, demo, reason=""):
    strategy = STRATEGIES[strategy_name]()
    if not demo:
        trials.log_trial(name, "Portfolio", 1, "fixed textbook values; risk settings not tuned")
    ev = evaluate_portfolio(strategy, prices, cash, is_demo=demo)
    print_evaluation("Portfolio", strategy.label(), ev)
    risk = ev.results[("full", "strategy")].risk
    print(f"      Risk rules: {risk.entries} entries, {risk.sized_by_risk_rule} sized by the 1% rule, "
          f"{risk.sized_by_cap} capped at 20%, {risk.trims} trims, {risk.stop_exits} stop exits, "
          f"circuit breaker triggered {len(risk.breaker_events)} times")
    for b in risk.breaker_events:
        print(f"      FLAG FOR REVIEW: circuit breaker tripped {b['tripped'].date()} ({b['drawdown']:.1%} from peak)")
    if not demo:
        record_look(name, [ev], reason)
    path = write_portfolio_report(strategy, ev, sources, cash_ok=cash is not None)
    print(f"  Overall: {ev.verdict}. Report: {path.relative_to(path.parents[2])}")


def record_look(idea, evaluations, reason):
    """Log this run's view of the 2018+ results (skipped if these exact numbers were seen before)."""
    numbers = []
    for ev in evaluations:
        m = ev.metrics.loc[("test", "strategy")]
        numbers += [ev.ticker, ev.strategy_label, m.sharpe, m.cagr, m.max_drawdown, m.n_trades]
    new = trials.log_look(idea, reason or "not given (run without --reason)", trials.results_fingerprint(numbers))
    n = len(trials.looks_for(idea))
    print(f"  Test-period look #{n} for {idea} logged." if new else
          f"  Same 2018+ numbers as an earlier run: not a new look ({n} so far for {idea}).")


def print_evaluation(ticker, label, ev):
    print(f"  {ticker:9s} {label:60s} -> {ev.verdict}")
    for c in ev.checks:
        print(f"      {c.number}. {c.name:30s} {c.status}")


def search_note(ticker, fitted) -> str:
    """Explain a parameter search in the report, so the number of tries is never hidden."""
    table = fitted.search_results
    best, median = table.sharpe.iloc[0], table.sharpe.median()
    return (f"**Parameter search on {ticker} (training data only):** tried **{len(table):,} combinations** "
            f"and kept the best: `{fitted.label()}`, training Sharpe {best:.2f}. The median combination "
            f"scored {median:.2f}. Picking the top of {len(table):,} tries almost guarantees a lucky winner; "
            "the question is whether it holds up in 2018+. (The search scores every combination with next-close "
            "timing, so the winner is picked to suit it: in the *Timing cost* table below, its same-close row is not "
            "a fair \"before\".)")


if __name__ == "__main__":
    sys.exit(main())
