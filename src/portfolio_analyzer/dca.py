"""Dollar-cost averaging simulation with periodic rebalancing."""

from __future__ import annotations

from typing import Any

import pandas as pd

from portfolio_analyzer.data import fetch_prices
from portfolio_analyzer.metrics import periods_per_year_for, total_return
from portfolio_analyzer.models import TargetAllocation


class DCASimulator:
    """Simulate monthly DCA investing with periodic rebalancing.

    Each month the investor contributes a fixed dollar amount, split
    across assets according to target weights.  Every *rebalance_every_months*
    months the portfolio is rebalanced back to the target allocation.

    Args:
        targets: Target allocation per asset.
        monthly_investment: Dollar amount invested each month.
        rebalance_every_months: Rebalance frequency in months (0 for never).
        benchmark_symbol: Ticker to compare against.
        period: yfinance period string (e.g. "max").
        interval: yfinance interval string (should be "1mo" for monthly DCA).
    """

    def __init__(
        self,
        targets: list[TargetAllocation],
        monthly_investment: float,
        rebalance_every_months: int,
        benchmark_symbol: str = "ACWI",
        period: str = "max",
        interval: str = "1mo",
    ) -> None:
        self.targets = targets
        self.monthly_investment = monthly_investment
        self.rebalance_every_months = rebalance_every_months
        self.benchmark_symbol = benchmark_symbol
        self.period = period
        self.interval = interval
        self.price_data: dict[str, pd.Series] = {}

    @property
    def symbols(self) -> list[str]:
        """Return list of asset symbols."""
        return [t.symbol for t in self.targets]

    @property
    def target_weight_map(self) -> dict[str, float]:
        """Return symbol → target weight percent."""
        return {t.symbol: t.target_weight_pct for t in self.targets}

    def fetch_data(self) -> None:
        """Fetch aligned monthly price data for all assets and benchmark."""
        all_symbols = [*self.symbols, self.benchmark_symbol]
        # De-duplicate if benchmark is also a holding
        unique = list(dict.fromkeys(all_symbols))
        self.price_data = fetch_prices(unique, period=self.period, interval=self.interval)

    def run(self) -> dict[str, Any]:
        """Run the full DCA simulation.

        Returns:
            Dict with keys: summary, value_history, rebalancing_log, comparison.
        """
        self.fetch_data()

        symbols = self.symbols
        target_weights = self.target_weight_map

        # Use the common date index from any symbol
        dates = self.price_data[symbols[0]].index
        n_periods = len(dates)

        # State: shares held per symbol (fractional)
        shares: dict[str, float] = {s: 0.0 for s in symbols}
        total_invested = 0.0

        # Tracking
        value_history_values: list[float] = []
        value_history_dates: list[Any] = []
        activity_log: list[dict[str, Any]] = []
        months_since_rebalance = 0

        for i in range(n_periods):
            date = dates[i]
            prices_now: dict[str, float] = {s: float(self.price_data[s].iloc[i]) for s in symbols}

            # ── Invest this month's contribution ──
            for symbol in symbols:
                weight = target_weights[symbol] / 100.0
                amount = self.monthly_investment * weight
                price = prices_now[symbol]
                if price > 0:
                    shares[symbol] += amount / price
            total_invested += self.monthly_investment
            months_since_rebalance += 1

            # Log the buy action
            current_value_after_buy = sum(shares[s] * prices_now[s] for s in symbols)
            activity_log.append(
                {
                    "date": date,
                    "action": "Buy",
                    "amount": self.monthly_investment,
                    "portfolio_value": current_value_after_buy,
                }
            )

            # ── Rebalance if it's time ──
            if (
                self.rebalance_every_months > 0
                and months_since_rebalance >= self.rebalance_every_months
                and i > 0
            ):
                portfolio_value = sum(shares[s] * prices_now[s] for s in symbols)
                if portfolio_value > 0:
                    weights_before: dict[str, float] = {
                        s: (shares[s] * prices_now[s] / portfolio_value) * 100.0 for s in symbols
                    }

                    # Rebalance: redistribute to target weights
                    for symbol in symbols:
                        target_value = portfolio_value * (target_weights[symbol] / 100.0)
                        if prices_now[symbol] > 0:
                            shares[symbol] = target_value / prices_now[symbol]

                    weights_after: dict[str, float] = {
                        s: (shares[s] * prices_now[s] / portfolio_value) * 100.0 for s in symbols
                    }

                    activity_log.append(
                        {
                            "date": date,
                            "action": "Rebalance",
                            "portfolio_value": portfolio_value,
                            "weights_before": weights_before,
                            "weights_after": weights_after,
                            "target_weights": dict(target_weights),
                        }
                    )
                    months_since_rebalance = 0

            # ── Record portfolio value ──
            current_value = sum(shares[s] * prices_now[s] for s in symbols)
            value_history_values.append(current_value)
            value_history_dates.append(date)

        # ── Final state ──
        final_value = value_history_values[-1] if value_history_values else 0.0
        total_return_pct = (
            ((final_value - total_invested) / total_invested) * 100.0
            if total_invested > 0
            else 0.0
        )

        # Annualized return using XIRR-like approximation:
        # We use the geometric approach over the number of years
        ppy = periods_per_year_for(self.interval)
        n_years = n_periods / ppy if ppy > 0 else 1.0
        # For DCA the simple annualized approach is:
        # average dollar has been invested for n_years/2, but we use
        # the money-weighted approach: ((final/invested)^(1/n_years) - 1)
        annualized_pct = 0.0
        if total_invested > 0 and n_years > 0 and final_value > 0:
            annualized_pct = float((final_value / total_invested) ** (1.0 / n_years) - 1.0) * 100.0

        value_history = pd.Series(
            value_history_values,
            index=pd.DatetimeIndex(value_history_dates),
            name="portfolio_value",
        )

        # ── Comparison: DCA vs lump-sum vs benchmark ──
        comparison = self._build_comparison(
            total_invested=total_invested,
            final_value=final_value,
            n_periods=n_periods,
        )

        num_rebalances = sum(1 for e in activity_log if e["action"] == "Rebalance")

        summary: dict[str, Any] = {
            "total_invested": total_invested,
            "final_value": final_value,
            "total_return_pct": total_return_pct,
            "annualized_return_pct": annualized_pct,
            "num_investments": n_periods,
            "num_periods": n_periods,
            "num_rebalances": num_rebalances,
            "final_shares": shares,
            "final_prices": {s: float(self.price_data[s].iloc[-1]) for s in symbols},
        }

        return {
            "summary": summary,
            "value_history": value_history,
            "activity_log": activity_log,
            "comparison": comparison,
        }

    def _build_comparison(
        self,
        total_invested: float,
        final_value: float,
        n_periods: int,
    ) -> dict[str, float]:
        """Compare DCA outcome to lump-sum and benchmark buy-and-hold.

        For lump-sum: assume the same total amount was invested at the
        start, split according to target weights.

        For benchmark: assume the same total amount was invested in
        the benchmark at the start.
        """
        symbols = self.symbols
        target_weights = self.target_weight_map

        # ── Lump-sum: invest total_invested at period start ──
        lump_sum_value = 0.0
        for symbol in symbols:
            prices = self.price_data[symbol]
            first_price = float(prices.iloc[0])
            last_price = float(prices.iloc[-1])
            weight = target_weights[symbol] / 100.0
            amount = total_invested * weight
            if first_price > 0:
                lump_shares = amount / first_price
                lump_sum_value += lump_shares * last_price

        lump_sum_return_pct = (
            ((lump_sum_value - total_invested) / total_invested) * 100.0
            if total_invested > 0
            else 0.0
        )

        # ── Benchmark: invest total_invested in benchmark at start ──
        bench_prices = self.price_data[self.benchmark_symbol]
        bench_return_pct = total_return(bench_prices)

        # What the benchmark lump-sum would be worth
        bench_first = float(bench_prices.iloc[0])
        bench_last = float(bench_prices.iloc[-1])
        bench_lump_value = 0.0
        if bench_first > 0:
            bench_lump_value = total_invested * (bench_last / bench_first)

        return {
            "dca_final_value": final_value,
            "dca_return_pct": (
                ((final_value - total_invested) / total_invested) * 100.0
                if total_invested > 0
                else 0.0
            ),
            "lump_sum_final_value": lump_sum_value,
            "lump_sum_return_pct": lump_sum_return_pct,
            "benchmark_final_value": bench_lump_value,
            "benchmark_return_pct": bench_return_pct,
            "total_invested": total_invested,
        }
