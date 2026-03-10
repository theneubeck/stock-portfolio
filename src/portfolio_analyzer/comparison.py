"""Compare multiple portfolio strategies side by side."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from portfolio_analyzer.data import fetch_prices
from portfolio_analyzer.metrics import RISK_FREE_RATE, periods_per_year_for, total_return


class PortfolioComparator:
    """Run the same DCA simulation for multiple allocation strategies and compare.

    All strategies share the same universe of assets, monthly investment,
    rebalance frequency, and time period — only the target weights differ.

    Args:
        strategies: List of dicts each with ``name`` (str) and
            ``weights`` (dict[str, float] of symbol → weight %).
        monthly_investment: Dollar amount invested each month.
        rebalance_every_months: Rebalance frequency in months.
        benchmark_symbol: Ticker of the benchmark index.
        period: yfinance period string.
        interval: yfinance interval string.
    """

    def __init__(
        self,
        strategies: list[dict[str, Any]],
        monthly_investment: float,
        rebalance_every_months: int,
        benchmark_symbol: str = "ACWI",
        period: str = "max",
        interval: str = "1mo",
    ) -> None:
        self.strategies = strategies
        self.monthly_investment = monthly_investment
        self.rebalance_every_months = rebalance_every_months
        self.benchmark_symbol = benchmark_symbol
        self.period = period
        self.interval = interval
        self.price_data: dict[str, pd.Series] = {}

    def _all_symbols(self) -> list[str]:
        """Collect all unique symbols across all strategies + benchmark."""
        symbols: set[str] = set()
        for strategy in self.strategies:
            for sym in strategy["weights"]:
                symbols.add(sym)
        symbols.add(self.benchmark_symbol)
        return sorted(symbols)

    def fetch_data(self) -> None:
        """Fetch price data once for all symbols."""
        self.price_data = fetch_prices(
            self._all_symbols(),
            period=self.period,
            interval=self.interval,
        )

    def _simulate_strategy(
        self,
        name: str,
        weights: dict[str, float],
    ) -> dict[str, Any]:
        """Run a single DCA simulation for one strategy.

        Returns a flat dict with strategy-level summary metrics.
        """
        symbols = [s for s in weights if weights[s] > 0]
        dates = self.price_data[symbols[0]].index
        n_periods = len(dates)

        shares: dict[str, float] = {s: 0.0 for s in symbols}
        total_invested = 0.0
        months_since_rebalance = 0

        value_history: list[float] = []

        for i in range(n_periods):
            prices_now: dict[str, float] = {s: float(self.price_data[s].iloc[i]) for s in symbols}

            # Invest
            for symbol in symbols:
                w = weights[symbol] / 100.0
                amount = self.monthly_investment * w
                price = prices_now[symbol]
                if price > 0:
                    shares[symbol] += amount / price
            total_invested += self.monthly_investment
            months_since_rebalance += 1

            # Rebalance
            if months_since_rebalance >= self.rebalance_every_months and i > 0:
                pv = sum(shares[s] * prices_now[s] for s in symbols)
                if pv > 0:
                    for symbol in symbols:
                        target_val = pv * (weights[symbol] / 100.0)
                        if prices_now[symbol] > 0:
                            shares[symbol] = target_val / prices_now[symbol]
                    months_since_rebalance = 0

            current_value = sum(shares[s] * prices_now[s] for s in symbols)
            value_history.append(current_value)

        final_value = value_history[-1] if value_history else 0.0
        total_return_pct = (
            ((final_value - total_invested) / total_invested) * 100.0
            if total_invested > 0
            else 0.0
        )

        # Benchmark return
        bench_return_pct = total_return(self.price_data[self.benchmark_symbol])
        excess_return_pct = total_return_pct - bench_return_pct

        # Risk metrics from value history periodic returns
        value_series = pd.Series(value_history)
        periodic_returns = value_series.pct_change().dropna()

        ppy = periods_per_year_for(self.interval)
        vol = float(periodic_returns.std() * np.sqrt(ppy)) * 100.0

        ann_return = float(periodic_returns.mean() * ppy)
        sharpe = 0.0
        if periodic_returns.std() > 0:
            sharpe = float((ann_return - RISK_FREE_RATE) / (periodic_returns.std() * np.sqrt(ppy)))

        cum = (1 + periodic_returns).cumprod()
        running_max = cum.cummax()
        drawdown = (cum - running_max) / running_max
        max_dd = float(drawdown.min()) * 100.0

        return {
            "name": name,
            "weights": weights,
            "total_invested": total_invested,
            "final_value": final_value,
            "total_return_pct": total_return_pct,
            "excess_return_pct": excess_return_pct,
            "volatility_pct": vol,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_dd,
            "num_periods": n_periods,
        }

    def run(self) -> dict[str, Any]:
        """Run all strategies and build the comparison result.

        Returns:
            Dict with keys:
            - strategies: list of per-strategy result dicts
            - ranking: strategies sorted by total return (best first)
            - benchmark_return_pct: benchmark total return
            - beat_benchmark: list of strategy names that beat benchmark
            - underperformed_benchmark: list of strategy names that didn't
        """
        self.fetch_data()

        results: list[dict[str, Any]] = []
        for strategy in self.strategies:
            result = self._simulate_strategy(
                name=strategy["name"],
                weights=strategy["weights"],
            )
            results.append(result)

        # Ranking by total return (descending)
        ranking = sorted(results, key=lambda r: r["total_return_pct"], reverse=True)

        bench_return_pct = total_return(self.price_data[self.benchmark_symbol])

        beat: list[str] = []
        underperformed: list[str] = []
        for r in results:
            if r["excess_return_pct"] >= 0:
                beat.append(r["name"])
            else:
                underperformed.append(r["name"])

        return {
            "strategies": results,
            "ranking": ranking,
            "benchmark_return_pct": bench_return_pct,
            "benchmark_symbol": self.benchmark_symbol,
            "beat_benchmark": beat,
            "underperformed_benchmark": underperformed,
        }
