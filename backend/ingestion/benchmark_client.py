"""Benchmark price history via yfinance.

Only benchmarks with a yf_ticker are fetched; others (e.g. the debt proxy index)
are skipped and reported as warnings so the ingest run record is honest.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BenchmarkRow:
    date: date
    close: float


def _extract_close(df: pd.DataFrame, ticker: str) -> pd.Series | None:
    """Pick the 'Adj Close' (preferred) or 'Close' column from a yfinance DF.

    yfinance returns a MultiIndex `(field, ticker)` even for a single ticker; a
    bare `df["Close"]` on that still returns a *DataFrame*, so we have to be
    explicit about selecting the ticker's column.
    """
    if df is None or df.empty:
        return None

    for field in ("Adj Close", "Close"):
        if isinstance(df.columns, pd.MultiIndex):
            if (field, ticker) in df.columns:
                return df[(field, ticker)]
            # fallback: first column at that top level
            top = [c for c in df.columns if c[0] == field]
            if top:
                return df[top[0]]
        else:
            if field in df.columns:
                return df[field]
    return None


def fetch_benchmark_history(ticker: str, start: str = "2013-01-01") -> list[BenchmarkRow]:
    """Daily close history for ticker. Lazy-import so yfinance is only required at call time."""
    import yfinance as yf  # noqa: WPS433

    end = datetime.now().strftime("%Y-%m-%d")
    logger.info("yfinance: downloading %s %s..%s", ticker, start, end)
    df = yf.download(
        ticker,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
        actions=False,
    )
    series = _extract_close(df, ticker)
    if series is None or series.empty:
        logger.warning("yfinance: no usable close for %s", ticker)
        return []

    out: list[BenchmarkRow] = []
    for idx, val in series.dropna().items():
        try:
            d = idx.date() if hasattr(idx, "date") else idx
            v = float(val)
        except (TypeError, ValueError):
            continue
        if v <= 0:
            continue
        out.append(BenchmarkRow(date=d, close=v))
    out.sort(key=lambda r: r.date)
    return out
