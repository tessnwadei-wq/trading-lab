import pandas as pd

from lab import config
from lab.skeptic import (FAIL, NMD, PASS, WARN, Check, alternatives_comparisons, consistency_check, evaluate,
                         overall_verdict, verdict)
from strategies.ma_trend import MATrend


def checks(*statuses):
    return [Check(i + 1, f"check {i + 1}", s, "finding.") for i, s in enumerate(statuses)]


def test_any_fail_means_fail():
    assert verdict(checks(PASS, PASS, FAIL, NMD), is_demo=False)[0] == FAIL


def test_too_few_trades_means_needs_more_data():
    assert verdict(checks(PASS, PASS, NMD), is_demo=False)[0] == NMD


def test_demo_data_can_never_pass():
    assert verdict(checks(PASS, PASS, PASS), is_demo=True)[0] == NMD
    assert verdict(checks(PASS, PASS, PASS), is_demo=False)[0] == PASS


def test_full_evaluation_answers_all_eight_checks(demo_prices):
    ev = evaluate(MATrend(), demo_prices["SPY"], demo_prices["SPY"], "SPY", is_demo=True)
    assert [c.number for c in ev.checks] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert ev.checks[2].name == "Beats the simple alternatives"
    assert ev.verdict in (FAIL, NMD)  # demo data: never PASS
    assert len(ev.regimes) == 3
    assert ev.sensitivity.shape == (9, 4)
    assert overall_verdict([ev]) == ev.verdict


def test_warn_alone_does_not_fail():
    v, reason = verdict(checks(PASS, WARN, PASS), is_demo=False)
    assert v == PASS and "Warning" in reason
    assert verdict(checks(PASS, WARN, FAIL), is_demo=False)[0] == FAIL


def test_consistency_warns_on_big_swings_either_way():
    gap = config.CONSISTENCY_MAX_SHARPE_GAP
    assert consistency_check(0.63, 0.82).status == PASS
    up = consistency_check(0.25, 0.91)  # the real XIU.TO swing from session 1
    assert up.status == WARN and "jumped" in up.finding and "+0.66" in up.finding
    assert consistency_check(1.0, 1.0 - gap - 0.01).status == WARN
    assert "dropped" in consistency_check(1.0, 0.2).finding


def fake_metrics(strategy, strategy_2x, bh, ix, mix_cagr, strat_cagr=0.10):
    rows = {("test", "strategy"): (strategy, strat_cagr), ("test", "strategy_2x"): (strategy_2x, strat_cagr - 0.01),
            ("test", "buy_hold"): (bh, 0.14), ("test", "buy_hold_2x"): (bh, 0.14),
            ("test", "index"): (ix, 0.14), ("test", "index_2x"): (ix, 0.14),
            ("test", "mix"): (bh, mix_cagr), ("test", "mix_2x"): (bh, mix_cagr)}
    return pd.DataFrame([{"period": p, "who": w, "sharpe": s, "cagr": c} for (p, w), (s, c) in rows.items()]
                        ).set_index(["period", "who"])


def test_alternatives_messages_say_which_comparison_failed_and_by_how_much():
    from lab.skeptic import _describe
    m = fake_metrics(0.91, 0.81, 0.84, 0.82, mix_cagr=0.095)
    comps = alternatives_comparisons(m, "buy-and-hold")
    lost = [c for c in comps if not c["won"]]
    texts = [_describe(c, with_gap=True) for c in lost]
    assert "the broad index (SPY) at double costs (Sharpe 0.81 vs 0.82, short by 0.01)" in texts
    assert any("same-risk mix at double costs (yearly return 9.0% vs 9.5%" in t for t in texts)
    won = [_describe(c, with_gap=False) for c in comps if c["won"]]
    assert "buy-and-hold at normal costs (Sharpe 0.91 vs 0.84)" in won


def test_near_ties_show_three_decimals():
    from lab.skeptic import _pair
    assert _pair(0.8215, 0.8195) == "0.822 vs 0.820"
    assert _pair(0.91, 0.84) == "0.91 vs 0.84"
