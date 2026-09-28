"""
The paper-trading account (lab/paper.py, paper_trade.py): pretend money, every risk rule, manual-reset breaker,
and refusing to run when its files are missing, edited or don't match git.

Every test works in a throwaway folder with its own git repository and made-up prices. None touches the real
paper account, and the circuit-breaker reset below happens ONLY inside a test, playing the part of Tessy typing
(agents never run the real reset; CLAUDE.md).
"""

import json
import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest

import reset_circuit_breaker
from lab import config
from lab.paper import (PAPER_ASSETS, PaperPaths, PaperRefused, commit_paper_files, integrity_problems, run_account,
                       start_account)

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is needed for the paper-account checks")

N_DAYS = 130
START_I = 40        # the account opens at this close
CRASH_I = 50        # every asset falls 16% at this close


def make_prices(crash=False):
    idx = pd.bdate_range("2024-01-01", periods=N_DAYS)
    out = {}
    for k, a in enumerate(PAPER_ASSETS):
        moves = np.where(np.arange(N_DAYS) % 2 == 0, 1.003, 1 / 1.003) * 1.0004
        if crash:
            moves[CRASH_I] *= 0.84
        out[a] = pd.DataFrame({"Close": (50 + 10 * k) * np.cumprod(moves)}, index=idx)
    return out


def upto(prices, i):
    """Only the closes up to day i: what the price files would hold on that day."""
    return {a: p.iloc[: i + 1] for a, p in prices.items()}


@pytest.fixture
def repo(tmp_path):
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    git("init", "-q")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    git("commit", "-q", "--allow-empty", "-m", "empty")
    return PaperPaths(tmp_path)


def open_account(paths, prices, i=START_I):
    state = start_account(paths, upto(prices, i), None, echo=lambda *_: None)
    assert commit_paper_files(paths, "open")[0]
    return state


def run(paths, prices, i):
    out = run_account(paths, upto(prices, i), None, echo=lambda *_: None)
    assert commit_paper_files(paths, f"run {i}")[0]
    return out


def fills(paths):
    return pd.read_csv(paths.logs["fills"]) if paths.logs["fills"].exists() else pd.DataFrame()


# ---- opening, timing, the allowed strategy ------------------------------------------------------------
def test_open_places_orders_that_fill_at_the_next_close(repo):
    prices = make_prices()
    state = open_account(repo, prices)
    assert state["cash"] == 10_000 and not state["positions"]
    assert sorted(o["kind"] for o in state["pending"].values()) == ["entry"] * 4   # decided at the last close
    assert integrity_problems(repo) == []
    # Running again with no new close changes nothing: the orders wait for the next close.
    assert run(repo, prices, START_I)["days"] == 0 and fills(repo).empty
    out = run(repo, prices, START_I + 1)
    f = fills(repo)
    assert len(f) == 4 and set(f["filled_on"]) == {str(prices["SPY"].index[START_I + 1].date())}
    for a in PAPER_ASSETS:   # filled at the NEXT close's price, never the close it was decided on
        assert float(f.loc[f.asset == a, "price"].iloc[0]) == pytest.approx(prices[a]["Close"].iloc[START_I + 1],
                                                                            rel=1e-6)
    weights = [p["units"] * out["state"]["last_price"][a] / out["equity"] for a, p in out["state"]["positions"].items()]
    assert max(weights) <= config.MAX_POSITION_WEIGHT + 1e-9 and min(weights) > 0.19   # 20% each, never above
    balances = pd.read_csv(repo.logs["balances"])
    assert list(balances["date"])[-1] == str(prices["SPY"].index[START_I + 1].date())


def test_only_buy_and_hold_is_allowed(repo):
    with pytest.raises(PaperRefused, match="No strategy has passed"):
        start_account(repo, make_prices(), None, strategy="ts_momentum", echo=lambda *_: None)
    assert not repo.state.exists()


def test_cli_refuses_other_strategies_before_touching_anything(tmp_path, capsys):
    import paper_trade
    assert paper_trade.main(["--start", "--strategy", "vol_target"], paths=PaperPaths(tmp_path)) == 1
    assert "not allowed in paper trading" in capsys.readouterr().out
    assert not any(tmp_path.iterdir())


def test_a_second_account_is_never_opened_over_the_first(repo):
    open_account(repo, make_prices())
    with pytest.raises(PaperRefused, match="already exists"):
        start_account(repo, make_prices(), None, echo=lambda *_: None)


def test_a_file_that_is_a_day_behind_is_not_treated_as_a_holiday(repo):
    prices = make_prices()
    open_account(repo, prices)
    lagging = upto(prices, START_I + 5)
    lagging["IEF"] = lagging["IEF"].iloc[:-1]            # IEF's file hasn't got the newest day yet
    out = run_account(repo, lagging, None, echo=lambda *_: None)
    assert out["state"]["last_processed"] == str(prices["SPY"].index[START_I + 4].date())


