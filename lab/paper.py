"""
The paper-trading account: pretend money, real prices, every risk rule, run by hand on Tessy's PC.

What it is: a small account ($10,000 of pretend money by default) whose whole state lives in files:
  paper/account.json                    cash, positions, stops, orders waiting to fill
  paper/circuit_breaker.json            the circuit breaker (lab/breaker.py, PAPER mode: manual reset only)
  journal/circuit_breaker_resets.csv    the append-only, hash-chained reset log
  journal/paper/orders.csv              every order: when it was decided, what, why
  journal/paper/fills.csv               every fill: when, how many units, at what price, what it cost
  journal/paper/balances.csv            the account's value at every close
  journal/paper/events.csv              alerts, blocked orders, circuit-breaker trips
No broker, no API keys, no internet except the optional price download. Nothing real is ever bought.

How a run works (python paper_trade.py): it reads the price files, then walks forward through every trading day
it hasn't seen yet, exactly like the backtest engine but one day at a time, remembering everything in the files:
  1. The day's closes arrive: positions are valued at them and cash earns a day of T-bill interest.
  2. Orders decided at the previous close are FILLED at this close (exits first, then buys, then resizes/trims).
  3. DECISIONS at this close (filled at the next close, which a later run will see): stop-outs, the circuit
     breaker, new buys, the monthly resize back to target, trims above 20%, the 22% alert.
So the last thing a run does is decide at the latest close; those orders fill when the next close arrives.

The only strategy allowed for now is `buy_and_hold` of the 4-asset control mix: SPY, XIU.TO, GLD and IEF at up to
20% each (sized by the 1% rule, capped at 20%), always held, resized monthly, the rest in cash. It tests the
plumbing, not a strategy: no strategy has passed the Skeptic Checklist yet, and any other name is refused.

Safety checks before every run (the account refuses to start if any fails):
  * the account file, the breaker file and the reset log all exist;
  * none of them, nor the journal/paper logs, has been changed since the last commit (git), and all are tracked;
  * the account file's own checksum matches (it was written by this program, not edited by hand);
  * the journal/paper logs match the fingerprint the account saved last time (no edited or deleted rows);
  * the reset log's hash chain is intact and matches what the breaker remembers.
After a successful run the program commits the paper files to git itself, so the next run can check them.

The circuit breaker is HUMAN-ONLY (CLAUDE.md): when it trips, this program opens no new trades and never resets it.
Only Tessy resets it, in person, with reset_circuit_breaker.py; then she commits the two changed files.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from lab import config
from lab.breaker import PAPER, RESET_COLUMNS, CircuitBreaker, ResetLogTampered, file_sha256, verify_reset_log
from lab.cash import align_cash
from lab.portfolio import risk_sized_order
from strategies.vol_target import month_end_decision_days

ROOT = Path(__file__).resolve().parent.parent
STARTING_CASH = 10_000.0

# The only paper strategy allowed until a strategy passes the full Skeptic Checklist (none has yet).
ALLOWED_STRATEGIES = {
    "buy_and_hold": ("Buy-and-hold of the 4-asset control mix: SPY, XIU.TO, GLD and IEF at up to 20% each (1% rule, "
                     "20% cap), always held, resized monthly, the rest in cash. A plumbing test, not a strategy."),
}
PAPER_ASSETS = ["SPY", "XIU.TO", "GLD", "IEF"]
TARGET_WEIGHT = config.MAX_POSITION_WEIGHT

ORDER_COLUMNS = ["order_id", "decided_on", "asset", "kind", "target_weight", "note"]
FILL_COLUMNS = ["order_id", "filled_on", "asset", "kind", "side", "units", "price", "amount", "cost"]
BALANCE_COLUMNS = ["date", "cash"] + [f"{a}_value" for a in PAPER_ASSETS] + ["total", "change_since_start",
                                                                              "below_peak", "breaker"]
EVENT_COLUMNS = ["date", "kind", "detail"]


class PaperRefused(RuntimeError):
    """The paper account refuses to run. The message says what's wrong and how to fix it."""


@dataclass
class PaperPaths:
    root: Path = ROOT

    @property
    def state(self) -> Path:
        return self.root / "paper" / "account.json"

    @property
    def breaker(self) -> Path:
        return self.root / "paper" / "circuit_breaker.json"

    @property
    def reset_log(self) -> Path:
        return self.root / "journal" / "circuit_breaker_resets.csv"

    @property
    def log_dir(self) -> Path:
        return self.root / "journal" / "paper"

    @property
    def logs(self) -> dict:
        return {"orders": self.log_dir / "orders.csv", "fills": self.log_dir / "fills.csv",
                "balances": self.log_dir / "balances.csv", "events": self.log_dir / "events.csv"}

    def all_files(self) -> list[Path]:
        return [self.state, self.breaker, self.reset_log] + list(self.logs.values())

    def rel(self, p: Path) -> str:
        return p.relative_to(self.root).as_posix()


