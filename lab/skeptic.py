"""
The Skeptic: automates as much of the Skeptic Checklist (CLAUDE.md) as a computer can.

Default stance: a good result is luck or overfitting until proven otherwise. So every
check has a clear, written rule, and the strategy must pass ALL of them.

Each check gives one of:
  PASS             fine.
  WARN             worth knowing and shown in the report, but does NOT fail the strategy on its own.
  FAIL             the strategy fails.
  NEEDS MORE DATA  can't tell yet (too few trades).

The rules (kept deliberately simple so a beginner can argue with them):
  1 Look-ahead   Two tests, both must pass:
                 (a) Truncation: signals computed on data cut off at day X must equal the signals
                     computed on the full data, for every day up to X. Otherwise the STRATEGY peeks.
                 (b) Trade timing: the ENGINE must trade at a close after the one it decided on. We
                     change one day's closing price (x3, then /3) and check that what was held
                     over the following day did not change. A backtest that buys at the same close
                     it used to decide (the lab's old "same_close" timing) fails this test.
  2 Out-of-sample Test (2018+) Sharpe must be above 0 AND at least half the training Sharpe.
  3 Beats the simple alternatives
                 In the test period, after costs, the strategy must beat three simple things you
                 could do instead, at normal costs AND at double costs (everyone's costs doubled):
                   * buy-and-hold of the same asset  (compared on Sharpe ratio)
                   * the broad index, SPY            (compared on Sharpe ratio)
                   * the same-risk mix               (compared on yearly return, CAGR)
                   * the equal-risk mix              (compared on yearly return, CAGR)
                 Why CAGR for the mixes: a mix is built to be as bumpy as the strategy, so at equal
                 risk the fair question is simply "who earned more?". (Its Sharpe is almost identical
                 to buy-and-hold's, so a Sharpe comparison would just repeat that test.)
                 The same-risk mix is sized on TRAINING data, so in the test period the strategy can
                 end up bumpier than it and "win" just by taking more risk (vol_target did this). The
                 equal-risk mix (session 5) closes that loophole: the same mix, rescaled so that its
                 TEST-period volatility equals the strategy's TEST-period volatility. This is allowed
                 to use test-period data because it is a yardstick for judging, never a strategy
                 decision: nothing about the strategy changes. Losing to it = FAIL.
  4 Sensitivity  On training data, the neighbouring parameter settings must have a median
                 Sharpe of at least 70% of the chosen setting's, and none may lose money.
  5 Sample size  At least 30 trades over the whole period, else NEEDS MORE DATA.
                 Strategies that are always partly invested (sample_size_rule = "rebalances", e.g. vol_target)
                 use their pre-registered rule instead: at least 30 "active rebalances" (weight changes of 5
                 percentage points or more) AND at least 5 years of test period.
  6 Drawdown     The worst fall must be no deeper than buy-and-hold's worst fall.
  7 Regimes      In 2008, 2020 and 2022 the strategy must not be worse than buy-and-hold
                 on BOTH return and drawdown at the same time.
  8 Consistency  WARN if the test Sharpe differs from the training Sharpe by more than
                 config.CONSISTENCY_MAX_SHARPE_GAP in EITHER direction. A big swing usually means
                 the period drove the result rather than a steady edge. (A warning, not a fail.)
  9 Verdict      Any FAIL -> FAIL. Otherwise any "needs more data" -> NEEDS MORE DATA.
                 Demo (synthetic) data can never earn PASS. Otherwise PASS (warnings are listed).

All Sharpe ratios are measured on returns above the cash (T-bill) rate. See lab/metrics.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from lab import config
from lab.backtest import BacktestResult, buy_and_hold, fixed_mix, run_backtest
from strategies.base import Strategy
from lab.metrics import max_drawdown_info, result_sharpe, summarize, volatility

PASS, WARN, FAIL, NMD = "PASS", "WARN", "FAIL", "NEEDS MORE DATA"

# Who is compared with whom. "_2x" = the same thing with double trading costs.
WHO = ["strategy", "strategy_2x", "buy_hold", "buy_hold_2x", "index", "index_2x", "mix", "mix_2x"]
# Plus, in the test period only: "eqmix" and "eqmix_2x", the equal-risk mix (see equal_risk_weight).


@dataclass
class Check:
    number: int
    name: str
    status: str
    finding: str       # one or two plain-English sentences
    headline: str = ""  # a short "what went wrong", used in the verdict sentence


@dataclass
class Subject:
    """
    Everything the skeptic needs to judge one thing: a strategy on one asset, or a portfolio.
    The run_* functions all take (start, end, cost_multiplier) and return a BacktestResult.
    """
    ticker: str                 # heading in the report, e.g. "SPY" or "Portfolio"
    label: str                  # strategy with its parameters
    benchmark_name: str         # e.g. "buy-and-hold"
    first_day: pd.Timestamp     # first day the strategy can act (after its warm-up)
    last_day: pd.Timestamp
    run_strategy: Callable
    run_benchmark: Callable     # buy-and-hold of the same asset(s)
    run_index: Callable         # the broad index (SPY)
    run_mix: Callable           # (weight, start, end, cost_multiplier): weight in the benchmark, rest in cash
    lookahead: Callable         # () -> (ok, message)
    sensitivity: Callable       # (train_start, train_end) -> (grid, (row param, col param), chosen)
    run_same_close: Callable = None  # (start, end): the strategy with the OLD same-close timing, for
                                     # the report's "Timing cost" table only. Never used to judge.
    sample_size_rule: str = "trades"  # "trades" (round trips) or "rebalances" (always-partly-invested strategies)


@dataclass
class AssetEvaluation:
    ticker: str
    strategy_label: str
    is_demo: bool
    periods: dict                 # {"train": (start, end), "test": ..., "full": ...}
    results: dict                 # {(period, who): BacktestResult}, who in WHO
    metrics: pd.DataFrame         # one row per (period, who)
    sensitivity: pd.DataFrame     # 2-D grid of training Sharpe
    sensitivity_params: tuple     # (row param, column param)
    chosen: tuple                 # chosen (row value, column value)
    regimes: pd.DataFrame
    timing: pd.DataFrame = None   # key metrics under same-close vs next-close execution
    mix_weight: float = 1.0       # share of the account in the asset(s) for the same-risk mix
    eq_mix_weight: float = 1.0    # the same for the equal-risk mix (test period only)
    benchmark_name: str = "buy-and-hold"
    sample_size_rule: str = "trades"
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


class PriceRoseProbe(Strategy):
    """
    Not a trading idea: a test probe. "Be invested if today's close is above yesterday's."
    It reacts to EVERY day's closing price, so if the engine ever trades at the same close it
    decided on, changing that close is guaranteed to change what gets held.
    """
    name = "price_rose_probe"

    def generate_signals(self, prices):
        close = prices["Close"]
        signal = (close > close.shift(1)).astype(float)
        signal.iloc[0] = np.nan
        return signal


def _probe_days(n: int, n_days: int, warm_up: int) -> list[int]:
    return sorted(set(np.linspace(warm_up, n - 3, n_days).astype(int)))


def _shocked(prices: pd.DataFrame, k: int, factor: float) -> pd.DataFrame:
    """A copy of prices up to day k+2, with day k's closing price multiplied by `factor`."""
    out = prices.iloc[: k + 3].copy()
    out.iloc[k, out.columns.get_loc("Close")] *= factor
    return out


