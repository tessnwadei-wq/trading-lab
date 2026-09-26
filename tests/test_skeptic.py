from lab.skeptic import FAIL, NMD, PASS, Check, evaluate, overall_verdict, verdict
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


def test_full_evaluation_answers_all_seven_checks(demo_prices):
    ev = evaluate(MATrend(), demo_prices["SPY"], demo_prices["SPY"], "SPY", is_demo=True)
    assert [c.number for c in ev.checks] == [1, 2, 3, 4, 5, 6, 7]
    assert ev.verdict in (FAIL, NMD)  # demo data: never PASS
    assert len(ev.regimes) == 3
    assert ev.sensitivity.shape == (9, 4)
    assert overall_verdict([ev]) == ev.verdict
