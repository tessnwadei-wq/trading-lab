import numpy as np
import pandas as pd
import pytest

from lab.metrics import cagr, max_drawdown_info, sharpe, total_return


def series(values, start="2020-01-01", freq="B"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq=freq), dtype=float)


def test_max_drawdown_and_recovery():
    eq = series([1.0, 1.2, 0.9, 1.0, 1.2, 1.3])
    info = max_drawdown_info(eq)
    assert info["max_dd"] == pytest.approx(0.9 / 1.2 - 1)  # -25%
    assert info["recovery_days"] == 2  # trough (day 2) -> back to 1.2 on day 4


def test_drawdown_not_recovered():
    info = max_drawdown_info(series([1.0, 0.5, 0.6]))
    assert info["max_dd"] == pytest.approx(-0.5)
    assert info["recovered"] is None and info["recovery_days"] is None


def test_cagr_doubling_over_two_years():
    eq = pd.Series([1.0, 2.0], index=pd.to_datetime(["2020-01-01", "2022-01-01"]))
    assert cagr(eq) == pytest.approx(np.sqrt(2) - 1, rel=1e-3)
    assert total_return(eq) == pytest.approx(1.0)


def test_sharpe_is_zero_when_nothing_moves():
    assert sharpe(series([0.0] * 10)) == 0.0


def test_sharpe_positive_for_steady_gains():
    rng = np.random.default_rng(0)
    r = series(0.001 + 0.005 * rng.standard_normal(500))
    assert sharpe(r) > 2
