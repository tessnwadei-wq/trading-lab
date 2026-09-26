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
"""

from __future__ import annotations

import csv
import math
from datetime import date
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
TRIALS_CSV = ROOT / "journal" / "trials.csv"
COLUMNS = ["first_logged", "idea", "asset", "configurations", "how_chosen", "data"]
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
