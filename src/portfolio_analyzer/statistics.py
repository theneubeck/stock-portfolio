"""Descriptive statistics for individual holdings and the overall portfolio."""

from __future__ import annotations

from typing import Any

import pandas as pd

from portfolio_analyzer.metrics import portfolio_periodic_returns
from portfolio_analyzer.models import Portfolio


def per_holding_statistics(
    price_data: dict[str, pd.Series],
    symbols: list[str],
    interval: str = "1mo",
) -> dict[str, dict[str, Any]]:
    """Calculate descriptive statistics for each holding.

    For each symbol returns price extremes (min, max, median with dates)
    and return distribution stats (best/worst period, median, std dev).

    Args:
        price_data: Mapping of symbol → closing price series.
        symbols: Symbols to calculate stats for.
        interval: Data interval (for labelling; not used in calculation).

    Returns:
        Mapping of symbol → stat dict.
    """
    result: dict[str, dict[str, Any]] = {}

    for symbol in symbols:
        prices = price_data[symbol]
        returns = prices.pct_change().dropna()

        # Price extremes
        min_idx = prices.idxmin()
        max_idx = prices.idxmax()

        # Return extremes
        best_idx = returns.idxmax()
        worst_idx = returns.idxmin()

        result[symbol] = {
            # Price extremes
            "min_price": float(prices.min()),
            "min_price_date": min_idx,
            "max_price": float(prices.max()),
            "max_price_date": max_idx,
            "median_price": float(prices.median()),
            # Return distribution
            "best_period_return_pct": float(returns.max()) * 100.0,
            "best_period_date": best_idx,
            "worst_period_return_pct": float(returns.min()) * 100.0,
            "worst_period_date": worst_idx,
            "median_return_pct": float(returns.median()) * 100.0,
            "mean_return_pct": float(returns.mean()) * 100.0,
            "return_std_pct": float(returns.std()) * 100.0,
            "positive_periods": int((returns > 0).sum()),
            "negative_periods": int((returns < 0).sum()),
            "total_periods": len(returns),
        }

    return result


def portfolio_statistics(
    portfolio: Portfolio,
    price_data: dict[str, pd.Series],
    interval: str = "1mo",
) -> dict[str, Any]:
    """Calculate descriptive statistics for the overall portfolio.

    Computes a portfolio value time series from weighted returns, then
    derives extremes and return distribution stats.

    Args:
        portfolio: The portfolio with holdings.
        price_data: Symbol → closing price series.
        interval: Data interval.

    Returns:
        Dict with peak/trough values (and dates), return distribution stats.
    """
    # Build a portfolio value series from initial-value-weighted returns
    periodic = portfolio_periodic_returns(portfolio, price_data)
    cum = (1 + periodic).cumprod()

    # Scale to initial portfolio dollar value
    initial_value = 0.0
    for holding in portfolio.holdings:
        first_price = float(price_data[holding.symbol].iloc[0])
        initial_value += first_price * holding.shares

    value_series = cum * initial_value

    # Current (latest) portfolio value from actual last prices
    current_value = 0.0
    for holding in portfolio.holdings:
        last_price = float(price_data[holding.symbol].iloc[-1])
        current_value += last_price * holding.shares

    # Value extremes
    peak_idx = value_series.idxmax()
    trough_idx = value_series.idxmin()

    # Return distribution
    best_idx = periodic.idxmax()
    worst_idx = periodic.idxmin()

    return {
        # Value extremes
        "peak_value": float(value_series.max()),
        "peak_value_date": peak_idx,
        "trough_value": float(value_series.min()),
        "trough_value_date": trough_idx,
        "current_value": current_value,
        # Return distribution
        "best_period_return_pct": float(periodic.max()) * 100.0,
        "best_period_date": best_idx,
        "worst_period_return_pct": float(periodic.min()) * 100.0,
        "worst_period_date": worst_idx,
        "median_return_pct": float(periodic.median()) * 100.0,
        "mean_return_pct": float(periodic.mean()) * 100.0,
        "return_std_pct": float(periodic.std()) * 100.0,
        "positive_periods": int((periodic > 0).sum()),
        "negative_periods": int((periodic < 0).sum()),
        "total_periods": len(periodic),
    }
