"""The over-search counter and its luck bar."""

import pytest

from lab import trials


def test_log_is_append_only_and_skips_exact_repeats(tmp_path):
    path = tmp_path / "trials.csv"
    assert trials.log_trial("idea_a", "SPY", 1, "fixed", path=path, today="2026-01-01")
    assert not trials.log_trial("idea_a", "SPY", 1, "fixed", path=path)  # same test again: not a new try
    assert trials.log_trial("idea_a", "XIU.TO", 1, "fixed", path=path)
    assert trials.log_trial("idea_b", "SPY", 500, "search", path=path)
    assert trials.log_trial("idea_c", "SPY", 9, "search", data="synthetic", path=path)
    t = trials.totals(path)
    assert t == {"configurations": 502, "ideas": 2, "rows": 3}  # synthetic practice runs don't count
    assert trials.trials_for("idea_b", "SPY", path=path) == 500


def test_luck_bar_grows_with_tries_and_shrinks_with_more_years():
    assert trials.luck_bar(1, 10) == 0.0
    assert trials.luck_bar(10, 10) < trials.luck_bar(1000, 10)
    assert trials.luck_bar(1000, 25) < trials.luck_bar(1000, 10)
    # Best of ~2,000 useless strategies over 12 years: a Sharpe near 1 by luck alone.
    assert trials.luck_bar(1920, 12) == pytest.approx(0.99, abs=0.03)


def test_chance_real_falls_as_the_search_grows():
    one = trials.chance_real(0.6, 1, 12)
    many = trials.chance_real(0.6, 2000, 12)
    assert one > 0.95 and many < 0.1


# ---- Test-period looks ------------------------------------------------------------------
def test_each_look_is_logged_with_date_and_reason(tmp_path):
    path = tmp_path / "looks.csv"
    assert trials.log_look("idea_a", "first real run", "abc", path=path, today="2026-10-01")
    assert trials.log_look("idea_a", "after a fix", "def", path=path, today="2026-10-02")
    assert trials.log_look("idea_b", "first", "abc", path=path)          # same numbers, different idea: counts
    looks = trials.looks_for("idea_a", path=path)
    assert [(r["date"], r["reason"]) for r in looks] == [("2026-10-01", "first real run"), ("2026-10-02", "after a fix")]


def test_seeing_the_same_numbers_again_is_not_a_new_look(tmp_path):
    path = tmp_path / "looks.csv"
    fp = trials.results_fingerprint(["SPY", 0.61, 0.093, -0.21, 26])
    assert trials.log_look("idea_a", "run", fp, path=path)
    assert not trials.log_look("idea_a", "re-run, nothing changed", fp, path=path)
    changed = trials.results_fingerprint(["SPY", 0.60, 0.093, -0.21, 26])
    assert changed != fp and trials.log_look("idea_a", "after a change", changed, path=path)
    # Hand-logged (backfilled) looks have no fingerprint and are always added.
    assert trials.log_look("idea_a", "backfilled", "", path=path)
    assert trials.log_look("idea_a", "backfilled", "", path=path)
    assert len(trials.looks_for("idea_a", path=path)) == 4


def test_run_lab_records_a_look_and_the_report_shows_the_count(tmp_path, monkeypatch, demo_prices):
    import run_lab
    from lab import report
    from lab.skeptic import evaluate
    from strategies.ma_trend import MATrend

    monkeypatch.setattr(trials, "LOOKS_CSV", tmp_path / "looks.csv")
    ev = evaluate(MATrend(), demo_prices["SPY"], demo_prices["SPY"], "SPY", is_demo=False)
    run_lab.record_look("ma_trend", [ev], "testing the counter")
    run_lab.record_look("ma_trend", [ev], "same numbers again")      # not a new look
    assert len(trials.looks_for("ma_trend")) == 1
    text = report.looks_section("ma_trend", is_demo=False)
    assert "seen **1 time**" in text and "testing the counter" in text
    assert "looks for this idea: 1" in report.looks_line("ma_trend", is_demo=False)


def test_the_backfilled_session_two_looks_are_in_the_real_log():
    looks = trials.read_looks()
    portfolio = [r for r in looks if r["idea"] == "portfolio_ma_trend" and "Session 2" in r["reason"]]
    assert len(portfolio) == 3
