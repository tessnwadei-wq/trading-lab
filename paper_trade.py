"""
Run the paper-trading account by hand: pretend money, real prices, every risk rule. No broker, no API keys.

    python paper_trade.py --start              # once: open the account ($10,000 of pretend money)
    python paper_trade.py                      # each time after: catch up on new closing prices
    python paper_trade.py --refresh            # the same, downloading the latest prices first
    python paper_trade.py --status             # show the account; change nothing

Each run reads the price files in data/csv/, processes every close it hasn't seen yet (orders decided at one close
fill at the next), decides at the latest close, logs every order, fill and balance in journal/paper/, and commits
the paper files to git. It refuses to run if any of its files is missing, edited, or doesn't match git.

The only strategy allowed is buy_and_hold of the 4-asset control mix (SPY, XIU.TO, GLD, IEF at up to 20% each), until
a strategy passes the full Skeptic Checklist. This is a PRACTICE RUN of the plumbing, not a strategy test.

The circuit breaker is human-only: if it trips, no new trades open until Tessy reviews what happened and resets it
herself with reset_circuit_breaker.py. This script never resets it. See lab/paper.py for the details.
"""

from __future__ import annotations

import argparse
import sys
import warnings

from lab import config
from lab.cash import daily_cash_returns
from lab.data import DataUnavailable, load_all, load_prices
from lab.paper import (ALLOWED_STRATEGIES, PAPER_ASSETS, PaperPaths, PaperRefused, commit_paper_files,
                       integrity_problems, load_state, run_account, start_account)


def load_market(refresh: bool):
    prices, _ = load_all(PAPER_ASSETS, refresh=refresh)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            irx, _ = load_prices(config.CASH_TICKER, refresh=refresh)
        except DataUnavailable:
            irx = None
        cash = daily_cash_returns(irx)
    for w in caught:
        print(f"WARNING: {w.message}")
    return prices, cash


def show_status(paths: PaperPaths) -> None:
    state, breaker = load_state(paths)
    equity = state["cash"] + sum(p["units"] * state["last_price"][a] for a, p in state["positions"].items())
    print(f"Paper account ({state['strategy']}), opened {state['started']}, last close processed "
          f"{state['last_processed']}.")
    print(f"  Value {equity:,.2f} ({equity / state['starting_cash'] - 1:+.2%} since the start), cash "
          f"{state['cash']:,.2f}")
    for a, p in sorted(state["positions"].items()):
        v = p["units"] * state["last_price"][a]
        print(f"  {a:7s} {p['units']:10.4f} units  worth {v:10,.2f} ({v / equity:5.1%})  stop {p['stop']:.2f}")
    for a, o in sorted(state["pending"].items()):
        print(f"  Waiting to fill at the next close: {o['kind']} {a} (decided {o['decided_on']})")
    status = ("HARD FLOOR tripped" if breaker.halted else "TRIPPED" if breaker.tripped else "ok")
    print(f"  Circuit breaker: {status}.")
    if not breaker.allows_new_trades:
        print("  FLAG FOR REVIEW: no new trades until Tessy reviews what happened and resets the breaker by hand.")


def main(argv=None, paths: PaperPaths | None = None) -> int:
    ap = argparse.ArgumentParser(description="Paper-trading account (pretend money, run by hand)")
    ap.add_argument("--start", action="store_true", help="open a new paper account (only once)")
    ap.add_argument("--cash", type=float, default=10_000.0, help="pretend starting money for --start")
    ap.add_argument("--strategy", default="buy_and_hold",
                    help=f"only {', '.join(ALLOWED_STRATEGIES)} is allowed until a strategy passes the Skeptic")
    ap.add_argument("--refresh", action="store_true", help="download the latest prices first")
    ap.add_argument("--status", action="store_true", help="show the account and change nothing")
    args = ap.parse_args(argv)
    paths = paths or PaperPaths()
    try:
        if args.status:
            problems = integrity_problems(paths)
            show_status(paths) if paths.state.exists() else print("No paper account yet: python paper_trade.py --start")
            for p in problems:
                print(f"  PROBLEM: {p}")
            return 0 if not problems else 1
        if args.strategy not in ALLOWED_STRATEGIES:
            from lab.paper import check_allowed
            check_allowed(args.strategy)
        prices, cash = load_market(args.refresh)
        if args.start:
            state = start_account(paths, prices, cash, args.strategy, args.cash)
            message = f"Paper trading: open the {args.strategy} account at the {state['started']} close"
            print(f"Opened the paper account with {args.cash:,.2f} of pretend money at the {state['started']} close. "
                  "Its first buy orders fill at the next close: run this again after that close arrives.")
        else:
            out = run_account(paths, prices, cash)
            state = out["state"]
            message = f"Paper trading: processed closes up to {state['last_processed']}"
            print(f"Processed {out['days']} new close(s), up to {state['last_processed']}.")
    except PaperRefused as exc:
        print(f"\nREFUSED. {exc}")
        return 1
    except DataUnavailable as exc:
        print(f"\nDATA PROBLEM\n{exc}")
        return 1
    show_status(paths)
    ok, detail = commit_paper_files(paths, message)
    if ok:
        print(f"Saved and committed the paper files ({detail.splitlines()[0] if detail else 'ok'}). "
              "Push them from GitHub Desktop when you like.")
    else:
        print(f"WARNING: couldn't commit the paper files ({detail}). Commit paper/ and journal/ in GitHub Desktop "
              "before the next run, or it will refuse to start.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
