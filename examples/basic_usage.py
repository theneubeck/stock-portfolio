"""Basic usage example for the Portfolio Analyzer."""

from portfolio_analyzer import (
    DCASimulator,
    Holding,
    Portfolio,
    PortfolioAnalyzer,
    PortfolioComparator,
    TargetAllocation,
)
from portfolio_analyzer.report import format_comparison_report, format_dca_report, format_report


def main() -> None:
    """Analyze a balanced 4-asset-class portfolio vs the world index."""
    portfolio = Portfolio(
        holdings=[
            Holding(symbol="GLD", shares=50, name="SPDR Gold Shares"),
            Holding(symbol="GSG", shares=80, name="iShares S&P GSCI Commodity ETF"),
            Holding(symbol="ACWI", shares=60, name="iShares MSCI ACWI ETF"),
            Holding(symbol="AGG", shares=100, name="iShares Core US Aggregate Bond ETF"),
        ]
    )

    analyzer = PortfolioAnalyzer(
        portfolio=portfolio,
        benchmark_symbol="ACWI",
        period="max",
        interval="1mo",
    )

    report = analyzer.run()
    print(format_report(report))

    # ── DCA Simulation ────────────────────────
    print("\n")

    targets = [
        TargetAllocation(symbol="GLD", name="SPDR Gold Shares", target_weight_pct=25.0),
        TargetAllocation(
            symbol="GSG", name="iShares S&P GSCI Commodity ETF", target_weight_pct=25.0
        ),
        TargetAllocation(symbol="ACWI", name="iShares MSCI ACWI ETF", target_weight_pct=25.0),
        TargetAllocation(
            symbol="AGG",
            name="iShares Core US Aggregate Bond ETF",
            target_weight_pct=25.0,
        ),
    ]

    simulator = DCASimulator(
        targets=targets,
        monthly_investment=100,
        rebalance_every_months=6,
        benchmark_symbol="ACWI",
        period="max",
        interval="1mo",
    )

    dca_result = simulator.run()
    print(format_dca_report(dca_result))

    # ── Multi-Portfolio Comparison ────────────
    print("\n")

    comparator = PortfolioComparator(
        strategies=[
            {"name": "Equal Weight", "weights": {"GLD": 25, "GSG": 25, "ACWI": 25, "AGG": 25}},
            {"name": "Heavy Gold", "weights": {"GLD": 50, "GSG": 10, "ACWI": 20, "AGG": 20}},
            {"name": "Stocks & Bonds", "weights": {"GLD": 0, "GSG": 0, "ACWI": 60, "AGG": 40}},
            {"name": "All Weather", "weights": {"GLD": 30, "GSG": 15, "ACWI": 30, "AGG": 25}},
        ],
        monthly_investment=100,
        rebalance_every_months=6,
        benchmark_symbol="ACWI",
        period="max",
        interval="1mo",
    )

    comparison_result = comparator.run()
    print(format_comparison_report(comparison_result))


if __name__ == "__main__":
    main()