# --------------------------------------------------------------------------------------
# Fingerprints and git
# --------------------------------------------------------------------------------------
def state_checksum(state: dict) -> str:
    """A fingerprint of the account file's contents (everything except the checksum itself)."""
    body = {k: v for k, v in state.items() if k != "checksum"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()


def ledger_sha256(paths: PaperPaths) -> str:
    """One fingerprint for all four journal/paper logs together."""
    h = hashlib.sha256()
    for name, p in paths.logs.items():
        h.update(name.encode() + b"\0" + (p.read_bytes() if p.exists() else b"") + b"\0")
    return h.hexdigest()


def _git(paths: PaperPaths, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(paths.root), *args], capture_output=True, text=True)


def git_problems(paths: PaperPaths, files: list[Path]) -> list[str]:
    """Every file must be tracked by git and unchanged since the last commit."""
    try:
        inside = _git(paths, "rev-parse", "--is-inside-work-tree")
    except OSError:
        return ["git isn't installed, so the paper account can't check its files. Install GitHub Desktop "
                "(it includes git) and get the code with File -> Clone repository."]
    if inside.returncode != 0:
        return ["This folder isn't a git repository (was it downloaded as a ZIP?). Get the code with GitHub Desktop "
                "(File -> Clone repository) so the paper account can check its files against git."]
    problems = []
    for f in files:
        rel = paths.rel(f)
        if _git(paths, "ls-files", "--error-unmatch", "--", rel).returncode != 0:
            problems.append(f"{rel} is not committed to git.")
        elif _git(paths, "diff", "--quiet", "HEAD", "--", rel).returncode != 0:
            problems.append(f"{rel} has been changed since the last commit.")
    return problems


def commit_paper_files(paths: PaperPaths, message: str) -> tuple[bool, str]:
    """Commit ONLY the paper files (nothing else in the folder), so the next run can check them against git."""
    rels = [paths.rel(f) for f in paths.all_files() if f.exists()]
    add = _git(paths, "add", "--", *rels)
    if add.returncode != 0:
        return False, add.stderr.strip()
    if _git(paths, "diff", "--cached", "--quiet", "--", *rels).returncode == 0:
        return True, "nothing new to commit"
    done = _git(paths, "commit", "-m", message, "--", *rels)
    return done.returncode == 0, (done.stdout + done.stderr).strip()


# --------------------------------------------------------------------------------------
# Loading, checking, saving
# --------------------------------------------------------------------------------------
def check_allowed(strategy: str) -> None:
    if strategy not in ALLOWED_STRATEGIES:
        raise PaperRefused(
            f"'{strategy}' is not allowed in paper trading. No strategy has passed the full Skeptic Checklist yet, "
            f"so the only paper strategy is 'buy_and_hold' (the 4-asset control mix), which tests the plumbing. "
            "A strategy can only be added after its report says PASS on real data, and after the risk-manager review.")


def integrity_problems(paths: PaperPaths, check_git: bool = True) -> list[str]:
    """Everything that must be true before the account may run. An empty list means all is well."""
    problems = []
    for f, what in ((paths.state, "the account file"), (paths.breaker, "the circuit-breaker file"),
                    (paths.reset_log, "the circuit-breaker reset log")):
        if not f.exists():
            problems.append(f"{paths.rel(f)} ({what}) is missing.")
    if problems:
        return problems
    state = json.loads(paths.state.read_text(encoding="utf-8"))
    if state.get("checksum") != state_checksum(state):
        problems.append(f"{paths.rel(paths.state)} was edited by hand (its checksum doesn't match).")
    if state.get("ledger_sha256") != ledger_sha256(paths):
        problems.append("The journal/paper logs don't match what the account saved last time: a row was edited, "
                        "added or deleted by hand, or a file is missing.")
    try:
        CircuitBreaker.load(paths.breaker).check_reset_log(paths.reset_log)
    except ResetLogTampered as exc:
        problems.append(f"Reset log problem: {exc}")
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        problems.append(f"{paths.rel(paths.breaker)} can't be read ({exc}).")
    if state.get("strategy") not in ALLOWED_STRATEGIES:
        problems.append(f"The account's strategy '{state.get('strategy')}' is not allowed in paper trading.")
    if check_git:
        problems += git_problems(paths, [f for f in paths.all_files() if f.exists()])
    return problems


