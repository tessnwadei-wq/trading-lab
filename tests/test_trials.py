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
