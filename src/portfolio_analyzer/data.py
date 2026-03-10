"""Data fetching from Yahoo Finance via yfinance."""

from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_prices(
    symbols: list[str],
    period: str = "1y",
    interval: str = "1d",
    align: bool = True,
) -> dict[str, pd.Series]:
    """Fetch closing prices for the given symbols.

    When *align* is True (the default), all series are trimmed to the
    common date range so that every symbol covers exactly the same
    periods.  This is essential when mixing ETFs with different
    inception dates (e.g. ``period="max"``).

    Args:
        symbols: List of ticker symbols (e.g. ["AAPL", "MSFT"]).
        period: yfinance period string (e.g. "1y", "6mo", "max").
        interval: yfinance interval string (e.g. "1d", "1wk", "1mo").
        align: If True, align all series to the common date range.

    Returns:
        Dict mapping symbol → pandas Series of closing prices.

    Raises:
        ValueError: If no data could be fetched for a symbol.
    """
    raw: dict[str, pd.Series] = {}
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        hist: pd.DataFrame = ticker.history(period=period, interval=interval)
        if hist.empty:
            msg = f"No price data returned for symbol '{symbol}'"
            raise ValueError(msg)
        series: pd.Series = hist["Close"]
        # Normalize timezone: strip tz so all series share naive UTC dates.
        # yfinance returns different tz for different asset classes
        # (e.g. UTC for crypto, America/New_York for US equities).
        if hasattr(series.index, "tz") and series.index.tz is not None:
            series = series.tz_localize(None)
        raw[symbol] = series

    if not align or len(raw) <= 1:
        return raw

    # Build a combined DataFrame and drop rows where any symbol is missing
    combined = pd.DataFrame(raw).dropna()

    result: dict[str, pd.Series] = {}
    for symbol in symbols:
        result[symbol] = combined[symbol]
    return result