def execution_timing_check(prices: pd.DataFrame, execution: str | None = None,
                           n_days: int = 8) -> tuple[bool, str]:
    """
    The trade-timing test for the single-asset backtester.

    Idea: the position that earns the move from close k to close k+1 must already have been bought
    at (or before) close k. If we traded at a later close than we decided on, that position was
    decided from data up to close k-1, so changing close k can't change it. We push close k up x3
    and down to a third, with the probe strategy, and compare what was held over day k+1.
    """
    probe = PriceRoseProbe()
    days = _probe_days(len(prices), n_days, warm_up=5)
    for k in days:
        held = []
        for factor in (3.0, 1 / 3):
            p = _shocked(prices, k, factor)
            held.append(run_backtest(p, probe.generate_signals(p), execution=execution).position.iloc[: k + 2])
        if not held[0].equals(held[1]):
            day = prices.index[k].date()
            return False, (f"Changing the closing price of {day} changed what was held right after that close: "
                           "the backtest trades at the same closing price it used to decide (look-ahead).")
    return True, (f"Trades happen at the close after the decision: changing a decision day's closing price "
                  f"never changed what was held over the next day ({len(days)} days tested).")


def full_lookahead_check(strategy, prices: pd.DataFrame, execution: str | None = None) -> tuple[bool, str]:
    """Check 1: the strategy's signals don't peek (truncation) AND the engine trades after deciding (timing)."""
    ok, msg = lookahead_check(strategy, prices)
    if not ok:
        return ok, msg
    ok2, msg2 = execution_timing_check(prices, execution)
    return ok2, msg + " " + msg2


