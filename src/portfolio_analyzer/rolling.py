"""Rolling N-year buy-and-hold return analysis.

The key insight: given a price series, shift it by N years and divide.
This produces a vector of all possible N-year buy-and-hold returns —
one for every possible entry date.  From this distribution we can
derive mean, median, Sharpe ratio, worst/best outcomes, etc.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from portfolio_analyzer.metrics import RISK_FREE_RATE, periods_per_year_for


def rolling_returns(
    prices: pd.Series,
    horizon_years: int = 5,
    interval: str = "1mo",
) -> pd.Series:
    """Compute all N-year buy-and-hold returns from a price series.

    For each date *t* that has a corresponding date *t + N years* in the
    series, the return is ``prices[t+N] / prices[t] - 1`` expressed as
    a percentage.

    Args:
        prices: Time-series of closing prices, oldest first.
        horizon_years: Investment horizon in years.
        interval: Data interval (``"1d"``, ``"1wk"``, or ``"1mo"``).

    Returns:
        A pandas Series indexed by the *entry date*, with values being
        the total return in percent for holding *horizon_years* from
        that date.
    """
    ppy = periods_per_year_for(interval)
    offset = horizon_years * ppy

    if offset >= len(prices):
        return pd.Series(dtype=float, name="rolling_return_pct")

    start_vals: np.ndarray[Any, np.dtype[np.floating[Any]]] = np.asarray(
        prices.iloc[: len(prices) - offset], dtype=np.float64
    )
    end_vals: np.ndarray[Any, np.dtype[np.floating[Any]]] = np.asarray(
        prices.iloc[offset:], dtype=np.float64
    )

    returns_pct: pd.Series = pd.Series(
        (end_vals / start_vals - 1.0) * 100.0,
        index=prices.iloc[: len(prices) - offset].index,
        name="rolling_return_pct",
    )
    return returns_pct


def rolling_return_statistics(
    returns: pd.Series,
    horizon_years: int = 5,
    risk_free_rate: float = RISK_FREE_RATE,
) -> dict[str, Any]:
    """Compute summary statistics for a rolling-return distribution.

    Args:
        returns: Series of rolling N-year returns in percent (from
            :func:`rolling_returns`).
        horizon_years: The horizon used (for annualisation).
        risk_free_rate: Annualised risk-free rate (decimal, e.g. 0.04).

    Returns:
        Dict with descriptive statistics of the return distribution.
    """
    if len(returns) == 0:
        return {
            "mean_return_pct": 0.0,
            "median_return_pct": 0.0,
            "std_return_pct": 0.0,
            "best_return_pct": 0.0,
            "worst_return_pct": 0.0,
            "best_entry_date": "",
            "worst_entry_date": "",
            "sharpe_ratio": 0.0,
            "positive_pct": 0.0,
            "count": 0,
        }

    mean_ret = float(returns.mean())
    std_ret = float(returns.std())

    # Annualise for Sharpe: convert total N-year return to annualised
    # mean_annual = (1 + mean_ret/100)^(1/N) - 1
    mean_annual = (1.0 + mean_ret / 100.0) ** (1.0 / horizon_years) - 1.0
    std_annual = std_ret / 100.0 / np.sqrt(horizon_years)
    sharpe = float((mean_annual - risk_free_rate) / std_annual) if std_annual > 0 else 0.0

    best_idx = returns.idxmax()
    worst_idx = returns.idxmin()

    return {
        "mean_return_pct": mean_ret,
        "median_return_pct": float(returns.median()),
        "std_return_pct": std_ret,
        "best_return_pct": float(returns.max()),
        "worst_return_pct": float(returns.min()),
        "best_entry_date": str(pd.Timestamp(best_idx).date()),
        "worst_entry_date": str(pd.Timestamp(worst_idx).date()),
        "sharpe_ratio": sharpe,
        "positive_pct": float((returns > 0).sum() / len(returns) * 100.0),
        "count": len(returns),
    }


def rolling_return_histogram(
    returns: pd.Series,
    bins: int = 20,
) -> list[dict[str, float]]:
    """Bucket rolling returns into a histogram for display.

    Args:
        returns: Series of rolling N-year returns in percent.
        bins: Number of histogram bins.

    Returns:
        List of dicts with ``bin_start``, ``bin_end``, ``count``,
        and ``pct`` keys.
    """
    if len(returns) == 0:
        return []

    values: np.ndarray[Any, np.dtype[np.floating[Any]]] = np.asarray(
        returns.values, dtype=np.float64
    )
    counts, edges = np.histogram(values, bins=bins)
    total = int(counts.sum())
    result: list[dict[str, float]] = []
    for i in range(len(counts)):
        result.append(
            {
                "bin_start": float(edges[i]),
                "bin_end": float(edges[i + 1]),
                "count": int(counts[i]),
                "pct": float(counts[i] / total * 100.0) if total > 0 else 0.0,
            }
        )
    return result
