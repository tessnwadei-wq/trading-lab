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
         Tessy runs `python reset_circuit_breaker.py --who Tessy --reason "..."`. The reset is
         refused without a name and a reason, and every reset is written to
         journal/circuit_breaker_resets.csv (when, who, why, and what tripped it).

  backtest  Nobody can press "reset" inside a simulation of the past. So we make an explicit,
         written-down ASSUMPTION: the review takes config.CIRCUIT_BREAKER_REVIEW_DAYS trading days,
         then trading resumes and that day's value becomes the new peak. The report prints this
         assumption. The hard floor never restarts in a backtest.

After any restart (manual or simulated), the peak is reset to the current value. Otherwise the
account would still be "10% below the old peak" and the breaker would trip again the next day.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from lab import config

ROOT = Path(__file__).resolve().parent.parent
RESET_LOG = ROOT / "journal" / "circuit_breaker_resets.csv"
PAPER_STATE = ROOT / "paper" / "circuit_breaker.json"   # created by paper trading (a later phase)
RESET_COLUMNS = ["reset_at", "who", "reason", "tripped_on", "fall_from_peak", "kind"]

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
              log_path: Path | None = None) -> dict:
        """
        Paper mode only: a person restarts trading after reviewing what went wrong.
        Refused without a name and a reason. Clears the 10% breaker and makes the current value the
        new peak. The all-time high is KEPT, so a series of reviewed 10% falls still hits the 20% hard
        floor. Resetting the hard floor itself is a bigger decision: it also makes the current value
        the new all-time high. Every reset is appended to the reset log.
        """
        if self.mode != PAPER:
            raise RuntimeError("Backtests can't be reset by hand: they use the review-period assumption "
                               "(config.CIRCUIT_BREAKER_REVIEW_DAYS).")
        if not (who or "").strip() or not (reason or "").strip():
            raise ValueError("A reset needs WHO is resetting it and the REASON (what was reviewed).")
        if self.allows_new_trades:
            raise ValueError("The circuit breaker is not tripped, so there is nothing to reset.")
        when = when or datetime.now()
        equity = self.last_equity if equity is None else equity
        kind = "hard floor" if self.halted else "10% breaker"
        trip = self.hard_stop if self.halted else self.events[-1]
        row = {"reset_at": when.isoformat(timespec="seconds"), "who": who.strip(), "reason": reason.strip(),
               "tripped_on": str(trip["tripped"])[:10], "fall_from_peak": f"{trip['drawdown']:.4f}", "kind": kind}
        self._restart(when, equity, f"manual reset by {who.strip()}: {reason.strip()}")
        if self.halted:
            self.halted, self.all_time_high = False, equity
        log_reset(row, log_path or RESET_LOG)
        return row

    # ---- saving and loading (paper mode keeps its state in a file between runs) ----------------
    def to_dict(self) -> dict:
        def clean(d):
            return None if d is None else {k: (str(v) if k in ("tripped", "resumed") and v is not None else v)
                                           for k, v in d.items()}
        return {"mode": self.mode, "peak": self.peak, "all_time_high": self.all_time_high,
                "last_equity": self.last_equity,
                "tripped": self.tripped, "halted": self.halted,
                "events": [clean(e) for e in self.events], "hard_stop": clean(self.hard_stop)}

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitBreaker":
        b = cls(mode=d["mode"])
        b.peak, b.all_time_high, b.last_equity = d["peak"], d["all_time_high"], d["last_equity"]
        b.tripped, b.halted = d["tripped"], d["halted"]
        b.events, b.hard_stop = list(d["events"]), d["hard_stop"]
        return b

    def save(self, path: Path = PAPER_STATE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = PAPER_STATE) -> "CircuitBreaker":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def log_reset(row: dict, path: Path = RESET_LOG) -> None:
    """Append one reset to the log. Rows are only ever added, never changed or removed."""
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESET_COLUMNS)
        if new:
            w.writeheader()
        w.writerow(row)