# --------------------------------------------------------------------------------------
# The same-risk mix
# --------------------------------------------------------------------------------------
def same_risk_weight(strategy_train: BacktestResult, benchmark_train: BacktestResult) -> float:
    """
    X for the same-risk mix: how much of the asset (the rest in cash) gives the same bumpiness
    as the strategy. Measured on TRAINING data only, then frozen for the test period, so the
    benchmark never uses information from the future. Capped at 100% (no borrowing).
    """
    bench_vol = volatility(benchmark_train.returns)
    if bench_vol <= 0:
        return 1.0
    return float(np.clip(volatility(strategy_train.returns) / bench_vol, 0.0, 1.0))


def equal_risk_weight(mix_weight: float, strategy_test: BacktestResult, mix_test: BacktestResult) -> float:
    """
    X for the EQUAL-RISK mix: the same-risk mix rescaled so that, in the TEST period, it is exactly as bumpy
    as the strategy was in the test period. Mixing an asset with cash scales volatility in proportion to the
    share invested, so if the strategy was 10% bumpier than the mix, the equal-risk mix holds 10% more.

    Using test-period data is allowed here: this is a yardstick for JUDGING the result, not a strategy
    decision (nothing about the strategy changes). It stops a strategy "winning" by simply taking more risk
    than a mix that was sized on training data. Capped at 100% (no borrowing), so a strategy that is bumpier
    than the asset itself is compared with 100% of the asset.
    """
    mix_vol = volatility(mix_test.returns)
    if mix_vol <= 0 or mix_weight <= 0:
        return float(np.clip(mix_weight, 0.0, 1.0))
    return float(np.clip(mix_weight * volatility(strategy_test.returns) / mix_vol, 0.0, 1.0))


# --------------------------------------------------------------------------------------
# The main evaluation
# --------------------------------------------------------------------------------------
def evaluate(strategy, prices: pd.DataFrame, index_prices: pd.DataFrame, ticker: str,
             is_demo: bool = False, cash_rate: pd.Series | None = None,
             execution: str | None = None) -> AssetEvaluation:
    """Judge one strategy on one asset. execution defaults to config.EXECUTION ("next_close")."""
    execution = execution or config.EXECUTION
    signal = strategy.generate_signals(prices)
    first = signal.first_valid_index()
    # Measure everything from the first day the strategy could act (after warm-up).
    start = prices.index[prices.index.get_loc(first) + 1]

    def run_variant(variant, s, e, cost_multiplier=1.0):
        return run_backtest(prices, variant.generate_signals(prices), cost_multiplier, s, e, cash_rate, execution)

    subject = Subject(
        ticker=ticker, label=strategy.label(), benchmark_name="buy-and-hold",
        first_day=start, last_day=prices.index[-1],
        run_strategy=lambda s, e, m=1.0: run_backtest(prices, signal, m, s, e, cash_rate, execution),
        run_benchmark=lambda s, e, m=1.0: buy_and_hold(prices, s, e, m, cash_rate, execution),
        run_index=lambda s, e, m=1.0: buy_and_hold(index_prices, s, e, m, cash_rate, execution),
        run_mix=lambda w, s, e, m=1.0: fixed_mix(prices[["Close"]], {"Close": w}, s, e, m, cash_rate, execution),
        lookahead=lambda: full_lookahead_check(strategy, prices, execution),
        sensitivity=lambda s, e: sensitivity_grid(strategy, lambda v: run_variant(v, s, e)),
        run_same_close=lambda s, e: run_backtest(prices, signal, 1.0, s, e, cash_rate, "same_close"),
        sample_size_rule=getattr(strategy, "sample_size_rule", "trades"),
    )
    return evaluate_subject(subject, is_demo)


