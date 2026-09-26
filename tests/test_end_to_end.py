"""Whole-lab checks: the committed data is usable, and run_lab.py works end to end offline."""

import pytest

from lab import config, data


@pytest.mark.parametrize("ticker", config.TRADED_ASSETS + config.COMPARISON_ASSETS + [config.CASH_TICKER])
def test_committed_price_files_are_readable(ticker):
    path = data.csv_path(ticker)
    if not path.exists():
        pytest.skip(f"{path.name} not committed yet")
    df = data.read_price_csv(path)
    assert df.index[0].year <= 2005 and len(df) > 5000
    assert df["Close"].notna().all()


def test_run_lab_demo_end_to_end(tmp_path, monkeypatch):
    import run_lab
    from lab import report, trials

    monkeypatch.setattr(report, "REPORTS_DIR", tmp_path)            # don't overwrite the real reports
    monkeypatch.setattr(trials, "TRIALS_CSV", tmp_path / "trials.csv")
    assert run_lab.main(["--demo", "--strategy", "portfolio_ma_trend"]) == 0
    text = (tmp_path / "portfolio_ma_trend" / "report.md").read_text(encoding="utf-8")
    assert "DEMO DATA" in text and "## Risk manager" in text and "Same-risk mix" in text
    assert not (tmp_path / "trials.csv").exists()  # demo runs are never counted as trials
