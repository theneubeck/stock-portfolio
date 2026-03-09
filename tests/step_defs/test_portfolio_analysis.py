"""Step definitions for portfolio analysis feature."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when


@scenario(
    "../features/portfolio_analysis.feature",
    "Fetch historical prices for all holdings and benchmark",
)
def test_fetch_prices() -> None:
    """Fetch historical prices for all holdings and benchmark."""


@scenario(
    "../features/portfolio_analysis.feature",
    "Calculate individual holding returns",
)
def test_individual_returns() -> None:
    """Calculate individual holding returns."""


@scenario(
    "../features/portfolio_analysis.feature",
    "Calculate portfolio total value and weights",
)
def test_portfolio_allocation() -> None:
    """Calculate portfolio total value and weights."""


@scenario(
    "../features/portfolio_analysis.feature",
    "Calculate portfolio risk metrics",
)
def test_risk_metrics() -> None:
    """Calculate portfolio risk metrics."""


@scenario(
    "../features/portfolio_analysis.feature",
    "Compare portfolio to the world index benchmark",
)
def test_benchmark_comparison() -> None:
    """Compare portfolio to the world index benchmark."""


@scenario(
    "../features/portfolio_analysis.feature",
    "Generate a full analysis report",
)
def test_full_report() -> None:
    """Generate a full analysis report."""


# ── Shared context ────────────────────────────────


@pytest.fixture()
def context() -> dict[str, Any]:
    """Shared mutable state across steps."""
    return {}


# ── GIVEN steps ───────────────────────────────────


@given(
    parsers.parse("a portfolio with the following holdings:"),
    target_fixture="context",
)
def given_portfolio_holdings(
    context: dict[str, Any], datatable: list[list[str]]
) -> dict[str, Any]:
    """Build holdings from the Gherkin data table."""
    from portfolio_analyzer.models import Holding, Portfolio

    headers = datatable[0]
    rows = datatable[1:]
    holdings = []
    for row in rows:
        parsed = dict(zip(headers, row, strict=True))
        holdings.append(
            Holding(
                symbol=parsed["symbol"],
                shares=int(parsed["shares"]),
                name=parsed["name"],
            )
        )
    context["portfolio"] = Portfolio(holdings=holdings)
    return context


@given(parsers.parse('the benchmark is "{benchmark}"'))
def given_benchmark(context: dict[str, Any], benchmark: str) -> None:
    """Set the benchmark symbol."""
    context["benchmark"] = benchmark


@given(parsers.parse("the analysis period is {period}"))
def given_analysis_period(context: dict[str, Any], period: str) -> None:
    """Set the analysis look-back period, converting human-readable to yfinance format."""
    period_map: dict[str, str] = {
        "1 year": "1y",
        "6 months": "6mo",
        "3 months": "3mo",
        "1 month": "1mo",
        "5 years": "5y",
        "2 years": "2y",
    }
    context["period"] = period_map.get(period, period)


@given(parsers.parse("the data interval is {interval}"))
def given_data_interval(context: dict[str, Any], interval: str) -> None:
    """Set the data interval, converting human-readable to yfinance format."""
    interval_map: dict[str, str] = {
        "daily": "1d",
        "weekly": "1wk",
        "monthly": "1mo",
    }
    context["interval"] = interval_map.get(interval, interval)


# ── WHEN steps ────────────────────────────────────


@when("I fetch historical price data")
def when_fetch_prices(context: dict[str, Any]) -> None:
    """Fetch historical prices via the data provider."""
    from portfolio_analyzer.analyzer import PortfolioAnalyzer

    analyzer = PortfolioAnalyzer(
        portfolio=context["portfolio"],
        benchmark_symbol=context["benchmark"],
        period=context["period"],
        interval=context.get("interval", "1d"),
    )
    analyzer.fetch_data()
    context["analyzer"] = analyzer


@when("I calculate individual returns")
def when_calculate_returns(context: dict[str, Any]) -> None:
    """Calculate returns for each holding."""
    analyzer = context["analyzer"]
    context["individual_returns"] = analyzer.calculate_individual_returns()


@when("I calculate the portfolio allocation")
def when_calculate_allocation(context: dict[str, Any]) -> None:
    """Calculate portfolio allocation weights."""
    analyzer = context["analyzer"]
    context["allocation"] = analyzer.calculate_allocation()


@when("I calculate portfolio risk metrics")
def when_calculate_risk(context: dict[str, Any]) -> None:
    """Calculate portfolio risk metrics."""
    analyzer = context["analyzer"]
    context["risk_metrics"] = analyzer.calculate_risk_metrics()


@when("I compare the portfolio to the benchmark")
def when_compare_benchmark(context: dict[str, Any]) -> None:
    """Compare portfolio performance to the benchmark."""
    analyzer = context["analyzer"]
    context["comparison"] = analyzer.compare_to_benchmark()


@when("I run the full analysis")
def when_full_analysis(context: dict[str, Any]) -> None:
    """Run the full analysis pipeline and generate a report."""
    from portfolio_analyzer.analyzer import PortfolioAnalyzer

    analyzer = PortfolioAnalyzer(
        portfolio=context["portfolio"],
        benchmark_symbol=context["benchmark"],
        period=context["period"],
        interval=context.get("interval", "1d"),
    )
    context["report"] = analyzer.run()


# ── THEN steps ────────────────────────────────────


@then("I should have price data for each holding")
def then_price_data_for_holdings(context: dict[str, Any]) -> None:
    """Verify price data exists for every holding."""
    analyzer = context["analyzer"]
    for holding in context["portfolio"].holdings:
        assert holding.symbol in analyzer.price_data
        assert len(analyzer.price_data[holding.symbol]) > 0


@then("I should have price data for the benchmark")
def then_price_data_for_benchmark(context: dict[str, Any]) -> None:
    """Verify price data exists for the benchmark."""
    analyzer = context["analyzer"]
    assert context["benchmark"] in analyzer.price_data
    assert len(analyzer.price_data[context["benchmark"]]) > 0


@then("each holding should have a total return percentage")
def then_total_return(context: dict[str, Any]) -> None:
    """Each holding must report a total return."""
    for _symbol, metrics in context["individual_returns"].items():
        assert "total_return_pct" in metrics
        assert isinstance(metrics["total_return_pct"], float)


@then("each holding should have an annualized return")
def then_annualized_return(context: dict[str, Any]) -> None:
    """Each holding must report an annualized return."""
    for _symbol, metrics in context["individual_returns"].items():
        assert "annualized_return_pct" in metrics
        assert isinstance(metrics["annualized_return_pct"], float)


@then("each holding should have a current market value")
def then_market_value(context: dict[str, Any]) -> None:
    """Each holding in the allocation must have a market value."""
    for _symbol, alloc in context["allocation"].items():
        assert "market_value" in alloc
        assert alloc["market_value"] > 0


@then("each holding should have a weight as percentage of the portfolio")
def then_weight(context: dict[str, Any]) -> None:
    """Each holding must have a weight."""
    for _symbol, alloc in context["allocation"].items():
        assert "weight_pct" in alloc
        assert 0 < alloc["weight_pct"] <= 100


@then("the weights should sum to 100 percent")
def then_weights_sum(context: dict[str, Any]) -> None:
    """Portfolio weights must sum to 100%."""
    total = sum(alloc["weight_pct"] for alloc in context["allocation"].values())
    assert abs(total - 100.0) < 0.01


@then("the portfolio should have a volatility value")
def then_volatility(context: dict[str, Any]) -> None:
    """Risk metrics must include volatility."""
    assert "volatility_pct" in context["risk_metrics"]
    assert context["risk_metrics"]["volatility_pct"] > 0


@then("the portfolio should have a Sharpe ratio")
def then_sharpe(context: dict[str, Any]) -> None:
    """Risk metrics must include Sharpe ratio."""
    assert "sharpe_ratio" in context["risk_metrics"]
    assert isinstance(context["risk_metrics"]["sharpe_ratio"], float)


@then("the portfolio should have a maximum drawdown")
def then_max_drawdown(context: dict[str, Any]) -> None:
    """Risk metrics must include max drawdown."""
    assert "max_drawdown_pct" in context["risk_metrics"]
    assert context["risk_metrics"]["max_drawdown_pct"] <= 0


@then("I should see the portfolio total return")
def then_portfolio_return(context: dict[str, Any]) -> None:
    """Benchmark comparison must include portfolio return."""
    assert "portfolio_return_pct" in context["comparison"]


@then("I should see the benchmark total return")
def then_benchmark_return(context: dict[str, Any]) -> None:
    """Benchmark comparison must include benchmark return."""
    assert "benchmark_return_pct" in context["comparison"]


@then("I should see the excess return over the benchmark")
def then_excess_return(context: dict[str, Any]) -> None:
    """Benchmark comparison must include excess return."""
    assert "excess_return_pct" in context["comparison"]
    expected = (
        context["comparison"]["portfolio_return_pct"]
        - context["comparison"]["benchmark_return_pct"]
    )
    assert abs(context["comparison"]["excess_return_pct"] - expected) < 0.01


@then("the report should contain a summary section")
def then_report_summary(context: dict[str, Any]) -> None:
    """Report must have a summary section."""
    assert "summary" in context["report"]


@then("the report should contain an allocation section")
def then_report_allocation(context: dict[str, Any]) -> None:
    """Report must have an allocation section."""
    assert "allocation" in context["report"]


@then("the report should contain a performance section")
def then_report_performance(context: dict[str, Any]) -> None:
    """Report must have a performance section."""
    assert "performance" in context["report"]


@then("the report should contain a risk section")
def then_report_risk(context: dict[str, Any]) -> None:
    """Report must have a risk section."""
    assert "risk" in context["report"]


@then("the report should contain a benchmark comparison section")
def then_report_benchmark(context: dict[str, Any]) -> None:
    """Report must have a benchmark comparison section."""
    assert "benchmark_comparison" in context["report"]
