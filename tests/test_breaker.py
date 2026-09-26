"""
The circuit breaker must wait for a person.

Paper mode: after a 10% fall, nothing restarts by itself; only a logged manual reset (who, when, why).
Backtest mode: a person can't press reset in a simulation, so a fixed, documented review period is assumed.
"""

import csv
from datetime import datetime

import pandas as pd
import pytest

import reset_circuit_breaker
from lab import config
from lab.breaker import BACKTEST, PAPER, CircuitBreaker

DAYS = pd.bdate_range("2030-01-01", periods=400)


def fall_then_flat(b: CircuitBreaker, days=300):
    """Account rises to 1.10, falls 12% to 0.968, then stays flat for a long time."""
    path = [1.0, 1.05, 1.10, 0.968] + [0.968] * days
    for i, v in enumerate(path):
        b.update(i, DAYS[i], v)
    return len(path)


def test_paper_breaker_never_restarts_by_itself():
    b = CircuitBreaker(mode=PAPER)
    fall_then_flat(b, days=300)          # more than a year later...
    assert b.tripped and not b.allows_new_trades   # ...still blocked
    assert b.events[0]["resumed"] is None


def test_manual_reset_needs_a_name_and_a_reason(tmp_path):
    b = CircuitBreaker(mode=PAPER)
    fall_then_flat(b)
    log = tmp_path / "resets.csv"
    for who, reason in (("", "reviewed"), ("Tessy", ""), (None, None), ("  ", "  ")):
        with pytest.raises(ValueError, match="WHO|REASON"):
            b.reset(who, reason, log_path=log)
    assert not b.allows_new_trades and not log.exists()


def test_manual_reset_is_logged_and_restarts_from_the_current_value(tmp_path):
    b = CircuitBreaker(mode=PAPER)
    n = fall_then_flat(b)
    log = tmp_path / "resets.csv"
    row = b.reset("Tessy", "Reviewed: normal market fall, rules followed", when=datetime(2031, 3, 2, 9, 30),
                  log_path=log)
    assert b.allows_new_trades
    assert b.peak == pytest.approx(0.968)           # the new peak is today's value
    rows = list(csv.DictReader(log.open()))
    assert rows == [row]
    assert rows[0]["who"] == "Tessy" and rows[0]["reset_at"] == "2031-03-02T09:30:00"
    assert rows[0]["reason"].startswith("Reviewed") and rows[0]["tripped_on"] == str(DAYS[3].date())
    assert b.events[0]["resumed_by"].startswith("manual reset by Tessy")
    # A small wobble after the reset doesn't re-trip it (it is measured from the new peak).
    b.update(n, DAYS[n], 0.95)
    assert b.allows_new_trades


def test_reset_is_refused_when_nothing_is_tripped(tmp_path):
    b = CircuitBreaker(mode=PAPER)
    b.update(0, DAYS[0], 1.0)
    with pytest.raises(ValueError, match="not tripped"):
        b.reset("Tessy", "just because", log_path=tmp_path / "r.csv")


def test_backtests_cannot_be_reset_by_hand():
    b = CircuitBreaker(mode=BACKTEST)
    fall_then_flat(b, days=1)
    with pytest.raises(RuntimeError, match="review"):
        b.reset("Tessy", "reason")


def test_backtest_resumes_after_the_configured_review_period():
    b = CircuitBreaker(mode=BACKTEST)
    fall_then_flat(b, days=config.CIRCUIT_BREAKER_REVIEW_DAYS + 5)
    event = b.events[0]
    assert DAYS.get_loc(event["resumed"]) - DAYS.get_loc(event["tripped"]) == config.CIRCUIT_BREAKER_REVIEW_DAYS
    assert "simulated" in event["resumed_by"] and b.allows_new_trades


def test_review_days_is_set_in_config():
    assert config.CIRCUIT_BREAKER_REVIEW_DAYS == 21


def test_hard_floor_needs_a_manual_reset_in_paper_mode(tmp_path):
    b = CircuitBreaker(mode=PAPER)
    for i, v in enumerate([1.0, 0.89, 0.89]):
        b.update(i, DAYS[i], v)
    b.reset("Tessy", "first review", log_path=tmp_path / "r.csv")
    for i, v in enumerate([0.78, 0.78], start=3):   # a second fall: 22% below the all-time high of 1.0
        b.update(i, DAYS[i], v)
    assert b.halted and not b.allows_new_trades
    row = b.reset("Tessy", "second review", log_path=tmp_path / "r.csv")
    assert row["kind"] == "hard floor" and b.allows_new_trades
    assert len(list(csv.DictReader((tmp_path / "r.csv").open()))) == 2


def test_state_survives_save_and_load(tmp_path):
    b = CircuitBreaker(mode=PAPER)
    fall_then_flat(b, days=2)
    b.save(tmp_path / "state.json")
    again = CircuitBreaker.load(tmp_path / "state.json")
    assert again.tripped and again.mode == PAPER and again.last_equity == pytest.approx(0.968)


def test_reset_command(tmp_path, capsys):
    state, log = tmp_path / "state.json", tmp_path / "resets.csv"
    # No paper account yet: nothing to reset.
    assert reset_circuit_breaker.main(["--status"], state, log) == 1
    b = CircuitBreaker(mode=PAPER)
    fall_then_flat(b, days=2)
    b.save(state)
    assert reset_circuit_breaker.main(["--status"], state, log) == 0
    assert "TRIPPED" in capsys.readouterr().out
    assert reset_circuit_breaker.main(["--who", "Tessy"], state, log) == 1          # no reason: refused
    assert not log.exists()
    assert reset_circuit_breaker.main(["--who", "Tessy", "--reason", "Reviewed"], state, log) == 0
    assert CircuitBreaker.load(state).allows_new_trades
    assert list(csv.DictReader(log.open()))[0]["who"] == "Tessy"
