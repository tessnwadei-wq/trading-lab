"""
Getting daily price data.

data/csv/ is the lab's price store, and it is committed to git so everyone uses the same numbers.
  * Normal run:        read data/csv/<ticker>.csv. If a file is missing, download it and save it there.
  * `--refresh` run:   re-download EVERY ticker and overwrite its file in data/csv/ (to get the
                       latest days). If a download fails, the old file is kept and you get a warning.
Downloads try Yahoo Finance (the `yfinance` package) first, then Stooq (a free backup website).
If you pass demo=True we skip all of that and use made-up practice data (see lab/synthetic.py).

Every function returns a pandas DataFrame indexed by date with at least a "Close" column.
"Close" is the *adjusted* close: it includes dividends, so buy-and-hold is measured fairly.
(For ^IRX, the T-bill yield, "Close" is the interest rate in % a year, e.g. 4.07.)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from lab import config

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "data" / "csv"
TMP_DIR = ROOT / "data" / "cache"  # scratch space for downloads; not committed

# Stooq uses different ticker names from Yahoo.
STOOQ_SYMBOLS = {"SPY": "spy.us", "GLD": "gld.us", "IEF": "ief.us", "CAD=X": "usdcad", "XIU.TO": "xiu.ca"}

# The US and Toronto markets close at 16:00 New York time. Before then, a download's row for today holds the
# LATEST price, not the close, and the lab only ever uses closes. We wait until 17:00 to be safe.
MARKET_CLOSE_TZ = "America/New_York"
CLOSE_FINAL_AFTER_HOUR = 17


class DataUnavailable(RuntimeError):
    """Raised when no source could provide prices for a ticker."""


def _file_name(ticker: str) -> str:
    """CSV file name for a ticker: "CAD=X" -> "CAD_X.csv", "XIU.TO" -> "XIU_TO.csv", "^IRX" -> "IRX.csv"."""
    return ticker.replace("=", "_").replace(".", "_").replace("^", "") + ".csv"


def csv_path(ticker: str) -> Path:
    """Where this ticker's prices live. Also accepts the older name "XIU.TO.csv" if that's what exists."""
    path = CSV_DIR / _file_name(ticker)
    legacy = CSV_DIR / (ticker.replace("=", "_").replace("^", "") + ".csv")
    return legacy if not path.exists() and legacy.exists() else path


def read_price_csv(path: Path) -> pd.DataFrame:
    """
    Read a price CSV in any of the common layouts (Yahoo, Stooq, or just Date + Close).

    We prefer the "Adj Close" column when it exists, because it accounts for dividends.
    """
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    lower = {c.lower(): c for c in df.columns}

    date_col = lower.get("date") or lower.get("datetime") or df.columns[0]
    close_col = (lower.get("adj close") or lower.get("adj_close") or lower.get("close")
                 or lower.get("price"))  # Investing.com calls it "Price"
    if close_col is None:
        raise ValueError(f"{path.name}: could not find a 'Close' or 'Adj Close' column")

    # .to_numpy() so pandas pairs values with dates by position, not by row label.
    values = pd.to_numeric(df[close_col].astype(str).str.replace(",", ""), errors="coerce")
    # utc=True copes with dates like "2020-01-02 00:00:00-05:00"; then keep just the day.
    dates = pd.to_datetime(df[date_col], errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    out = pd.DataFrame({"Close": values.to_numpy()}, index=dates.to_numpy())
    out.index.name = "Date"
    out = out[out.index.notna()].dropna().sort_index()
    out = out[~out.index.duplicated(keep="last")]
    if out.empty:
        raise ValueError(f"{path.name}: no usable rows")
    return out


def _download_yahoo(ticker: str, start: str) -> pd.DataFrame:
    import yfinance as yf  # imported here so the rest of the lab works without it

    raw = yf.download(ticker, start=start, progress=False, auto_adjust=True)
    if raw is None or raw.empty:
        raise DataUnavailable(f"Yahoo returned no data for {ticker}")
    close = raw["Close"]
    if isinstance(close, pd.DataFrame):  # newer yfinance versions return one column per ticker
        close = close.iloc[:, 0]
    out = pd.DataFrame({"Close": close.astype(float)}).dropna()
    out.index = pd.to_datetime(out.index).tz_localize(None)
    out.index.name = "Date"
    return out


def _download_stooq(ticker: str, start: str) -> pd.DataFrame:
    import requests

    symbol = STOOQ_SYMBOLS.get(ticker, ticker.lower())
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    if "Date" not in resp.text[:100]:
        raise DataUnavailable(f"Stooq returned no data for {ticker}")
    tmp = TMP_DIR / f"_stooq_{_file_name(ticker)}"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(resp.text)
    df = read_price_csv(tmp)
    tmp.unlink(missing_ok=True)
    return df.loc[start:]


def save_price_csv(df: pd.DataFrame, path: Path) -> None:
    """Write Date + Close (the only columns the lab uses) so the committed files stay small."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df[["Close"]].to_csv(path, index_label="Date", float_format="%.8g")


