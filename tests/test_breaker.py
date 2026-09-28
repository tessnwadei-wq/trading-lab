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
from lab.breaker import BACKTEST, PAPER, CircuitBreaker, ResetLogTampered, verify_reset_log

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
            b.reset(who, reason, log_path=log, confirmation="RESET")
    assert not b.allows_new_trades and not log.exists()


def test_manual_reset_is_logged_and_restarts_from_the_current_value(tmp_path):
    b = CircuitBreaker(mode=PAPER)
    n = fall_then_flat(b)
    log = tmp_path / "resets.csv"
    row = b.reset("Tessy", "Reviewed: normal market fall, rules followed", when=datetime(2031, 3, 2, 9, 30),
                  log_path=log, confirmation="RESET")
    assert b.allows_new_trades
    assert b.peak == pytest.approx(0.968)           # the new peak is today's value
    rows = list(csv.DictReader(log.open()))
    assert rows == [{**row, "log_sha256_before": rows[0]["log_sha256_before"]}]
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
        b.reset("Tessy", "just because", log_path=tmp_path / "r.csv", confirmation="RESET")


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
    b.reset("Tessy", "first review", log_path=tmp_path / "r.csv", confirmation="RESET")
    for i, v in enumerate([0.78, 0.78], start=3):   # a second fall: 22% below the all-time high of 1.0
        b.update(i, DAYS[i], v)
    assert b.halted and not b.allows_new_trades
    with pytest.raises(ValueError, match="HARD FLOOR"):   # the extra confirmation is required
        b.reset("Tessy", "second review", log_path=tmp_path / "r.csv", confirmation="RESET")
    row = b.reset("Tessy", "second review", log_path=tmp_path / "r.csv", confirmation="RESET",
                  hard_floor_confirmation="HARD FLOOR")
    assert row["kind"] == "hard floor" and b.allows_new_trades
    assert len(list(csv.DictReader((tmp_path / "r.csv").open()))) == 2


def test_state_survives_save_and_load(tmp_path):
    b = CircuitBreaker(mode=PAPER)
    fall_then_flat(b, days=2)
    b.save(tmp_path / "state.json")
    again = CircuitBreaker.load(tmp_path / "state.json")
    assert again.tripped and again.mode == PAPER and again.last_equity == pytest.approx(0.968)


def typist(*answers):
    """Plays a person typing answers at the prompts, in order."""
    it = iter(answers)
    return lambda prompt="": next(it)


def test_reset_command(tmp_path, capsys):
    state, log = tmp_path / "state.json", tmp_path / "resets.csv"
    # No paper account yet: nothing to reset.
    assert reset_circuit_breaker.main(["--status"], state, log) == 1
    b = CircuitBreaker(mode=PAPER)
    fall_then_flat(b, days=2)
    b.save(state)
    assert reset_circuit_breaker.main(["--status"], state, log) == 0
    assert "TRIPPED" in capsys.readouterr().out
    # No reason: refused.
    assert reset_circuit_breaker.main(["--who", "Tessy"], state, log, typist("RESET"), interactive=True) == 1
    assert not log.exists()
    ok = ["--who", "Tessy", "--reason", "Reviewed"]
    # Run from a script or an agent (no person at a terminal): refused, whatever it "types".
    assert reset_circuit_breaker.main(ok, state, log, typist("RESET"), interactive=False) == 1
    assert "person at a terminal" in capsys.readouterr().out
    # A person who doesn't type RESET exactly: cancelled.
    for answer in ("", "yes", "reset", "RESET!"):
        assert reset_circuit_breaker.main(ok, state, log, typist(answer), interactive=True) == 1
    assert not log.exists() and not CircuitBreaker.load(state).allows_new_trades
    # Name, reason and RESET typed: done.
    assert reset_circuit_breaker.main(ok, state, log, typist("RESET"), interactive=True) == 0
    assert CircuitBreaker.load(state).allows_new_trades
    assert list(csv.DictReader(log.open()))[0]["who"] == "Tessy"


def test_library_reset_needs_the_typed_word(tmp_path):
    b = CircuitBreaker(mode=PAPER)
    fall_then_flat(b)
    for word in ("", "yes", "reset"):
        with pytest.raises(ValueError, match="RESET"):
            b.reset("Tessy", "reviewed", log_path=tmp_path / "r.csv", confirmation=word)
    assert not b.allows_new_trades


def hard_floor_state(tmp_path):
    """A paper breaker saved while halted by the 20% hard floor (after one earlier, logged 10% reset)."""
    state, log = tmp_path / "state.json", tmp_path / "resets.csv"
    b = CircuitBreaker(mode=PAPER)
    for i, v in enumerate([1.0, 0.89, 0.89]):
        b.update(i, DAYS[i], v)
    b.reset("Tessy", "first review", log_path=log, confirmation="RESET")
    for i, v in enumerate([0.78, 0.78], start=3):
        b.update(i, DAYS[i], v)
    assert b.halted
    b.save(state)
    return state, log


