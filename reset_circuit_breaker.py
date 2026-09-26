"""
Manually reset the circuit breaker (for paper trading, a later phase).

In paper trading the circuit breaker never restarts by itself. After the account falls 10% from its
peak (or 20% from its all-time high), no new trades are opened until a person has looked at what went
wrong and runs this command. Every reset is logged, with who did it, when and why, in
journal/circuit_breaker_resets.csv. The log is only ever added to.

Usage:
    python reset_circuit_breaker.py --status
    python reset_circuit_breaker.py --who Tessy --reason "Reviewed the fall: normal market drop, rules worked"

(Backtests don't use this: a simulation can't wait for a person, so it assumes a review period of
config.CIRCUIT_BREAKER_REVIEW_DAYS trading days instead. See lab/breaker.py.)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab import breaker as brk


def main(argv=None, state_path: Path | None = None, log_path: Path | None = None) -> int:
    ap = argparse.ArgumentParser(description="Manually reset the paper-trading circuit breaker")
    ap.add_argument("--status", action="store_true", help="show the breaker's state and change nothing")
    ap.add_argument("--who", help="your name (required to reset)")
    ap.add_argument("--reason", help="what you reviewed and why trading may restart (required to reset)")
    args = ap.parse_args(argv)
    state_path = state_path or brk.PAPER_STATE
    log_path = log_path or brk.RESET_LOG

    if not state_path.exists():
        print(f"No paper-trading account found ({state_path}). Paper trading hasn't started yet, "
              "so there is nothing to reset.")
        return 1
    b = brk.CircuitBreaker.load(state_path)
    status = ("TRIPPED by the hard floor (20% below the all-time high)" if b.halted else
              "TRIPPED (10% below the peak)" if b.tripped else "OK: new trades allowed")
    print(f"Circuit breaker: {status}. Account value {b.last_equity:.4f}, peak {b.peak:.4f}, "
          f"all-time high {b.all_time_high:.4f}.")
    if args.status:
        return 0
    try:
        row = b.reset(args.who, args.reason, log_path=log_path)
    except (ValueError, RuntimeError) as exc:
        print(f"NOT RESET: {exc}")
        return 1
    b.save(state_path)
    print(f"Reset by {row['who']} at {row['reset_at']} ({row['kind']}, tripped {row['tripped_on']}). "
          f"Reason logged in {log_path.name}. New trades are allowed again; the peak is now {b.peak:.4f}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
