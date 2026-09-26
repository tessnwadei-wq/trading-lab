"""
The over-search counter: how many things has the lab tried, ever?

Why it matters: if you test enough rules, one of them WILL look great by pure luck, the same way
someone in a big enough crowd will flip ten heads in a row. So a result must be judged against
how many tries it took to find it. journal/trials.csv keeps the running count, and it never
goes down: rows are added, never removed.

One row = one idea tested on one asset (or portfolio), with how many parameter combinations were
tried to pick the version that's reported. Re-running the exact same thing adds nothing.
(The sensitivity grid in each report is NOT counted: it checks a choice already made, it doesn't
make the choice. If you ever pick parameters BY LOOKING at that grid, log those as trials too.)

The "luck bar" (a simplified version of the Deflated Sharpe Ratio, Bailey & Lopez de Prado, 2014):
  If you try N strategies that have NO real edge, each measured over T years, their Sharpe ratios
  scatter around 0 with a spread of about 1 / sqrt(T). The best of N such tries is expected to reach
      luck bar ~= spread x z(N)
  where z(N) is how far above average the best of N random draws usually lands
  (about 1.5 for N = 5, 2.5 for N = 100, 3.4 for N = 2,000).
  A strategy's Sharpe has to clear this bar before we can believe it's more than luck.
  The rough chance it's real = Normal distribution at (Sharpe - luck bar) / spread.
  (The full formula also adjusts for fat tails and skew; we skip that to keep it readable.)

TEST-PERIOD LOOKS (journal/test_period_looks.csv). The rules say the 2018+ test period is touched
ONCE per idea. Every time someone sees 2018+ results for an idea during development, that's a
"look", and each extra look quietly weakens the test: if you look, change something, and look again,
the test period starts to become training data. So every look is logged with its date and reason:
  * run_lab.py logs one automatically whenever it writes a real-data report (the reason comes from
    `--reason "..."`). Re-running with nothing changed shows exactly the same numbers, so it is NOT a
    new look: each look carries a "fingerprint" of the 2018+ results, and a repeat is skipped.
  * Looks made any other way (a notebook, a one-off script, a teammate's screenshot) must be added
    by hand with log_look(). Like trials.csv, rows are only ever added, never removed.
"""

from __future__ import annotations

import csv
import hashlib
import math
from datetime import date
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
TRIALS_CSV = ROOT / "journal" / "trials.csv"
COLUMNS = ["first_logged", "idea", "asset", "configurations", "how_chosen", "data"]
LOOKS_CSV = ROOT / "journal" / "test_period_looks.csv"
LOOK_COLUMNS = ["date", "idea", "reason", "logged_by", "fingerprint"]
EULER_GAMMA = 0.5772156649


def read_trials(path: Path = TRIALS_CSV) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def log_trial(idea: str, asset: str, configurations: int, how_chosen: str, data: str = "real",
              path: Path = TRIALS_CSV, today: str | None = None) -> bool:
    """Add a row unless the exact same test (idea, asset, configurations, how chosen) is already logged."""
    rows = read_trials(path)
    key = (idea, asset, str(configurations), how_chosen)
    if any((r["idea"], r["asset"], r["configurations"], r["how_chosen"]) == key for r in rows):
        return False
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        w.writerow({"first_logged": today or date.today().isoformat(), "idea": idea, "asset": asset,
                    "configurations": configurations, "how_chosen": how_chosen, "data": data})
    return True


def totals(path: Path = TRIALS_CSV) -> dict:
    """Lab-wide counts, real-data trials only (practice runs on synthetic data don't count)."""
    rows = [r for r in read_trials(path) if r["data"] == "real"]
    return {"configurations": sum(int(r["configurations"]) for r in rows),
            "ideas": len({r["idea"] for r in rows}), "rows": len(rows)}


def trials_for(idea: str, asset: str, path: Path = TRIALS_CSV) -> int:
    return sum(int(r["configurations"]) for r in read_trials(path)
               if r["idea"] == idea and r["asset"] == asset and r["data"] == "real")


def expected_max_z(n: int) -> float:
    """How many 'spreads' above zero the best of n no-skill tries is expected to land."""
    if n <= 1:
        return 0.0
    nd = NormalDist()
    return (1 - EULER_GAMMA) * nd.inv_cdf(1 - 1 / n) + EULER_GAMMA * nd.inv_cdf(1 - 1 / (n * math.e))


def luck_bar(n_trials: int, years: float) -> float:
    """The Sharpe the luckiest of n no-edge strategies would be expected to show over `years` years."""
    return expected_max_z(n_trials) / math.sqrt(years)


def chance_real(sharpe: float, n_trials: int, years: float) -> float:
    """Rough probability that the true Sharpe is above zero, after allowing for n_trials tries."""
    spread = 1 / math.sqrt(years)
    return NormalDist().cdf((sharpe - luck_bar(n_trials, years)) / spread)


# --------------------------------------------------------------------------------------
# Test-period looks
# --------------------------------------------------------------------------------------
def read_looks(path: Path | None = None) -> list[dict]:
    path = path or LOOKS_CSV
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def log_look(idea: str, reason: str, fingerprint: str = "", logged_by: str = "run_lab.py",
             path: Path | None = None, today: str | None = None) -> bool:
    """
    Record one look at an idea's 2018+ results. Returns False (and logs nothing) if these exact
    results were already seen: same idea, same fingerprint. An empty fingerprint is always logged.
    """
    path = path or LOOKS_CSV
    rows = read_looks(path)
    if fingerprint and any(r["idea"] == idea and r["fingerprint"] == fingerprint for r in rows):
        return False
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOOK_COLUMNS)
        if new:
            w.writeheader()
        w.writerow({"date": today or date.today().isoformat(), "idea": idea, "reason": reason,
                    "logged_by": logged_by, "fingerprint": fingerprint})
    return True


def looks_for(idea: str, path: Path | None = None) -> list[dict]:
    """Every logged look at this idea's test period, oldest first."""
    return [r for r in read_looks(path) if r["idea"] == idea]


def results_fingerprint(numbers) -> str:
    """A short code that changes whenever any of the given test-period numbers change."""
    text = repr([round(float(x), 6) if isinstance(x, (int, float)) else str(x) for x in numbers])
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
