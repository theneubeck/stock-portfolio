"""Portfolio metric calculations (returns, risk, allocation)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from portfolio_analyzer.models import Portfolio

RISK_FREE_RATE = 0.04  # 4 % annualized, approximate T-bill yield

# Mapping from yfinance interval codes to periods-per-year
PERIODS_PER_YEAR: dict[str, int] = {
    "1d": 252,
    "1wk": 52,
    "1mo": 12,
}


def periods_per_year_for(interval: str) -> int:
    """Return the number of periods per year for a given interval.

    Args:
        interval: yfinance interval string (e.g. "1d", "1wk", "1mo").

    Returns:
        Number of periods in one year.

    Raises:
        ValueError: If the interval is not recognised.
    """
    if interval not in PERIODS_PER_YEAR:
        msg = f"Unsupported interval '{interval}'. Use one of: {list(PERIODS_PER_YEAR)}"
        raise ValueError(msg)
    return PERIODS_PER_YEAR[interval]


def total_return(prices: pd.Series) -> float:
    """Calculate total return as a percentage.

    Args:
        prices: Time-series of closing prices, oldest first.

    Returns:
        Total return in percent (e.g. 12.5 for 12.5 %).
    """
    first: float = float(prices.iloc[0])
    last: float = float(prices.iloc[-1])
    return ((last - first) / first) * 100.0


def annualized_return(prices: pd.Series, periods_per_yr: int = 252) -> float:
    """Calculate annualized return from a price series.

    Args:
        prices: Time-series of closing prices.
        periods_per_yr: Number of data periods per year (252 for daily,
            52 for weekly, 12 for monthly).

    Returns:
        Annualized return in percent.
    """
    first: float = float(prices.iloc[0])
    last: float = float(prices.iloc[-1])
    n_periods = len(prices)
    if n_periods <= 1 or first <= 0:
        return 0.0
    total = last / first
    ann: float = float(total ** (periods_per_yr / n_periods) - 1)
    return ann * 100.0


def individual_returns(
    price_data: dict[str, pd.Series],
    symbols: list[str],
    interval: str = "1d",
) -> dict[str, dict[str, float]]:
    """Calculate total and annualized return for each symbol.

    Args:
        price_data: Mapping of symbol → closing price series.
        symbols: Symbols to calculate returns for.
        interval: Data interval (e.g. "1d", "1mo").

    Returns:
        Mapping of symbol → {total_return_pct, annualized_return_pct}.
    """
    ppy = periods_per_year_for(interval)
    result: dict[str, dict[str, float]] = {}
    for symbol in symbols:
        prices = price_data[symbol]
        result[symbol] = {
            "total_return_pct": total_return(prices),
            "annualized_return_pct": annualized_return(prices, periods_per_yr=ppy),
        }
    return result


def allocation(
    portfolio: Portfolio,
    price_data: dict[str, pd.Series],
) -> dict[str, dict[str, float]]:
    """Calculate market value and weight for each holding.

    Args:
        portfolio: The portfolio with holdings.
        price_data: Mapping of symbol → closing price series.

    Returns:
        Mapping of symbol → {market_value, weight_pct}.
    """
    values: dict[str, float] = {}
    for holding in portfolio.holdings:
        latest_price: float = float(price_data[holding.symbol].iloc[-1])
        values[holding.symbol] = latest_price * holding.shares

    total_value = sum(values.values())
    result: dict[str, dict[str, float]] = {}
    for symbol, mv in values.items():
        result[symbol] = {
            "market_value": mv,
            "weight_pct": (mv / total_value) * 100.0 if total_value > 0 else 0.0,
        }
    return result


def portfolio_periodic_returns(
    portfolio: Portfolio,
    price_data: dict[str, pd.Series],
) -> pd.Series:
    """Calculate weighted periodic returns for the whole portfolio.

    Uses start-of-period weights (fixed weight based on initial prices).

    Args:
        portfolio: The portfolio with holdings.
        price_data: Mapping of symbol → closing price series.

    Returns:
        A pandas Series of periodic portfolio returns.
    """
    frames: dict[str, pd.Series] = {}
    for holding in portfolio.holdings:
        prices = price_data[holding.symbol]
        frames[holding.symbol] = prices.pct_change().dropna()

    returns_df = pd.DataFrame(frames).dropna()

    # Compute initial weights from first available prices
    initial_values: dict[str, float] = {}
    for holding in portfolio.holdings:
        first_price: float = float(price_data[holding.symbol].iloc[0])
        initial_values[holding.symbol] = first_price * holding.shares

    total_initial = sum(initial_values.values())
    weights = pd.Series({sym: val / total_initial for sym, val in initial_values.items()})

    weighted: pd.Series = returns_df.dot(weights)
    return weighted


def risk_metrics(
    portfolio: Portfolio,
    price_data: dict[str, pd.Series],
    interval: str = "1d",
    risk_free_rate: float = RISK_FREE_RATE,
) -> dict[str, float]:
    """Calculate volatility, Sharpe ratio, and max drawdown for the portfolio.

    Args:
        portfolio: The portfolio.
        price_data: Symbol → price series.
        interval: Data interval (e.g. "1d", "1mo").
        risk_free_rate: Annualized risk-free rate (decimal).

    Returns:
        Dict with volatility_pct, sharpe_ratio, max_drawdown_pct.
    """
    ppy = periods_per_year_for(interval)
    periodic = portfolio_periodic_returns(portfolio, price_data)

    # Annualized volatility
    vol: float = float(periodic.std() * np.sqrt(ppy)) * 100.0

    # Sharpe ratio
    ann_return: float = float(periodic.mean() * ppy)
    sharpe: float = (
        (ann_return - risk_free_rate) / (periodic.std() * np.sqrt(ppy))
        if periodic.std() > 0
        else 0.0
    )
    sharpe = float(sharpe)

    # Max drawdown from cumulative returns
    cum = (1 + periodic).cumprod()
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max
    max_dd: float = float(drawdown.min()) * 100.0

    return {
        "volatility_pct": vol,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_dd,
    }


def benchmark_comparison(
    portfolio: Portfolio,
    price_data: dict[str, pd.Series],
    benchmark_symbol: str,
) -> dict[str, float]:
    """Compare portfolio return to benchmark return.

    Args:
        portfolio: The portfolio.
        price_data: Symbol → price series (must include benchmark).
        benchmark_symbol: Ticker of the benchmark index.

    Returns:
        Dict with portfolio_return_pct, benchmark_return_pct, excess_return_pct.
    """
    periodic = portfolio_periodic_returns(portfolio, price_data)
    cum = (1 + periodic).cumprod()
    port_ret: float = (float(cum.iloc[-1]) - 1.0) * 100.0

    bench_ret: float = total_return(price_data[benchmark_symbol])

    return {
        "portfolio_return_pct": port_ret,
        "benchmark_return_pct": bench_ret,
        "excess_return_pct": port_ret - bench_ret,
    }