def evaluate_subject(subject: Subject, is_demo: bool = False) -> AssetEvaluation:
    """Run every backtest the checklist needs, then the checklist itself."""
    periods = {
        "train": (subject.first_day, config.TRAIN_END),
        "test": (config.TEST_START, subject.last_day),
        "full": (subject.first_day, subject.last_day),
    }

    results: dict[tuple, BacktestResult] = {}
    for p, (s, e) in periods.items():
        for mult, suffix in ((1.0, ""), (2.0, "_2x")):
            results[(p, "strategy" + suffix)] = subject.run_strategy(s, e, mult)
            results[(p, "buy_hold" + suffix)] = subject.run_benchmark(s, e, mult)
            results[(p, "index" + suffix)] = subject.run_index(s, e, mult)

    # Same-risk mix: X chosen on training data, then used unchanged in every period.
    weight = same_risk_weight(results[("train", "strategy")], results[("train", "buy_hold")])
    for p, (s, e) in periods.items():
        results[(p, "mix")] = subject.run_mix(weight, s, e, 1.0)
        results[(p, "mix_2x")] = subject.run_mix(weight, s, e, 2.0)

    # Equal-risk mix: the same mix, rescaled to the strategy's TEST-period volatility. Test period only.
    eq_weight = equal_risk_weight(weight, results[("test", "strategy")], results[("test", "mix")])
    results[("test", "eqmix")] = subject.run_mix(eq_weight, *periods["test"], 1.0)
    results[("test", "eqmix_2x")] = subject.run_mix(eq_weight, *periods["test"], 2.0)

    rows = [{"period": p, "who": who, **summarize(res)} for (p, who), res in results.items()]
    metrics = pd.DataFrame(rows).set_index(["period", "who"])

    sens, params, chosen = subject.sensitivity(*periods["train"])
    regimes = regime_table(subject)
    timing = timing_table(subject, periods, results)

    ev = AssetEvaluation(subject.ticker, subject.label, is_demo, periods, results, metrics,
                         sens, params, chosen, regimes, timing, weight, eq_weight, subject.benchmark_name,
                         subject.sample_size_rule)
    ev.checks = run_checks(subject, ev)
    ev.verdict, ev.reason = verdict(ev.checks, is_demo)
    return ev


def sensitivity_grid(strategy, run_variant: Callable):
    """Training-period Sharpe for every combination of the strategy's two key parameters."""
    grid = strategy.sensitivity_grid()
    (p_row, rows), (p_col, cols) = list(grid.items())[:2]
    table = pd.DataFrame(index=pd.Index(rows, name=p_row), columns=pd.Index(cols, name=p_col), dtype=float)
    for r in rows:
        for c in cols:
            table.loc[r, c] = result_sharpe(run_variant(strategy.with_params(**{p_row: r, p_col: c})))
    chosen = (strategy.params[p_row], strategy.params[p_col])
    return table, (p_row, p_col), chosen


def timing_table(subject: Subject, periods: dict, results: dict) -> pd.DataFrame | None:
    """
    The "Timing cost" table: the strategy's key numbers with the old same-close timing next to the
    real (next-close) ones, at normal costs. It only DESCRIBES how optimistic the old timing was;
    no check or verdict uses the same-close numbers.
    """
    if subject.run_same_close is None:
        return None
    rows = []
    for p, (s, e) in periods.items():
        for execution, res in (("same_close", subject.run_same_close(s, e)), ("next_close", results[(p, "strategy")])):
            rows.append({"period": p, "execution": execution, **summarize(res)})
    return pd.DataFrame(rows).set_index(["period", "execution"])


