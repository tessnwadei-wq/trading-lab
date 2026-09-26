"""
Getting daily price data.

Where prices come from, in the order we try them:
  1. A CSV file you dropped into data/csv/        (you are always in control)
  2. A cached copy in data/cache/                 (so we don't re-download every run)
  3. Yahoo Finance via the `yfinance` package     (free, the usual choice)
  4. Stooq (free backup website)
If you pass demo=True we skip all of that and use made-up practice data (see lab/synthetic.py).

Every function returns a pandas DataFrame indexed by date with at least a "Close" column.
"Close" is the *adjusted* close: it includes dividends, so buy-and-hold is measured fairly.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from lab import config

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "data" / "csv"
CACHE_DIR = ROOT / "data" / "cache"

# Stooq uses different ticker names from Yahoo.
STOOQ_SYMBOLS = {"SPY": "spy.us", "GLD": "gld.us", "CAD=X": "usdcad", "XIU.TO": "xiu.ca"}


class DataUnavailable(RuntimeError):
    """Raised when no source could provide prices for a ticker."""


def _file_name(ticker: str) -> str:
    # "CAD=X" is not a friendly file name on every system, so swap odd characters.
    return ticker.replace("=", "_").replace("^", "")


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
    tmp = CACHE_DIR / f"_stooq_{_file_name(ticker)}.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(resp.text)
    df = read_price_csv(tmp)
    tmp.unlink(missing_ok=True)
    return df.loc[start:]


def load_prices(ticker: str, start: str = config.START_DATE, demo: bool = False,
                refresh: bool = False) -> tuple[pd.DataFrame, str]:
    """
    Return (prices, source_description) for one ticker.

    refresh=True ignores the cache and downloads again (e.g. to get the latest days).
    """
    if demo:
        from lab.synthetic import make_demo_prices
        return make_demo_prices()[ticker].loc[start:], "SYNTHETIC demo data (not real prices)"

    # 1. Your own CSV always wins.
    csv_path = CSV_DIR / f"{_file_name(ticker)}.csv"
    if csv_path.exists():
        return read_price_csv(csv_path).loc[start:], f"your CSV file data/csv/{csv_path.name}"

    # 2. Cache.
    cache_path = CACHE_DIR / f"{_file_name(ticker)}.csv"
    if cache_path.exists() and not refresh:
        return read_price_csv(cache_path).loc[start:], f"cached download data/cache/{cache_path.name}"

    # 3 and 4. Download.
    errors = []
    for name, fetch in (("Yahoo Finance", _download_yahoo), ("Stooq", _download_stooq)):
        try:
            df = fetch(ticker, start)
            if len(df) < 250:
                raise DataUnavailable(f"only {len(df)} rows")
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            df.to_csv(cache_path)
            return df, f"downloaded from {name}"
        except Exception as exc:  # any failure: note it and try the next source
            errors.append(f"{name}: {type(exc).__name__}: {str(exc)[:120]}")

    raise DataUnavailable(
        f"Could not get prices for {ticker}.\n  " + "\n  ".join(errors) +
        f"\nFix: download a CSV and save it as data/csv/{_file_name(ticker)}.csv "
        "(see README.md, 'If the download fails'), or run with --demo for practice data."
    )


def load_all(tickers: list[str], demo: bool = False, refresh: bool = False) -> tuple[dict, dict]:
    """Load several tickers. Returns ({ticker: prices}, {ticker: source})."""
    prices, sources = {}, {}
    for t in tickers:
        prices[t], sources[t] = load_prices(t, demo=demo, refresh=refresh)
    return prices, sources