def refuse_if_unsafe(paths: PaperPaths, check_git: bool = True) -> None:
    problems = integrity_problems(paths, check_git)
    if problems:
        raise PaperRefused("The paper account refuses to run:\n  - " + "\n  - ".join(problems) + "\n" + FIX_HELP)


FIX_HELP = ("How to fix: if you have just reset the circuit breaker yourself, commit the two changed files "
            "(paper/circuit_breaker.json and journal/circuit_breaker_resets.csv) in GitHub Desktop and run again. "
            "Otherwise, put the files back as they were in git (GitHub Desktop: right-click the file -> Discard "
            "changes). Never edit these files by hand.")


def load_state(paths: PaperPaths) -> tuple[dict, CircuitBreaker]:
    return json.loads(paths.state.read_text(encoding="utf-8")), CircuitBreaker.load(paths.breaker)


def save_state(paths: PaperPaths, state: dict, breaker: CircuitBreaker) -> None:
    state["ledger_sha256"] = ledger_sha256(paths)
    state["checksum"] = state_checksum(state)
    paths.state.parent.mkdir(parents=True, exist_ok=True)
    paths.state.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    breaker.save(paths.breaker)


def _append(path: Path, columns: list[str], row: dict) -> None:
    """Logs are only ever appended to."""
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        if new:
            w.writeheader()
        w.writerow(row)