def regime_table(subject: Subject) -> pd.DataFrame:
    rows = []
    for label, s, e in config.REGIMES:
        if pd.Timestamp(e) < subject.first_day or pd.Timestamp(s) > subject.last_day:
            continue
        strat = subject.run_strategy(s, e, 1.0)
        bh = subject.run_benchmark(s, e, 1.0)
        rows.append({
            "period": label,
            "strategy_return": strat.equity.iloc[-1] - 1,
            "buy_hold_return": bh.equity.iloc[-1] - 1,
            "strategy_max_dd": max_drawdown_info(strat.equity)["max_dd"],
            "buy_hold_max_dd": max_drawdown_info(bh.equity)["max_dd"],
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# Wording helpers: always say which comparison, and by how much
# --------------------------------------------------------------------------------------
def _pair(a: float, b: float, pct: bool = False) -> str:
    """'0.91 vs 0.84', switching to 3 decimals when 2 would make different numbers look equal."""
    if pct:
        d = 1 if round(a * 100, 1) != round(b * 100, 1) else 2
        return f"{a * 100:.{d}f}% vs {b * 100:.{d}f}%"
    d = 2 if round(a, 2) != round(b, 2) else 3
    return f"{a:.{d}f} vs {b:.{d}f}"


def _gap(a: float, b: float, pct: bool = False) -> str:
    if pct:
        return f"{abs(a - b) * 100:.1f} percentage points a year" if abs(a - b) >= 0.0005 else \
            f"{abs(a - b) * 100:.2f} percentage points a year"
    return f"{abs(a - b):.2f}" if abs(a - b) >= 0.005 else f"{abs(a - b):.3f}"


def alternatives_comparisons(m: pd.DataFrame, benchmark_name: str) -> list[dict]:
    """The comparisons behind check 3, in the test period (each at normal and at double costs)."""
    out = []
    for cost_label, sfx in (("normal costs", ""), ("double costs", "_2x")):
        strat = m.loc[("test", "strategy" + sfx)]
        for who, name, metric in (("buy_hold", benchmark_name, "sharpe"),
                                  ("index", "the broad index (SPY)", "sharpe"),
                                  ("mix", "the same-risk mix", "cagr"),
                                  ("eqmix", "the equal-risk mix", "cagr")):
            if ("test", who + sfx) not in m.index:
                continue
            other = m.loc[("test", who + sfx)]
            a, b = float(strat[metric]), float(other[metric])
            out.append({"costs": cost_label, "name": name, "metric": metric,
                        "strategy": a, "other": b, "won": a > b})
    return out


def _describe(c: dict, with_gap: bool) -> str:
    pct = c["metric"] == "cagr"
    what = "yearly return" if pct else "Sharpe"
    text = f"{c['name']} at {c['costs']} ({what} {_pair(c['strategy'], c['other'], pct)}"
    if with_gap:
        text += f", {'ahead' if c['won'] else 'short'} by {_gap(c['strategy'], c['other'], pct)}"
    return text + ")"


# --------------------------------------------------------------------------------------
# The checklist
# --------------------------------------------------------------------------------------
def run_checks(subject: Subject, ev: AssetEvaluation) -> list[Check]:
    m = ev.metrics
    bench = ev.benchmark_name
    checks = []

    # 1. Look-ahead
    ok, msg = subject.lookahead()
    checks.append(Check(1, "Look-ahead bias", PASS if ok else FAIL, msg,
                        "a decision used data it could not have had when it traded"))

    # 2. Out-of-sample
    tr, te = m.loc[("train", "strategy"), "sharpe"], m.loc[("test", "strategy"), "sharpe"]
    ok = te > 0 and te >= 0.5 * tr
    checks.append(Check(2, "Out-of-sample", PASS if ok else FAIL,
        f"Sharpe was {tr:.2f} in training (2005-2017) and {te:.2f} in the 2018+ test. " +
        ("The edge roughly held up on unseen data." if ok else
         "Performance collapsed on data it had never seen, a classic sign of luck or overfitting."),
        f"test Sharpe {te:.2f} vs training {tr:.2f}"))

    # 3. Beats the simple alternatives (test period, after costs)
    comps = alternatives_comparisons(m, bench)
    won = [c for c in comps if c["won"]]
    lost = [c for c in comps if not c["won"]]
    parts = []
    if won:
        parts.append("Beat " + "; ".join(_describe(c, with_gap=False) for c in won) + ".")
    if lost:
        parts.append(("But fell short of " if won else "Fell short of ") +
                     "; ".join(_describe(c, with_gap=True) for c in lost) + ".")
    x = ev.mix_weight
    where = 'in the assets' if subject.ticker == 'Portfolio' else 'in ' + subject.ticker
    xe = ev.eq_mix_weight
    parts.append(f"(Same-risk mix = {x:.0%} {where} + {1 - x:.0%} in cash, sized on 2005-2017 data. "
                 f"Equal-risk mix = {xe:.0%} {where} + {1 - xe:.0%} in cash, the same mix rescaled so its 2018+ "
                 f"volatility matches the strategy's 2018+ volatility"
                 + (", capped at 100% because there's no borrowing" if xe >= 1.0 else "") + ".)")
    headline = ("it fell short of " + "; ".join(_describe(c, with_gap=True) for c in lost)) if lost else ""
    checks.append(Check(3, "Beats the simple alternatives", PASS if not lost else FAIL,
                        " ".join(parts), headline))

    # 4. Parameter sensitivity
    ok, msg = sensitivity_verdict(ev.sensitivity, ev.chosen)
    checks.append(Check(4, "Parameter sensitivity", PASS if ok else FAIL, msg,
                        "the chosen setting is a lone 'magic number'"))

    # 5. Sample size
    if ev.sample_size_rule == "rebalances":
        checks.append(rebalance_sample_check(ev))
    else:
        n_full = int(m.loc[("full", "strategy"), "n_trades"])
        n_test = int(m.loc[("test", "strategy"), "n_trades"])
        ok = n_full >= config.MIN_TRADES
        checks.append(Check(5, "Sample size", PASS if ok else NMD,
            f"{n_full} trades in total ({n_test} in the test period). " +
            ("Enough to say something." if ok else
             f"Fewer than {config.MIN_TRADES}: too few to tell skill from luck."),
            f"only {n_full} trades"))

    # 6. Drawdown
    sd = max_drawdown_info(ev.results[("full", "strategy")].equity)
    bd = max_drawdown_info(ev.results[("full", "buy_hold")].equity)
    ok = sd["max_dd"] >= bd["max_dd"]  # drawdowns are negative; "greater" = shallower
    rec = (f"took {sd['recovery_days']} trading days to recover" if sd["recovery_days"] is not None
           else "has not recovered yet")
    checks.append(Check(6, "Drawdown", PASS if ok else FAIL,
        f"Worst fall {sd['max_dd']:.1%} (trough {sd['trough'].date() if sd['trough'] is not None else 'n/a'}, "
        f"{rec}) vs {bench} {bd['max_dd']:.1%}. " +
        ("Shallower than just holding." if ok else "Deeper than just holding: more pain, not less."),
        f"worst fall {sd['max_dd']:.1%} vs {bench} {bd['max_dd']:.1%}"))

    # 7. Regimes
    r = ev.regimes
    worse_both = r[(r.strategy_return < r.buy_hold_return) & (r.strategy_max_dd < r.buy_hold_max_dd)]
    ok = worse_both.empty
    parts = [f"{row.period}: {row.strategy_return:+.1%} vs {row.buy_hold_return:+.1%}" for row in r.itertuples()]
    checks.append(Check(7, "Regime check", PASS if ok else FAIL,
        f"Strategy vs {bench}: " + "; ".join(parts) + ". " +
        ("No stress period where it was worse on both return and drawdown." if ok else
         "Worse on both return AND drawdown in: " + ", ".join(worse_both.period) + "."),
        "worse on both return and drawdown in " + ", ".join(worse_both.period)))

    # 8. Consistency (a warning, never a fail)
    checks.append(consistency_check(tr, te))
    return checks


def rebalance_sample_check(ev: AssetEvaluation) -> Check:
    """
    Check 5 for always-partly-invested strategies (pre-registered in strategies/specs/vol_target.md, section 7):
    count "active rebalances" (weight changes of at least 5 percentage points) instead of round-trip trades,
    and require a test period of at least 5 years.
    """
    step = config.ACTIVE_REBALANCE_MIN_CHANGE
    full, test = ev.results[("full", "strategy")], ev.results[("test", "strategy")]
    n_full, n_test = full.rebalances(step), test.rebalances(step)
    all_full = full.rebalances()
    s, e = ev.periods["test"]
    years = (pd.Timestamp(e) - pd.Timestamp(s)).days / 365.25
    ok = n_full >= config.MIN_ACTIVE_REBALANCES and years >= config.MIN_TEST_YEARS
    finding = (f"This strategy is always partly invested, so it is judged by its pre-registered rule, not by "
               f"round trips: {n_full} active rebalances (weight changes of {step * 100:.0f} percentage points or more) in total, "
               f"{n_test} of them in the test period (out of {all_full} rebalances of any size), and "
               f"{years:.1f} years of test period. Needs at least {config.MIN_ACTIVE_REBALANCES} and "
               f"{config.MIN_TEST_YEARS} years. " +
               ("Enough to say something." if ok else "Too little evidence to tell skill from luck."))
    return Check(5, "Sample size", PASS if ok else NMD, finding,
                 f"only {n_full} active rebalances" if n_full < config.MIN_ACTIVE_REBALANCES
                 else f"only {years:.1f} years of test period")


def consistency_check(train_sharpe: float, test_sharpe: float) -> Check:
    gap = test_sharpe - train_sharpe
    limit = config.CONSISTENCY_MAX_SHARPE_GAP
    if abs(gap) <= limit:
        return Check(8, "Consistency", PASS,
            f"Sharpe went from {train_sharpe:.2f} (training) to {test_sharpe:.2f} (test), a change of "
            f"{gap:+.2f}, within the ±{limit:.1f} expected from normal ups and downs. Behaviour was steady.")
    direction = "jumped" if gap > 0 else "dropped"
    return Check(8, "Consistency", WARN,
        f"Sharpe {direction} from {train_sharpe:.2f} (training) to {test_sharpe:.2f} (test), a change of "
        f"{gap:+.2f}, bigger than the ±{limit:.1f} that normal ups and downs explain. A swing this big "
        "usually means the period drove the result (the market happened to suit or not suit the rule) "
        "rather than a steady edge, so don't lean on either number alone.",
        f"Sharpe {direction} {train_sharpe:.2f} → {test_sharpe:.2f}")


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
    warns = [c for c in checks if c.status == WARN]
    warn_note = ("" if not warns else
                 f" Warning{'s' if len(warns) > 1 else ''}: " +
                 "; ".join(f"{c.name.lower()} ({c.headline or 'see check'})" for c in warns) + ".")
    if fails:
        first = fails[0]
        return FAIL, (f"It failed {len(fails)} of {len(checks)} checks. Main problem ({first.name.lower()}): "
                      f"{first.headline or first.finding}." + warn_note)
    if any(c.status == NMD for c in checks):
        return NMD, "Nothing failed, but there are too few trades to tell skill from luck." + warn_note
    if is_demo:
        return NMD, "It passed every check, but only on synthetic demo data; re-run on real prices." + warn_note
    return PASS, "It passed every check on real data, including the untouched 2018+ test period." + warn_note


def overall_verdict(evaluations: list[AssetEvaluation]) -> str:
    verdicts = [e.verdict for e in evaluations]
    if FAIL in verdicts:
        return FAIL
    if NMD in verdicts:
        return NMD
    return PASS
