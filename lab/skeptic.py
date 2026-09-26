"""
The Skeptic: automates as much of the Skeptic Checklist (CLAUDE.md) as a computer can.

Default stance: a good result is luck or overfitting until proven otherwise. So every
check has a clear, written pass rule, and the strategy must pass ALL of them.

Pass rules (kept deliberately simple so a beginner can argue with them):
  1 Look-ahead   Signals computed on data cut off at day X must equal the signals computed
                 on the full data, for every day up to X. Otherwise the strategy is peeking.
  2 Out-of-sample Test (2018+) Sharpe must be above 0 AND at least half the training Sharpe.
  3 Costs        In the test period, Sharpe must beat buy-and-hold of the same asset AND the
                 broad index, at normal costs and at double costs.
  4 Sensitivity  On training data, the neighbouring parameter settings must have a median
                 Sharpe of at least 70% of the chosen setting's, and none may lose money.
  5 Sample size  At least 30 trades over the whole period, else NEEDS MORE DATA.
  6 Drawdown     The worst fall must be no deeper than buy-and-hold's worst fall.
  7 Regimes      In 2008, 2020 and 2022 the strategy must not be worse than buy-and-hold
                 on BOTH return and drawdown at the same time.
  8 Verdict      Any FAIL -> FAIL. Otherwise any "needs more data" -> NEEDS MORE DATA.
                 Demo (synthetic) data can never earn PASS. Otherwise PASS.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from lab import config
from lab.backtest import BacktestResult, buy_and_hold, run_backtest
from lab.metrics import max_drawdown_info, sharpe, summarize

PASS, FAIL, NMD = "PASS", "FAIL", "NEEDS MORE DATA"


@dataclass
class Check:
    number: int
    name: str
    status: str
    finding: str  # one or two plain-English sentences


@dataclass
class AssetEvaluation:
    ticker: str
    strategy_label: str
    is_demo: bool
    periods: dict                 # {"train": (start, end), "test": ..., "full": ...}
    results: dict                 # {(period, who): BacktestResult}; who = strategy / buy_hold / index / strategy_2x
    metrics: pd.DataFrame         # one row per (period, who)
    sensitivity: pd.DataFrame     # 2-D grid of training Sharpe
    sensitivity_params: tuple     # (row param, column param)
    chosen: tuple                 # chosen (row value, column value)
    regimes: pd.DataFrame
    checks: list = field(default_factory=list)
    verdict: str = ""
    reason: str = ""


# --------------------------------------------------------------------------------------
# Check 1: look-ahead bias
# --------------------------------------------------------------------------------------
def lookahead_check(strategy, prices: pd.DataFrame, n_cuts: int = 6) -> tuple[bool, str]:
    """
    The "truncation test". If the strategy only uses the past, then hiding the future
    must not change any signal we already had. We cut the data at several dates and compare.
    """
    full = strategy.generate_signals(prices)
    idx = prices.index
    cut_points = np.linspace(len(idx) * 0.3, len(idx) - 2, n_cuts).astype(int)
    for cut in cut_points:
        partial = strategy.generate_signals(prices.iloc[: cut + 1])
        a = full.iloc[: cut + 1]
        same = (a.isna() & partial.isna()) | (a == partial)
        if not same.all():
            bad_day = a.index[~same.to_numpy()][0]
            return False, (f"Signal on {bad_day.date()} changed when later data was hidden: "
                           "the strategy uses information from the future.")
    return True, f"Signals stayed identical when the future was hidden ({n_cuts} cut-off dates tested)."


# --------------------------------------------------------------------------------------
# The main evaluation
# --------------------------------------------------------------------------------------
def evaluate(strategy, prices: pd.DataFrame, index_prices: pd.DataFrame, ticker: str,
             is_demo: bool = False) -> AssetEvaluation:
    signal = strategy.generate_signals(prices)
    first = signal.first_valid_index()
    # Measure everything from the first day the strategy could act (after warm-up).
    start = prices.index[prices.index.get_loc(first) + 1]
    periods = {
        "train": (start, config.TRAIN_END),
        "test": (config.TEST_START, prices.index[-1]),
        "full": (start, prices.index[-1]),
    }

    results: dict[tuple, BacktestResult] = {}
    for p, (s, e) in periods.items():
        results[(p, "strategy")] = run_backtest(prices, signal, start=s, end=e)
        results[(p, "strategy_2x")] = run_backtest(prices, signal, cost_multiplier=2, start=s, end=e)
        results[(p, "buy_hold")] = buy_and_hold(prices, start=s, end=e)
        results[(p, "index")] = buy_and_hold(index_prices, start=s, end=e)

    rows = []
    for (p, who), res in results.items():
        rows.append({"period": p, "who": who, **summarize(res)})
    metrics = pd.DataFrame(rows).set_index(["period", "who"])

    sens, params, chosen = sensitivity_grid(strategy, prices, periods["train"])
    regimes = regime_table(prices, signal)

    ev = AssetEvaluation(ticker, strategy.label(), is_demo, periods, results, metrics,
                         sens, params, chosen, regimes)
    ev.checks = run_checks(strategy, prices, ev)
    ev.verdict, ev.reason = verdict(ev.checks, is_demo)
    return ev


def sensitivity_grid(strategy, prices, train_period):
    """Training-period Sharpe for every combination of the strategy's two key parameters."""
    grid = strategy.sensitivity_grid()
    (p_row, rows), (p_col, cols) = list(grid.items())[:2]
    s, e = train_period
    table = pd.DataFrame(index=pd.Index(rows, name=p_row), columns=pd.Index(cols, name=p_col), dtype=float)
    for r in rows:
        for c in cols:
            variant = strategy.with_params(**{p_row: r, p_col: c})
            res = run_backtest(prices, variant.generate_signals(prices), start=s, end=e)
            table.loc[r, c] = sharpe(res.returns)
    chosen = (strategy.params[p_row], strategy.params[p_col])
    return table, (p_row, p_col), chosen


