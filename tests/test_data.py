import pandas as pd
import pytest

from lab import data


def test_reads_yahoo_style_csv_and_prefers_adjusted_close(tmp_path):
    p = tmp_path / "SPY.csv"
    p.write_text("Date,Open,High,Low,Close,Adj Close,Volume\n"
                 "2020-01-02,1,1,1,100,90,5\n2020-01-03,1,1,1,101,91,5\n")
    df = data.read_price_csv(p)
    assert df["Close"].tolist() == [90, 91]
    assert isinstance(df.index, pd.DatetimeIndex)


def test_reads_stooq_style_csv_and_sorts_dates(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("Date,Open,High,Low,Close,Volume\n2020-01-03,1,1,1,11,5\n2020-01-02,1,1,1,10,5\n")
    assert data.read_price_csv(p)["Close"].tolist() == [10, 11]


def test_user_csv_wins_over_download(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CSV_DIR", tmp_path)
    (tmp_path / "CAD_X.csv").write_text("Date,Close\n2010-01-04,1.05\n2010-01-05,1.04\n")
    df, source = data.load_prices("CAD=X", start="2005-01-01")
    assert len(df) == 2 and source == "data/csv/CAD_X.csv"


def test_clear_error_when_every_source_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CSV_DIR", tmp_path / "csv")

    def blocked(*_):
        raise ConnectionError("blocked")

    monkeypatch.setattr(data, "_download_yahoo", blocked)
    monkeypatch.setattr(data, "_download_stooq", blocked)
    with pytest.raises(data.DataUnavailable, match="data/csv/SPY.csv"):
        data.load_prices("SPY")


def test_demo_data_covers_all_assets():
    from lab import config
    prices, sources = data.load_all(config.TRADED_ASSETS + config.COMPARISON_ASSETS, demo=True)
    for t, df in prices.items():
        assert df.index[0].year == 2005 and len(df) > 5000
        assert "SYNTHETIC" in sources[t]


def test_reads_investing_com_style_csv(tmp_path):
    p = tmp_path / "XIU_TO.csv"
    p.write_text('"Date","Price","Open","High","Low","Vol.","Change %"\n'
                 '"01/03/2020","1,027.50","1","1","1","5K","0.1%"\n'
                 '"01/02/2020","1,020.00","1","1","1","5K","0.1%"\n')
    df = data.read_price_csv(p)
    assert df["Close"].tolist() == [1020.0, 1027.5]
    assert df.index[0] == pd.Timestamp("2020-01-02")


def fake_download(close_values):
    def fetch(ticker, start):
        idx = pd.bdate_range("2019-01-01", periods=len(close_values))
        return pd.DataFrame({"Close": close_values}, index=idx)
    return fetch


def test_file_names_match_the_readme():
    assert data._file_name("XIU.TO") == "XIU_TO.csv"
    assert data._file_name("CAD=X") == "CAD_X.csv"
    assert data._file_name("^IRX") == "IRX.csv"


def test_old_xiu_file_name_still_works(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CSV_DIR", tmp_path)
    (tmp_path / "XIU.TO.csv").write_text("Date,Close\n2010-01-04,20\n")
    assert data.csv_path("XIU.TO").name == "XIU.TO.csv"


def test_missing_file_is_downloaded_and_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CSV_DIR", tmp_path)
    monkeypatch.setattr(data, "_download_yahoo", fake_download([1.0] * 300))
    df, source = data.load_prices("SPY", start="2005-01-01")
    assert (tmp_path / "SPY.csv").exists() and "downloaded" in source
    assert data.read_price_csv(tmp_path / "SPY.csv")["Close"].tolist() == [1.0] * 300


def test_refresh_overwrites_the_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CSV_DIR", tmp_path)
    (tmp_path / "SPY.csv").write_text("Date,Close\n2010-01-04,5\n")
    monkeypatch.setattr(data, "_download_yahoo", fake_download([7.0] * 300))
    # Without refresh, the committed file wins.
    assert data.load_prices("SPY")[0]["Close"].tolist() == [5.0]
    # With refresh, it is re-downloaded and overwritten.
    df, source = data.load_prices("SPY", refresh=True)
    assert len(df) == 300 and "downloaded" in source
    assert data.read_price_csv(tmp_path / "SPY.csv")["Close"].iloc[0] == 7.0


def test_failed_refresh_keeps_the_old_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(data, "CSV_DIR", tmp_path)
    (tmp_path / "SPY.csv").write_text("Date,Close\n2010-01-04,5\n")

    def blocked(*_):
        raise ConnectionError("blocked")

    monkeypatch.setattr(data, "_download_yahoo", blocked)
    monkeypatch.setattr(data, "_download_stooq", blocked)
    df, source = data.load_prices("SPY", refresh=True)
    assert df["Close"].tolist() == [5.0] and "FAILED" in source
    assert "WARNING" in capsys.readouterr().out


# ---- Session 5: IEF, refreshing named tickers, never saving an unfinished day ----

def test_todays_row_is_dropped_until_the_close_is_final():
    idx = pd.to_datetime(["2026-09-24", "2026-09-25", "2026-09-28"])
    df = pd.DataFrame({"Close": [1.0, 2.0, 3.0]}, index=idx)
    during = pd.Timestamp("2026-09-28 12:31", tz="America/New_York")   # market still open
    after = pd.Timestamp("2026-09-28 18:00", tz="America/New_York")
    assert data.drop_unfinished_day(df, during).index[-1] == pd.Timestamp("2026-09-25")
    assert data.drop_unfinished_day(df, after).index[-1] == pd.Timestamp("2026-09-28")


def test_refresh_can_name_just_some_tickers(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CSV_DIR", tmp_path)
    for name in ("SPY", "IEF"):
        (tmp_path / f"{name}.csv").write_text("Date,Close\n2010-01-04,1\n2010-01-05,2\n")
    downloaded = []

    def fake(ticker, start):
        downloaded.append(ticker)
        idx = pd.bdate_range("2010-01-01", periods=300)
        return pd.DataFrame({"Close": range(1, 301)}, index=idx), "fake"

    monkeypatch.setattr(data, "_download", fake)
    data.load_all(["SPY", "IEF"], refresh=["IEF"])
    assert downloaded == ["IEF"]
    data.load_all(["SPY", "IEF"], refresh=True)
    assert downloaded == ["IEF", "SPY", "IEF"]


def test_ief_is_in_the_universe_but_old_portfolio_keeps_its_three_assets():
    from lab import config
    assert config.PORTFOLIO_ASSETS == ["SPY", "XIU.TO", "GLD", "IEF"]
    assert config.PORTFOLIO_STRATEGIES["ma_trend"] == ["SPY", "XIU.TO", "GLD"]   # tested idea: never changed
    assert "IEF" in config.COMPARISON_ASSETS and "IEF" in config.ASSET_NAMES


def test_demo_bonds_are_calm_and_move_against_stocks():
    from lab.synthetic import make_demo_prices
    p = make_demo_prices()
    r = pd.DataFrame({t: p[t]["Close"].pct_change() for t in ("SPY", "IEF")}).dropna()
    assert r["IEF"].std() < 0.5 * r["SPY"].std()
    assert r.corr().loc["SPY", "IEF"] < 0