def drop_unfinished_day(df: pd.DataFrame, now: pd.Timestamp | None = None) -> pd.DataFrame:
    """
    Remove any row for a day whose close isn't final yet. During the trading day, Yahoo already shows a row for
    "today" with the latest price in it; saving that as a close would be wrong (and would change later). So a row
    dated today (New York time) is only kept after 17:00 New York time, and rows dated in the future never are.
    `now` is only passed in by tests.
    """
    now = pd.Timestamp.now(tz=MARKET_CLOSE_TZ) if now is None else pd.Timestamp(now).tz_convert(MARKET_CLOSE_TZ)
    last_final = now.normalize().tz_localize(None)
    if now.hour < CLOSE_FINAL_AFTER_HOUR:
        last_final -= pd.Timedelta(days=1)
    return df.loc[:last_final]


def _download(ticker: str, start: str) -> tuple[pd.DataFrame, str]:
    """Try each download source in turn. Returns (prices, source name) or raises DataUnavailable."""
    errors = []
    for name, fetch in (("Yahoo Finance", _download_yahoo), ("Stooq", _download_stooq)):
        try:
            df = drop_unfinished_day(fetch(ticker, start))
            if len(df) < 250:
                raise DataUnavailable(f"only {len(df)} rows")
            return df, name
        except Exception as exc:  # any failure: note it and try the next source
            errors.append(f"{name}: {type(exc).__name__}: {str(exc)[:120]}")
    raise DataUnavailable("\n  ".join(errors))


def load_prices(ticker: str, start: str = config.START_DATE, demo: bool = False,
                refresh: bool = False) -> tuple[pd.DataFrame, str]:
    """
    Return (prices, source_description) for one ticker.

    refresh=True downloads again and OVERWRITES data/csv/<ticker>.csv (e.g. to get the latest days).
    Today's row is never saved until the day's close is final (see drop_unfinished_day).
    """
    if demo:
        from lab.synthetic import make_demo_prices
        return make_demo_prices()[ticker].loc[start:], "SYNTHETIC demo data (not real prices)"

    path = csv_path(ticker)
    if path.exists() and not refresh:
        return read_price_csv(path).loc[start:], f"data/csv/{path.name}"

    try:
        df, source = _download(ticker, start)
    except DataUnavailable as exc:
        if path.exists():  # refresh failed: keep using the file we already have
            print(f"  WARNING: could not refresh {ticker}, keeping the existing data/csv/{path.name}.\n  {exc}")
            return read_price_csv(path).loc[start:], f"data/csv/{path.name} (refresh FAILED, older data)"
        raise DataUnavailable(
            f"Could not get prices for {ticker}.\n  {exc}"
            f"\nFix: download a CSV and save it as data/csv/{_file_name(ticker)} "
            "(see README.md, 'If the download fails'), or run with --demo for practice data."
        ) from None

    new_path = CSV_DIR / _file_name(ticker)
    save_price_csv(df, new_path)
    return df, f"data/csv/{new_path.name} (downloaded from {source} today)"


def load_all(tickers: list[str], demo: bool = False, refresh=False) -> tuple[dict, dict]:
    """
    Load several tickers. Returns ({ticker: prices}, {ticker: source}).
    refresh: False (use the files), True (re-download every ticker) or a list of tickers to re-download.
    """
    prices, sources = {}, {}
    for t in tickers:
        again = refresh is True or (isinstance(refresh, (list, tuple, set)) and t in refresh)
        prices[t], sources[t] = load_prices(t, demo=demo, refresh=again)
    return prices, sources
