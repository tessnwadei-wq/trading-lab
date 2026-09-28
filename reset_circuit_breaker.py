"""
Manually reset the circuit breaker (for paper trading, a later phase).

HUMAN-ONLY. Only Tessy resets the circuit breaker, by typing this command in person at a terminal.
Agents (Claude or any other AI helper) must never run it, put it in a script, or suggest automating it
(CLAUDE.md). The command refuses to run unless a person is typing at a real terminal.

In paper trading the circuit breaker never restarts by itself. After the account falls 10% from its
peak (or 20% from its all-time high), no new trades are opened until a person has looked at what went
wrong and runs this command. A reset needs:
  1. --who and --reason (what you reviewed),
  2. typing RESET when asked, and
  3. for the 20% hard floor only, an extra step: typing HARD FLOOR and then your name again.
Every reset is logged, with who did it, when and why, in journal/circuit_breaker_resets.csv. The log is
only ever added to; if anyone edits or shortens it, resets are refused until it's restored (lab/breaker.py).

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


def main(argv=None, state_path: Path | None = None, log_path: Path | None = None,
         ask=input, interactive: bool | None = None) -> int:
    """`ask` and `interactive` exist only so the tests can play the part of a person typing."""
    ap = argparse.ArgumentParser(description="Manually reset the paper-trading circuit breaker (Tessy only)")
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
    ok, msg, _ = brk.verify_reset_log(log_path)
    print(f"Reset log: {msg}")
    if args.status:
        return 0

    if not (args.who or "").strip() or not (args.reason or "").strip():
        print("NOT RESET: a reset needs --who (your name) and --reason (what you reviewed).")
        return 1
    if interactive is None:
        interactive = sys.stdin.isatty()
    if not interactive:
        print("NOT RESET: this command must be typed by a person at a terminal, not run from a script or "
              "an AI agent (CLAUDE.md: only Tessy resets the circuit breaker).")
        return 1
    if b.allows_new_trades:
        print("NOT RESET: the circuit breaker is not tripped, so there is nothing to reset.")
        return 1

    print(f"\nYou are about to let the paper account open new trades again.\n  Who:    {args.who.strip()}\n"
          f"  Reason: {args.reason.strip()}")
    typed = ask(f"Type {brk.CONFIRM_WORD} to confirm (anything else cancels): ")
    if typed.strip() != brk.CONFIRM_WORD:
        print("Cancelled: nothing was reset.")
        return 1
    floor_word = ""
    if b.halted:
        fall = b.hard_stop["drawdown"] if b.hard_stop else b.last_equity / b.all_time_high - 1
        print(f"\nEXTRA CHECK: this is the 20% HARD FLOOR. The account fell {fall:.1%} from its all-time high.\n"
              "Resetting it also makes today's value the new all-time high, so the floor starts counting again\n"
              "from here. Only do this after a full review of the strategy, not just this fall.")
        floor_word = ask(f"Type {brk.HARD_FLOOR_CONFIRM_WORD} to confirm: ")
        again = ask("Type your name again: ")
        if floor_word.strip() != brk.HARD_FLOOR_CONFIRM_WORD or again.strip() != args.who.strip():
            print("Cancelled: nothing was reset.")
            return 1
    try:
        row = b.reset(args.who, args.reason, log_path=log_path, confirmation=typed,
                      hard_floor_confirmation=floor_word)
    except (ValueError, RuntimeError) as exc:
        print(f"NOT RESET: {exc}")
        return 1
    b.save(state_path)
    print(f"Reset by {row['who']} at {row['reset_at']} ({row['kind']}, tripped {row['tripped_on']}). "
          f"Reason logged in {log_path.name}. New trades are allowed again; the peak is now {b.peak:.4f}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