def test_hard_floor_needs_the_extra_confirmation_step(tmp_path, capsys):
    state, log = hard_floor_state(tmp_path)
    ok = ["--who", "Tessy", "--reason", "Full strategy review after the 20% fall"]
    # RESET alone isn't enough; nor a wrong extra word; nor a different name on the second ask.
    for answers in (("RESET", "", ""), ("RESET", "HARD FLOOR", "Someone else"), ("RESET", "hard floor", "Tessy")):
        assert reset_circuit_breaker.main(ok, state, log, typist(*answers), interactive=True) == 1
        assert CircuitBreaker.load(state).halted
    assert "HARD FLOOR" in capsys.readouterr().out
    assert reset_circuit_breaker.main(ok, state, log, typist("RESET", "HARD FLOOR", "Tessy"), interactive=True) == 0
    after = CircuitBreaker.load(state)
    assert after.allows_new_trades and not after.halted
    assert [r["kind"] for r in csv.DictReader(log.open())] == ["10% breaker", "hard floor"]


# ---- The reset log is append-only ------------------------------------------------------------------

def three_resets(tmp_path):
    """Three trips and three resets on one paper breaker. Returns the breaker, the log, and the log's
    exact bytes after each reset."""
    log = tmp_path / "resets.csv"
    b = CircuitBreaker(mode=PAPER)
    snapshots, day, v = [], 0, 1.0
    for n in range(3):
        for x in (v, v * 0.88):            # fall 12% from the latest peak: trips the 10% breaker
            b.update(day, DAYS[day], x)
            day += 1
        v *= 0.88
        b.reset("Tessy", f"review {n + 1}, with a comma, and \"quotes\"", log_path=log, confirmation="RESET",
                hard_floor_confirmation="HARD FLOOR")
        snapshots.append(log.read_bytes())
    return b, log, snapshots, day, v


def trip_again(b, day, v):
    b.update(day, DAYS[day], v * 0.85)
    assert not b.allows_new_trades


def test_reset_log_is_only_ever_added_to(tmp_path):
    b, log, snaps, _, _ = three_resets(tmp_path)
    # Each version of the file starts with the previous version, byte for byte: nothing was changed or
    # removed, only added at the end.
    for before, after in zip(snaps, snaps[1:]):
        assert after.startswith(before) and len(after) > len(before)
    ok, msg, rows = verify_reset_log(log)
    assert ok and rows == 3, msg
    assert b.reset_log_rows == 3


def test_an_edited_reset_log_blocks_the_next_reset(tmp_path):
    b, log, snaps, day, v = three_resets(tmp_path)
    log.write_bytes(snaps[-1].replace(b"review 1", b"review X"))       # someone rewrites history
    assert not verify_reset_log(log)[0]
    trip_again(b, day, v)
    with pytest.raises(ResetLogTampered, match="edited"):
        b.reset("Tessy", "reviewed", log_path=log, confirmation="RESET", hard_floor_confirmation="HARD FLOOR")
    assert log.read_bytes() == snaps[-1].replace(b"review 1", b"review X")   # and nothing was appended


@pytest.mark.parametrize("cut", ["last_row", "first_row", "everything_but_header", "empty_file"])
def test_a_shortened_reset_log_blocks_the_next_reset(tmp_path, cut):
    b, log, snaps, day, v = three_resets(tmp_path)
    lines = snaps[-1].splitlines(keepends=True)
    shortened = {"last_row": b"".join(lines[:-1]), "first_row": lines[0] + b"".join(lines[2:]),
                 "everything_but_header": lines[0], "empty_file": b""}[cut]
    log.write_bytes(shortened)
    trip_again(b, day, v)
    with pytest.raises(ResetLogTampered):
        b.reset("Tessy", "reviewed", log_path=log, confirmation="RESET", hard_floor_confirmation="HARD FLOOR")
    assert not b.allows_new_trades


def test_a_deleted_reset_log_blocks_the_next_reset(tmp_path):
    b, log, snaps, day, v = three_resets(tmp_path)
    log.unlink()
    trip_again(b, day, v)
    with pytest.raises(ResetLogTampered, match="shortened"):
        b.reset("Tessy", "reviewed", log_path=log, confirmation="RESET", hard_floor_confirmation="HARD FLOOR")


def test_log_tampering_survives_save_and_load(tmp_path):
    """The breaker's saved state remembers the log's size and fingerprint, so the check works across runs."""
    b, log, snaps, day, v = three_resets(tmp_path)
    trip_again(b, day, v)
    b.save(tmp_path / "state.json")
    log.write_bytes(b"".join(snaps[-1].splitlines(keepends=True)[:-1]))
    again = CircuitBreaker.load(tmp_path / "state.json")
    with pytest.raises(ResetLogTampered):
        again.reset("Tessy", "reviewed", log_path=log, confirmation="RESET", hard_floor_confirmation="HARD FLOOR")
    log.write_bytes(snaps[-1])                       # restored (e.g. from git): resets work again
    again.reset("Tessy", "reviewed", log_path=log, confirmation="RESET", hard_floor_confirmation="HARD FLOOR")
    assert verify_reset_log(log)[2] == 4