# --------------------------------------------------------------------------------------
# The account
# --------------------------------------------------------------------------------------
class Account:
    """One run of the paper account: walks through new closes, filling and deciding. See the module docstring."""

    def __init__(self, paths: PaperPaths, state: dict, breaker: CircuitBreaker, prices: dict,
                 cash_rate: pd.Series | None, echo=print):
        self.paths, self.s, self.breaker, self.echo = paths, state, breaker, echo
        self.assets = state["assets"]
        self.rate = config.COST_PER_TRADE
        self.closes = {a: prices[a]["Close"].astype(float).dropna() for a in self.assets}
        # Only days every asset's file already covers: a file that is a day behind must not look like a holiday.
        last_common = min(c.index[-1] for c in self.closes.values())
        self.calendar = pd.DatetimeIndex(sorted(set().union(*[c.index for c in self.closes.values()])))
        self.calendar = self.calendar[self.calendar <= last_common]
        self.cash_ret = align_cash(cash_rate, self.calendar)

    # ---- small helpers -------------------------------------------------------------------
    def value(self, a) -> float:
        p = self.s["positions"].get(a)
        return p["units"] * self.s["last_price"][a] if p else 0.0

    def equity(self) -> float:
        return self.s["cash"] + sum(self.value(a) for a in self.assets)

    def traded(self, a, day) -> bool:
        return day in self.closes[a].index

    def avg_move(self, a, day) -> float:
        hist = self.closes[a].loc[:day]
        return float(hist.pct_change().abs().tail(config.STOP_ATR_DAYS).mean()) if len(hist) > config.STOP_ATR_DAYS \
            else float("nan")

    def month_end(self, a, day) -> bool:
        idx = self.closes[a].loc[:day].index
        return bool(month_end_decision_days(idx)[-1])

    def event(self, day, kind, detail):
        _append(self.paths.logs["events"], EVENT_COLUMNS, {"date": str(day.date()), "kind": kind, "detail": detail})
        self.echo(f"  {day.date()} {kind.upper()}: {detail}")

    def order(self, day, a, kind, target=None, note="", extra=None):
        oid = self.s["next_order_id"]
        self.s["next_order_id"] += 1
        self.s["pending"][a] = {"id": oid, "kind": kind, "decided_on": str(day.date()), "target": target, **(extra or {})}
        _append(self.paths.logs["orders"], ORDER_COLUMNS,
                {"order_id": oid, "decided_on": str(day.date()), "asset": a, "kind": kind,
                 "target_weight": "" if target is None else f"{target:.4f}", "note": note})

    def fill(self, day, a, o, side, units, price, cost):
        _append(self.paths.logs["fills"], FILL_COLUMNS,
                {"order_id": o["id"], "filled_on": str(day.date()), "asset": a, "kind": o["kind"], "side": side,
                 "units": f"{units:.6f}", "price": f"{price:.4f}", "amount": f"{units * price:.2f}",
                 "cost": f"{cost:.2f}"})

    # ---- step 2: fills at this close ---------------------------------------------------------
    def fill_orders(self, day):
        todays = {a: o for a, o in self.s["pending"].items() if self.traded(a, day)}
        for a in list(todays):
            if todays[a]["kind"] in ("stop", "exit"):
                o, p = todays.pop(a), self.s["positions"].pop(a)
                price = self.s["last_price"][a]
                self.s["cash"] += p["units"] * price * (1 - self.rate)
                self.fill(day, a, o, "sell", p["units"], price, p["units"] * price * self.rate)
                if o["kind"] == "stop":
                    self.s["rearm"][a] = True    # wait for the next month-end before buying it again
                del self.s["pending"][a]
        equity = self.equity()          # every buy today is sized on the same account value
        buys = [a for a, o in todays.items() if o["kind"] == "entry"]
        sizes_today = sum(todays[a]["target"] for a in buys)
        for a in buys:
            o, price = self.s["pending"].pop(a), self.s["last_price"][a]
            amount = min(o["target"] * equity / (1 + sizes_today * self.rate), max(self.s["cash"], 0) / (1 + self.rate))
            if amount > 0:
                self.s["cash"] -= amount * (1 + self.rate)
                self.s["positions"][a] = {"units": amount / price, "stop": price * (1 - o["distance"]),
                                          "entry_date": str(day.date()), "entry_price": price}
                self.fill(day, a, o, "buy", amount / price, price, amount * self.rate)
        equity = self.equity()
        for a, o in todays.items():
            if o["kind"] not in ("resize", "trim"):
                continue
            self.s["pending"].pop(a)
            p, price = self.s["positions"].get(a), self.s["last_price"][a]
            if not p:
                continue
            value = p["units"] * price
            if o["kind"] == "trim":
                if value <= config.TRIM_BACK_TO * equity:
                    continue
                delta = -(value - config.TRIM_BACK_TO * equity) / (1 - config.TRIM_BACK_TO * self.rate)
            else:
                delta = o["target"] * equity - value
                if delta > 0 and not self.breaker.allows_new_trades:
                    self.event(day, "top-up skipped", f"{a}: no top-ups while the circuit breaker is on")
                    continue
                delta = min(delta, max(self.s["cash"], 0) / (1 + self.rate))
                p["stop"] = price * (1 - o["distance"])       # a resize resets the stop below today's price
            units = delta / price
            self.s["cash"] -= delta + abs(delta) * self.rate
            p["units"] += units
            self.fill(day, a, o, "buy" if delta > 0 else "sell", abs(units), price, abs(delta) * self.rate)

    # ---- step 3: decisions at this close ---------------------------------------------------------
    def decide(self, day):
        s = self.s
        # Stops (checked at the close; the sale fills at the next close).
        for a in self.assets:
            p = s["positions"].get(a)
            if p and self.traded(a, day) and a not in s["pending"] and s["last_price"][a] <= p["stop"]:
                self.order(day, a, "stop", note=f"close {s['last_price'][a]:.2f} at/below stop {p['stop']:.2f}")
        # The circuit breaker, on the account value relative to the starting cash.
        was_ok = self.breaker.allows_new_trades
        s["day_number"] += 1
        self.breaker.update(s["day_number"], day, self.equity() / s["starting_cash"])
        if was_ok and not self.breaker.allows_new_trades:
            level = "the 20% HARD FLOOR" if self.breaker.halted else "the 10% circuit breaker"
            self.event(day, "circuit breaker", f"FLAG FOR REVIEW: {level} tripped at {self.equity():,.2f} "
                       f"({self.equity() / s['starting_cash'] / self.breaker.peak - 1:.1%} from the peak). "
                       "No new trades until Tessy reviews and resets it by hand.")
        equity = self.equity()
        n_open = len(s["positions"]) + sum(1 for o in s["pending"].values() if o["kind"] == "entry")
        for a in self.assets:
            if not self.traded(a, day) or a in s["pending"]:
                continue
            month_end = self.month_end(a, day)
            if s["rearm"].get(a) and month_end:
                s["rearm"][a] = False
            move = self.avg_move(a, day)
            if np.isnan(move) or move <= 0:
                continue
            order, _ = risk_sized_order(move, self.rate, TARGET_WEIGHT)
            held = a in s["positions"]
            if not held and not s["rearm"].get(a):
                # Buy-and-hold: always wants to own it. Blocked by the breaker or the 5-position limit.
                if not self.breaker.allows_new_trades or n_open >= config.MAX_OPEN_POSITIONS:
                    if not s["blocked"].get(a):
                        s["blocked"][a] = True
                        why = "circuit breaker is on" if not self.breaker.allows_new_trades else "5 positions open"
                        self.event(day, "buy blocked", f"{a}: {why}")
                    continue
                s["blocked"][a] = False
                self.order(day, a, "entry", order["size"], "buy-and-hold: own it", {"distance": order["distance"]})
                n_open += 1
            elif held and month_end:
                self.order(day, a, "resize", order["size"], "monthly resize to target",
                           {"distance": order["distance"]})
            elif held and self.value(a) > config.MAX_POSITION_WEIGHT * equity * (1 + 1e-9):
                self.order(day, a, "trim", config.TRIM_BACK_TO, f"{self.value(a) / equity:.1%} of the account")
        for a in self.assets:
            if a in s["positions"] and self.value(a) > config.POSITION_ALERT_WEIGHT * equity:
                self.event(day, "position alert", f"{a} ended the day at {self.value(a) / equity:.1%} of the account")
        _append(self.paths.logs["balances"], BALANCE_COLUMNS, {
            "date": str(day.date()), "cash": f"{s['cash']:.2f}",
            **{f"{a}_value": f"{self.value(a):.2f}" for a in PAPER_ASSETS},
            "total": f"{equity:.2f}", "change_since_start": f"{equity / s['starting_cash'] - 1:.4f}",
            "below_peak": f"{equity / s['starting_cash'] / self.breaker.peak - 1:.4f}",
            "breaker": "ok" if self.breaker.allows_new_trades else ("HARD FLOOR" if self.breaker.halted else "TRIPPED")})
        s["last_processed"] = str(day.date())

    # ---- a whole run ----------------------------------------------------------------------------------
    def new_days(self) -> pd.DatetimeIndex:
        return self.calendar[self.calendar > pd.Timestamp(self.s["last_processed"])]

    def step(self, day):
        """One close: prices and interest, then fills, then decisions."""
        for a in self.assets:
            if self.traded(a, day):
                self.s["last_price"][a] = float(self.closes[a].loc[day])
        self.s["cash"] *= 1 + float(self.cash_ret.loc[day])
        self.fill_orders(day)
        self.decide(day)