def regime_table(prices, signal) -> pd.DataFrame:
    rows = []
    for label, s, e in config.REGIMES:
        if prices.loc[s:e].empty:
            continue
        strat = run_backtest(prices, signal, start=s, end=e)
        bh = buy_and_hold(prices, start=s, end=e)
        rows.append({
            "period": label,
            "strategy_return": strat.equity.iloc[-1] - 1,
            "buy_hold_return": bh.equity.iloc[-1] - 1,
            "strategy_max_dd": max_drawdown_info(strat.equity)["max_dd"],
            "buy_hold_max_dd": max_drawdown_info(bh.equity)["max_dd"],
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# The checklist
# --------------------------------------------------------------------------------------
def run_checks(strategy, prices, ev: AssetEvaluation) -> list[Check]:
    m = ev.metrics
    checks = []

    # 1. Look-ahead
    ok, msg = lookahead_check(strategy, prices)
    checks.append(Check(1, "Look-ahead bias", PASS if ok else FAIL, msg))

    # 2. Out-of-sample
    tr, te = m.loc[("train", "strategy"), "sharpe"], m.loc[("test", "strategy"), "sharpe"]
    ok = te > 0 and te >= 0.5 * tr
    checks.append(Check(2, "Out-of-sample", PASS if ok else FAIL,
        f"Sharpe was {tr:.2f} in training (2005-2017) and {te:.2f} in the 2018+ test. " +
        ("The edge roughly held up on unseen data." if ok else
         "Performance collapsed on data it had never seen, a classic sign of luck or overfitting.")))

    # 3. Costs vs buy-and-hold and broad index (test period)
    s1 = m.loc[("test", "strategy"), "sharpe"]
    s2 = m.loc[("test", "strategy_2x"), "sharpe"]
    bh = m.loc[("test", "buy_hold"), "sharpe"]
    ix = m.loc[("test", "index"), "sharpe"]
    ok = min(s1, s2) > max(bh, ix)
    checks.append(Check(3, "Costs", PASS if ok else FAIL,
        f"Test-period Sharpe after costs {s1:.2f} (double costs {s2:.2f}) vs buy-and-hold {bh:.2f} "
        f"and broad index {ix:.2f}. " +
        ("It still wins on risk-adjusted return after costs." if ok else
         "After costs it does not beat simply buying and holding, so it isn't earning its complexity.")))

    # 4. Parameter sensitivity
    ok, msg = sensitivity_verdict(ev.sensitivity, ev.chosen)
    checks.append(Check(4, "Parameter sensitivity", PASS if ok else FAIL, msg))

    # 5. Sample size
    n_full = int(m.loc[("full", "strategy"), "n_trades"])
    n_test = int(m.loc[("test", "strategy"), "n_trades"])
    ok = n_full >= config.MIN_TRADES
    checks.append(Check(5, "Sample size", PASS if ok else NMD,
        f"{n_full} trades in total ({n_test} in the test period). " +
        ("Enough to say something." if ok else
         f"Fewer than {config.MIN_TRADES}: too few to tell skill from luck.")))

    # 6. Drawdown
    sd = max_drawdown_info(ev.results[("full", "strategy")].equity)
    bd = max_drawdown_info(ev.results[("full", "buy_hold")].equity)
    ok = sd["max_dd"] >= bd["max_dd"]  # drawdowns are negative; "greater" = shallower
    rec = (f"took {sd['recovery_days']} trading days to recover" if sd["recovery_days"] is not None
           else "has not recovered yet")
    checks.append(Check(6, "Drawdown", PASS if ok else FAIL,
        f"Worst fall {sd['max_dd']:.1%} (trough {sd['trough'].date() if sd['trough'] is not None else 'n/a'}, "
        f"{rec}) vs buy-and-hold {bd['max_dd']:.1%}. " +
        ("Shallower than just holding." if ok else "Deeper than just holding: more pain, not less.")))

    # 7. Regimes
    r = ev.regimes
    worse_both = r[(r.strategy_return < r.buy_hold_return) & (r.strategy_max_dd < r.buy_hold_max_dd)]
    ok = worse_both.empty
    parts = [f"{row.period}: {row.strategy_return:+.1%} vs {row.buy_hold_return:+.1%}" for row in r.itertuples()]
    checks.append(Check(7, "Regime check", PASS if ok else FAIL,
        "Strategy vs buy-and-hold: " + "; ".join(parts) + ". " +
        ("No stress period where it was worse on both return and drawdown." if ok else
         "Worse on both return AND drawdown in: " + ", ".join(worse_both.period) + ".")))
    return checks


def sensitivity_verdict(grid: pd.DataFrame, chosen) -> tuple[bool, str]:
    r_vals, c_vals = list(grid.index), list(grid.columns)
    ri, ci = r_vals.index(chosen[0]), c_vals.index(chosen[1])
    centre = grid.iloc[ri, ci]
    neighbours = [grid.iloc[i, j]
                  for i in range(max(ri - 1, 0), min(ri + 2, len(r_vals)))
                  for j in range(max(ci - 1, 0), min(ci + 2, len(c_vals)))
                  if (i, j) != (ri, ci) and not np.isnan(grid.iloc[i, j])]
    med = float(np.median(neighbours)) if neighbours else float("nan")
    ok = centre > 0 and med >= 0.7 * centre and min(neighbours) > 0
    msg = (f"Chosen setting's training Sharpe {centre:.2f}; its {len(neighbours)} neighbours: "
           f"median {med:.2f}, worst {min(neighbours):.2f}. " +
           ("Nearby settings work too, so it isn't a single magic number." if ok else
            "The chosen setting stands out from its neighbours: a 'magic number' that probably fits noise."))
    return ok, msg


def verdict(checks: list[Check], is_demo: bool) -> tuple[str, str]:
    fails = [c for c in checks if c.status == FAIL]
    if fails:
        first = fails[0]
        why = first.finding.split(". ")[-1].rstrip(".")
        return FAIL, (f"It failed {len(fails)} of {len(checks)} checks. Main problem ({first.name.lower()}): "
                      f"{why[0].lower() + why[1:]}.")
    if any(c.status == NMD for c in checks):
        return NMD, "Nothing failed, but there are too few trades to tell skill from luck."
    if is_demo:
        return NMD, "It passed every check, but only on synthetic demo data; re-run on real prices."
    return PASS, "It passed every check on real data, including the untouched 2018+ test period."


def overall_verdict(evaluations: list[AssetEvaluation]) -> str:
    verdicts = [e.verdict for e in evaluations]
    if FAIL in verdicts:
        return FAIL
    if NMD in verdicts:
        return NMD
    return PASS
