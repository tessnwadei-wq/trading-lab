"""
The drawdown circuit breaker (CLAUDE.md risk rule: "If the account falls 10% from its peak, stop
opening new trades and flag for review").

In plain English: the breaker watches the account value every day. If it falls 10% below its
highest point (its "peak"), the breaker TRIPS: no new trades are opened until a review has
happened. Positions already open keep their normal exits (stops and signals), so the breaker
never forces a panic sale.

There is also a HARD FLOOR: if the account ever falls 20% below its ALL-TIME high, the breaker
halts new trades even if earlier 10% trips were reviewed. It stops a series of 10% falls quietly
adding up to a big loss.

What "a review" means depends on the MODE:

  paper  (future paper trading) A person must reset it. Nothing restarts by itself.
         HUMAN-ONLY (CLAUDE.md): only Tessy resets it, by typing at a terminal:
         `python reset_circuit_breaker.py --who Tessy --reason "..."`, then typing RESET to confirm
         (and, for the 20% hard floor, an extra confirmation). Agents must never run, script or
         suggest automating that command. The reset is refused without a name, a reason and the
         typed confirmation, and every reset is written to journal/circuit_breaker_resets.csv
         (when, who, why, and what tripped it).

         The reset log is APPEND-ONLY and tamper-evident:
           * each row stores `log_sha256_before`, a fingerprint (SHA-256 hash) of the whole file
             before that row was added, so editing or deleting an earlier row breaks the chain;
           * the breaker's saved state remembers how many rows the log had and its fingerprint after
             the last reset, so cutting rows off the END is caught too.
         If either check fails, the reset is refused until the log is restored (e.g. from git).

  backtest  Nobody can press "reset" inside a simulation of the past. So we make an explicit,
         written-down ASSUMPTION: the review takes config.CIRCUIT_BREAKER_REVIEW_DAYS trading days,
         then trading resumes and that day's value becomes the new peak. The report prints this
         assumption. The hard floor never restarts in a backtest.

After any restart (manual or simulated), the peak is reset to the current value. Otherwise the
account would still be "10% below the old peak" and the breaker would trip again the next day.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

from lab import config

ROOT = Path(__file__).resolve().parent.parent
RESET_LOG = ROOT / "journal" / "circuit_breaker_resets.csv"
PAPER_STATE = ROOT / "paper" / "circuit_breaker.json"   # created by paper trading (a later phase)
RESET_COLUMNS = ["reset_at", "who", "reason", "tripped_on", "fall_from_peak", "kind", "log_sha256_before"]
CONFIRM_WORD = "RESET"                  # what a person must type to confirm any reset
HARD_FLOOR_CONFIRM_WORD = "HARD FLOOR"  # the extra word for resetting the 20% hard floor


class ResetLogTampered(RuntimeError):
    """The reset log was edited or shortened: resets are refused until it is restored."""

BACKTEST, PAPER = "backtest", "paper"


class CircuitBreaker:
    def __init__(self, mode: str = BACKTEST, drawdown: float | None = None, review_days: int | None = None,
                 hard_stop: float | None = None):
        if mode not in (BACKTEST, PAPER):
            raise ValueError(f"mode must be '{BACKTEST}' or '{PAPER}'")
        self.mode = mode
        self.drawdown = config.CIRCUIT_BREAKER_DRAWDOWN if drawdown is None else drawdown
        self.review_days = config.CIRCUIT_BREAKER_REVIEW_DAYS if review_days is None else review_days
        self.hard_stop_level = config.CIRCUIT_BREAKER_HARD_STOP if hard_stop is None else hard_stop
        self.peak = 1.0              # the account starts at 1.0, which counts as its first peak
        self.all_time_high = 1.0
        self.last_equity = 1.0       # the account value at the most recent close seen
        self.tripped = False         # the 10% breaker is on
        self.resume_at = None        # backtest only: day number when the simulated review ends
        self.halted = False          # the 20% hard floor is on
        self.events: list[dict] = []  # one per 10% trip: {"tripped", "drawdown", "resumed", "resumed_by"}
        self.hard_stop: dict | None = None  # {"tripped", "drawdown"} once the hard floor is hit
        # What the reset log looked like after the last reset (paper mode): number of rows and fingerprint.
        self.reset_log_rows = 0
        self.reset_log_sha256 = ""

    @property
    def allows_new_trades(self) -> bool:
        return not (self.tripped or self.halted)

    def update(self, day_number: int, date, equity: float) -> None:
        """Call once a day with the account value at the close. day_number counts trading days."""
        self.last_equity = equity
        # Backtest only: the simulated review is over, so trading resumes from today's value.
        if self.tripped and self.mode == BACKTEST and day_number >= self.resume_at:
            self._restart(date, equity, f"simulated {self.review_days}-trading-day review (backtest assumption)")
        if not self.tripped:
            self.peak = max(self.peak, equity)
            if equity <= self.peak * (1 - self.drawdown):
                self.tripped = True
                self.resume_at = day_number + self.review_days
                self.events.append({"tripped": date, "drawdown": equity / self.peak - 1,
                                    "resumed": None, "resumed_by": None})
        self.all_time_high = max(self.all_time_high, equity)
        if not self.halted and equity <= self.all_time_high * (1 - self.hard_stop_level):
            self.halted = True
            self.hard_stop = {"tripped": date, "drawdown": equity / self.all_time_high - 1}

    def _restart(self, date, equity, by: str) -> None:
        self.tripped, self.resume_at, self.peak = False, None, equity
        if self.events and self.events[-1]["resumed"] is None:
            self.events[-1]["resumed"], self.events[-1]["resumed_by"] = date, by

    def reset(self, who: str, reason: str, equity: float | None = None, when: datetime | None = None,
              log_path: Path | None = None, confirmation: str = "", hard_floor_confirmation: str = "") -> dict:
        """
        Paper mode only: a person restarts trading after reviewing what went wrong.
        Refused without a name, a reason and the typed confirmation word (CONFIRM_WORD); resetting the
        20% hard floor also needs HARD_FLOOR_CONFIRM_WORD. Only reset_circuit_breaker.py, typed by Tessy,
        should ever call this (CLAUDE.md: agents never run, script or automate a reset).
        Clears the 10% breaker and makes the current value the new peak. The all-time high is KEPT, so a
        series of reviewed 10% falls still hits the 20% hard floor. Resetting the hard floor itself is a
        bigger decision: it also makes the current value the new all-time high. Every reset is appended
        to the reset log, which is checked for edits and shortening first.
        """
        if self.mode != PAPER:
            raise RuntimeError("Backtests can't be reset by hand: they use the review-period assumption "
                               "(config.CIRCUIT_BREAKER_REVIEW_DAYS).")
        if not (who or "").strip() or not (reason or "").strip():
            raise ValueError("A reset needs WHO is resetting it and the REASON (what was reviewed).")
        if self.allows_new_trades:
            raise ValueError("The circuit breaker is not tripped, so there is nothing to reset.")
        if (confirmation or "").strip() != CONFIRM_WORD:
            raise ValueError(f"Not confirmed: type {CONFIRM_WORD} to confirm a reset.")
        if self.halted and (hard_floor_confirmation or "").strip() != HARD_FLOOR_CONFIRM_WORD:
            raise ValueError(f"Not confirmed: the 20% hard floor needs the extra confirmation "
                             f"{HARD_FLOOR_CONFIRM_WORD}.")
        log_path = log_path or RESET_LOG
        self.check_reset_log(log_path)       # refuse if the log was edited or shortened
        when = when or datetime.now()
        equity = self.last_equity if equity is None else equity
        kind = "hard floor" if self.halted else "10% breaker"
        trip = self.hard_stop if self.halted else self.events[-1]
        who, reason = " ".join(who.split()), " ".join(reason.split())   # one line each in the log
        row = {"reset_at": when.isoformat(timespec="seconds"), "who": who.strip(), "reason": reason.strip(),
               "tripped_on": str(trip["tripped"])[:10], "fall_from_peak": f"{trip['drawdown']:.4f}", "kind": kind}
        self._restart(when, equity, f"manual reset by {who.strip()}: {reason.strip()}")
        if self.halted:
            self.halted, self.all_time_high = False, equity
        log_reset(row, log_path)
        self.reset_log_rows, self.reset_log_sha256 = self.reset_log_rows + 1, file_sha256(log_path)
        return row

    def check_reset_log(self, log_path: Path) -> None:
        """
        Raise ResetLogTampered unless the reset log is exactly what the last reset left behind (same number
        of rows and the same fingerprint) and every row's hash chain is intact.
        """
        ok, msg, rows = verify_reset_log(log_path)
        if not ok:
            raise ResetLogTampered(msg)
        if rows != self.reset_log_rows or (rows and file_sha256(log_path) != self.reset_log_sha256):
            raise ResetLogTampered(
                f"The reset log has {rows} rows, but after the last reset it had {self.reset_log_rows} with a "
                "different fingerprint: it was edited or shortened. Restore it (e.g. from git) before resetting.")

    # ---- saving and loading (paper mode keeps its state in a file between runs) ----------------
    def to_dict(self) -> dict:
        def clean(d):
            return None if d is None else {k: (str(v) if k in ("tripped", "resumed") and v is not None else v)
                                           for k, v in d.items()}
        return {"mode": self.mode, "peak": self.peak, "all_time_high": self.all_time_high,
                "last_equity": self.last_equity,
                "tripped": self.tripped, "halted": self.halted,
                "events": [clean(e) for e in self.events], "hard_stop": clean(self.hard_stop),
                "reset_log_rows": self.reset_log_rows, "reset_log_sha256": self.reset_log_sha256}

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitBreaker":
        b = cls(mode=d["mode"])
        b.peak, b.all_time_high, b.last_equity = d["peak"], d["all_time_high"], d["last_equity"]
        b.tripped, b.halted = d["tripped"], d["halted"]
        b.events, b.hard_stop = list(d["events"]), d["hard_stop"]
        b.reset_log_rows, b.reset_log_sha256 = d.get("reset_log_rows", 0), d.get("reset_log_sha256", "")
        return b

    def save(self, path: Path = PAPER_STATE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = PAPER_STATE) -> "CircuitBreaker":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def file_sha256(path: Path) -> str:
    """A fingerprint of a file's exact bytes: any change at all gives a completely different value."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def verify_reset_log(path: Path = RESET_LOG) -> tuple[bool, str, int]:
    """
    Check the hash chain: each row's log_sha256_before must be the fingerprint of everything above it.
    Returns (ok, message, number of rows). A missing file is fine (no resets yet).
    """
    if not path.exists():
        return True, "No resets logged yet.", 0
    data = path.read_bytes()
    lines = data.splitlines(keepends=True)
    if not lines:
        return False, "The reset log is empty but exists: it was cut down.", 0
    header = lines[0].decode("utf-8").strip().split(",")
    if header != RESET_COLUMNS:
        return False, "The reset log's header was changed.", 0
    offset = len(lines[0])
    for n, line in enumerate(lines[1:], start=1):
        row = next(csv.reader([line.decode("utf-8")]))
        if hashlib.sha256(data[:offset]).hexdigest() != row[-1]:
            return False, f"Row {n} of the reset log doesn't match the rows above it: the log was edited.", n
        offset += len(line)
    return True, f"{len(lines) - 1} resets logged; the hash chain is intact.", len(lines) - 1


def log_reset(row: dict, path: Path = RESET_LOG) -> None:
    """
    Append one reset to the log. Rows are only ever added, never changed or removed: the file is only
    ever opened in append mode, and each new row records the fingerprint of the file before it.
    """
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    if new:
        with path.open("a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=RESET_COLUMNS).writeheader()
    row = {**row, "log_sha256_before": file_sha256(path)}
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=RESET_COLUMNS).writerow(row)