def start_account(paths: PaperPaths, prices: dict, cash_rate, strategy: str = "buy_and_hold",
                  starting_cash: float = STARTING_CASH, echo=print, check_git: bool = True) -> dict:
    """Open a new paper account at the latest close and place its first orders (they fill at the next close)."""
    check_allowed(strategy)
    if paths.state.exists() or paths.breaker.exists():
        raise PaperRefused(f"A paper account already exists ({paths.rel(paths.state)}). It is never replaced "
                           "automatically; its history is part of the record.")
    ok, msg, _ = verify_reset_log(paths.reset_log)
    if not ok:
        raise PaperRefused(f"Reset log problem: {msg}")
    if check_git and paths.reset_log.exists():
        problems = git_problems(paths, [paths.reset_log])
        if problems:
            raise PaperRefused("The paper account refuses to start:\n  - " + "\n  - ".join(problems) + "\n" + FIX_HELP)
    if not paths.reset_log.exists():   # an empty reset log (header only), so "missing" can be detected later
        paths.reset_log.parent.mkdir(parents=True, exist_ok=True)
        with paths.reset_log.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(RESET_COLUMNS)
    breaker = CircuitBreaker(mode=PAPER)
    breaker.reset_log_rows = verify_reset_log(paths.reset_log)[2]
    breaker.reset_log_sha256 = file_sha256(paths.reset_log) if breaker.reset_log_rows else ""
    state = {"version": 1, "strategy": strategy, "assets": PAPER_ASSETS, "starting_cash": float(starting_cash),
             "cash": float(starting_cash), "positions": {}, "pending": {}, "rearm": {}, "blocked": {},
             "last_price": {}, "next_order_id": 1, "day_number": 0, "last_processed": "1900-01-01"}
    acct = Account(paths, state, breaker, prices, cash_rate, echo)
    first = acct.calendar[-1]
    for a in PAPER_ASSETS:
        state["last_price"][a] = float(acct.closes[a].loc[:first].iloc[-1])
    state["started"] = str(first.date())
    acct.event(first, "account opened", f"{strategy} with {starting_cash:,.2f} of pretend money")
    acct.decide(first)
    save_state(paths, state, breaker)
    return state


def run_account(paths: PaperPaths, prices: dict, cash_rate, echo=print, check_git: bool = True) -> dict:
    """Process every close since the last run. Refuses to run if any safety check fails."""
    refuse_if_unsafe(paths, check_git)
    state, breaker = load_state(paths)
    check_allowed(state["strategy"])
    acct = Account(paths, state, breaker, prices, cash_rate, echo)
    days = acct.new_days()
    for day in days:
        acct.step(day)
    save_state(paths, state, breaker)
    return {"days": len(days), "equity": acct.equity(), "state": state, "breaker": breaker}