# ---- refusing to run ---------------------------------------------------------------------------------
@pytest.mark.parametrize("damage", ["delete state", "delete breaker", "delete reset log", "edit state",
                                    "edit state and commit", "edit a log and commit", "edit reset log and commit",
                                    "uncommitted change"])
def test_refuses_when_files_are_missing_edited_or_not_matching_git(repo, damage):
    prices = make_prices()
    open_account(repo, prices)
    run(repo, prices, START_I + 3)
    if damage == "delete state":
        repo.state.unlink()
    elif damage == "delete breaker":
        repo.breaker.unlink()
    elif damage == "delete reset log":
        repo.reset_log.unlink()
    elif damage.startswith("edit state"):
        s = json.loads(repo.state.read_text())
        s["cash"] += 1_000_000                            # "free money"
        repo.state.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
    elif damage == "edit a log and commit":
        text = repo.logs["fills"].read_text().replace("buy", "sell", 1)
        repo.logs["fills"].write_text(text)
    elif damage == "edit reset log and commit":
        repo.reset_log.write_text(repo.reset_log.read_text() + "2026-01-01,Someone,x,2026-01-01,-0.1,10% breaker,0\n")
    elif damage == "uncommitted change":
        repo.logs["events"].write_text(repo.logs["events"].read_text() + "\n")
    if damage.endswith("and commit"):
        subprocess.run(["git", "-C", str(repo.root), "commit", "-qam", "sneaky"], check=True)
    with pytest.raises(PaperRefused, match="refuses to run"):
        run_account(repo, upto(prices, START_I + 6), None, echo=lambda *_: None)


def test_refuses_outside_git(tmp_path):
    paths = PaperPaths(tmp_path)
    start_account(paths, make_prices(), None, echo=lambda *_: None, check_git=False)
    problems = integrity_problems(paths)
    assert any("isn't a git repository" in p for p in problems)


# ---- the risk rules in paper mode ------------------------------------------------------------------------
def test_monthly_resize_and_twenty_percent_rule(repo):
    prices = make_prices()
    open_account(repo, prices)
    out = run(repo, prices, N_DAYS - 1)
    orders = pd.read_csv(repo.logs["orders"])
    assert (orders["kind"] == "resize").sum() >= 4 * 3            # every month-end, every asset
    b = pd.read_csv(repo.logs["balances"])
    total = b["total"].astype(float)
    for a in PAPER_ASSETS:                                          # never above 22% at any close
        assert (b[f"{a}_value"].astype(float) / total).max() <= config.POSITION_ALERT_WEIGHT
    assert out["breaker"].allows_new_trades


# ---- end to end: trip -> blocked -> manual reset (inside this test only) -> trading resumes ---------------
def test_breaker_trips_blocks_trading_and_resumes_only_after_a_manual_reset(repo, capsys):
    prices = make_prices(crash=True)
    open_account(repo, prices)

    # 1. The crash: the account falls more than 10% and the breaker trips. Stops sell the positions.
    out = run(repo, prices, CRASH_I + 25)             # through the next month-end
    assert not out["breaker"].allows_new_trades and out["breaker"].tripped and not out["breaker"].halted
    events = pd.read_csv(repo.logs["events"])
    assert events["kind"].str.contains("circuit breaker").any()
    assert events["kind"].eq("buy blocked").any()     # 2. it wanted to buy back at the month-end: blocked
    assert not out["state"]["positions"]

    # Still blocked on later runs: nothing restarts by itself.
    out = run(repo, prices, CRASH_I + 40)
    assert not out["breaker"].allows_new_trades and not out["state"]["positions"]
    n_fills = len(fills(repo))

    # 3. Tessy's manual reset, played by this test (typed confirmation). Agents never run the real one.
    code = reset_circuit_breaker.main(["--who", "Tessy", "--reason", "Test: reviewed the made-up crash"],
                                      state_path=repo.breaker, log_path=repo.reset_log,
                                      ask=lambda _: "RESET", interactive=True)
    assert code == 0
    # Until the reset is committed, the account refuses to run (its files no longer match git).
    with pytest.raises(PaperRefused, match="if you have just reset the circuit breaker"):
        run_account(repo, upto(prices, CRASH_I + 45), None, echo=lambda *_: None)
    subprocess.run(["git", "-C", str(repo.root), "commit", "-qam", "Tessy reset the breaker"], check=True)

    # 4. Trading resumes: buys are decided at the next close and filled at the one after.
    out = run(repo, prices, CRASH_I + 45)
    assert out["breaker"].allows_new_trades
    new = fills(repo).iloc[n_fills:]
    entries = new[new["kind"] == "entry"]
    assert len(entries) == 4 and set(entries["side"]) == {"buy"}
    assert entries["filled_on"].min() > str(prices["SPY"].index[CRASH_I + 40].date())   # only after the reset
    assert len(out["state"]["positions"]) == 4
    log = pd.read_csv(repo.reset_log)
    assert list(log["who"]) == ["Tessy"] and integrity_problems(repo) == []
