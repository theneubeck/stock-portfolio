"""High-level portfolio analysis orchestration."""

from __future__ import annotations

from typing import Any

import pandas as pd

from portfolio_analyzer.data import fetch_prices
from portfolio_analyzer.metrics import (
    allocation,
    benchmark_comparison,
    individual_returns,
    risk_metrics,
)
from portfolio_analyzer.models import Portfolio


class PortfolioAnalyzer:
    """Orchestrates data fetching, metric calculation, and report generation.

    Args:
        portfolio: The portfolio to analyze.
        benchmark_symbol: Ticker of the benchmark index (e.g. "URTH").
        period: Look-back period string (e.g. "1y", "6mo", "max").
        interval: Data interval (e.g. "1d", "1wk", "1mo").
    """

    def __init__(
        self,
        portfolio: Portfolio,
        benchmark_symbol: str = "URTH",
        period: str = "1y",
        interval: str = "1d",
    ) -> None:
        self.portfolio = portfolio
        self.benchmark_symbol = benchmark_symbol
        self.period = period
        self.interval = interval
        self.price_data: dict[str, pd.Series] = {}

    def fetch_data(self) -> None:
        """Fetch historical prices for all holdings and the benchmark."""
        all_symbols = [*self.portfolio.symbols, self.benchmark_symbol]
        self.price_data = fetch_prices(all_symbols, period=self.period, interval=self.interval)

    def calculate_individual_returns(self) -> dict[str, dict[str, float]]:
        """Calculate total and annualized returns for each holding."""
        return individual_returns(self.price_data, self.portfolio.symbols, interval=self.interval)

    def calculate_allocation(self) -> dict[str, dict[str, float]]:
        """Calculate market value and weight for each holding."""
        return allocation(self.portfolio, self.price_data)

    def calculate_risk_metrics(self) -> dict[str, float]:
        """Calculate portfolio volatility, Sharpe ratio, and max drawdown."""
        return risk_metrics(self.portfolio, self.price_data, interval=self.interval)

    def compare_to_benchmark(self) -> dict[str, float]:
        """Compare portfolio performance to the benchmark."""
        return benchmark_comparison(self.portfolio, self.price_data, self.benchmark_symbol)

    def run(self) -> dict[str, Any]:
        """Run the full analysis pipeline and return a structured report.

        Returns:
            A dict with keys: summary, allocation, performance, risk,
            benchmark_comparison.
        """
        self.fetch_data()

        alloc = self.calculate_allocation()
        perf = self.calculate_individual_returns()
        risk = self.calculate_risk_metrics()
        comparison = self.compare_to_benchmark()

        total_value = sum(a["market_value"] for a in alloc.values())

        summary: dict[str, Any] = {
            "num_holdings": len(self.portfolio.holdings),
            "total_portfolio_value": total_value,
            "benchmark": self.benchmark_symbol,
            "period": self.period,
            "interval": self.interval,
        }

        return {
            "summary": summary,
            "allocation": alloc,
            "performance": perf,
            "risk": risk,
            "benchmark_comparison": comparison,
        }
