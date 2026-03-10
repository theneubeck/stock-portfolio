"""Step definitions for portfolio descriptive statistics feature."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when


@scenario(
    "../features/portfolio_statistics.feature",
    "Per-holding price extremes",
)
def test_per_holding_price_extremes() -> None:
    """Per-holding price extremes."""


@scenario(
    "../features/portfolio_statistics.feature",
    "Per-holding return distribution",
)
def test_per_holding_return_distribution() -> None:
    """Per-holding return distribution."""


@scenario(
    "../features/portfolio_statistics.feature",
    "Portfolio-level value extremes",
)
def test_portfolio_value_extremes() -> None:
    """Portfolio-level value extremes."""


@scenario(
    "../features/portfolio_statistics.feature",
    "Portfolio-level return distribution",
)
def test_portfolio_return_distribution() -> None:
    """Portfolio-level return distribution."""


@scenario(
    "../features/portfolio_statistics.feature",
    "Portfolio statistics appear in the full report",
)
def test_statistics_in_report() -> None:
    """Portfolio statistics appear in the full report."""


# ── Shared context ────────────────────────────────


@pytest.fixture()
def context() -> dict[str, Any]:
    """Shared mutable state across steps."""
    return {}


# ── GIVEN steps ───────────────────────────────────


@given(
    parsers.parse("a portfolio with the following holdings for statistics:"),
    target_fixture="context",
)
def given_portfolio(context: dict[str, Any], datatable: list[list[str]]) -> dict[str, Any]:
    """Build a portfolio from a Gherkin data table."""
    from portfolio_analyzer.models import Holding, Portfolio

    headers = datatable[0]
    rows = datatable[1:]
    holdings: list[Holding] = []
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
    """Set the analysis look-back period."""
    period_map: dict[str, str] = {
        "1 year": "1y",
        "6 months": "6mo",
        "5 years": "5y",
        "2 years": "2y",
    }
    context["period"] = period_map.get(period, period)


@given(parsers.parse("the data interval is {interval}"))
def given_data_interval(context: dict[str, Any], interval: str) -> None:
    """Set the data interval."""
    interval_map: dict[str, str] = {
        "daily": "1d",
        "weekly": "1wk",
        "monthly": "1mo",
    }
    context["interval"] = interval_map.get(interval, interval)


# ── WHEN steps ────────────────────────────────────


@when("I fetch historical price data")
def when_fetch_data(context: dict[str, Any]) -> None:
    """Fetch price data via the analyzer."""
    from portfolio_analyzer.analyzer import PortfolioAnalyzer

    analyzer = PortfolioAnalyzer(
        portfolio=context["portfolio"],
        benchmark_symbol=context["benchmark"],
        period=context["period"],
        interval=context.get("interval", "1mo"),
    )
    analyzer.fetch_data()
    context["analyzer"] = analyzer
    context["price_data"] = analyzer.price_data


@when("I calculate per-holding statistics")
def when_per_holding_stats(context: dict[str, Any]) -> None:
    """Calculate per-holding descriptive statistics."""
    from portfolio_analyzer.statistics import per_holding_statistics

    context["holding_stats"] = per_holding_statistics(
        price_data=context["price_data"],
        symbols=context["portfolio"].symbols,
        interval=context.get("interval", "1mo"),
    )


@when("I calculate portfolio statistics")
def when_portfolio_stats(context: dict[str, Any]) -> None:
    """Calculate portfolio-level descriptive statistics."""
    from portfolio_analyzer.statistics import portfolio_statistics

    context["portfolio_stats"] = portfolio_statistics(
        portfolio=context["portfolio"],
        price_data=context["price_data"],
        interval=context.get("interval", "1mo"),
    )


@when("I run the full analysis with statistics")
def when_full_analysis_with_stats(context: dict[str, Any]) -> None:
    """Run the full analysis including statistics."""
    from portfolio_analyzer.analyzer import PortfolioAnalyzer

    analyzer = PortfolioAnalyzer(
        portfolio=context["portfolio"],
        benchmark_symbol=context["benchmark"],
        period=context["period"],
        interval=context.get("interval", "1mo"),
    )
    context["report"] = analyzer.run()


# ── THEN: Per-holding price extremes ──────────────


@then("each holding should have a minimum price and its date")
def then_min_price(context: dict[str, Any]) -> None:
    for symbol, stats in context["holding_stats"].items():
        assert "min_price" in stats, f"{symbol} missing min_price"
        assert "min_price_date" in stats, f"{symbol} missing min_price_date"
        assert stats["min_price"] > 0, f"{symbol} min_price should be positive"


@then("each holding should have a maximum price and its date")
def then_max_price(context: dict[str, Any]) -> None:
    for symbol, stats in context["holding_stats"].items():
        assert "max_price" in stats, f"{symbol} missing max_price"
        assert "max_price_date" in stats, f"{symbol} missing max_price_date"
        assert stats["max_price"] > 0, f"{symbol} max_price should be positive"


@then("each holding should have a median price")
def then_median_price(context: dict[str, Any]) -> None:
    for symbol, stats in context["holding_stats"].items():
        assert "median_price" in stats, f"{symbol} missing median_price"
        assert stats["median_price"] > 0


@then("the maximum price should be greater than or equal to the minimum price")
def then_max_gte_min(context: dict[str, Any]) -> None:
    for symbol, stats in context["holding_stats"].items():
        assert stats["max_price"] >= stats["min_price"], (
            f"{symbol}: max {stats['max_price']} < min {stats['min_price']}"
        )


# ── THEN: Per-holding return distribution ─────────


@then("each holding should have a best single-period return and its date")
def then_best_return(context: dict[str, Any]) -> None:
    for symbol, stats in context["holding_stats"].items():
        assert "best_period_return_pct" in stats, f"{symbol} missing best_period_return_pct"
        assert "best_period_date" in stats, f"{symbol} missing best_period_date"


@then("each holding should have a worst single-period return and its date")
def then_worst_return(context: dict[str, Any]) -> None:
    for symbol, stats in context["holding_stats"].items():
        assert "worst_period_return_pct" in stats, f"{symbol} missing worst_period_return_pct"
        assert "worst_period_date" in stats, f"{symbol} missing worst_period_date"
        assert stats["worst_period_return_pct"] <= stats["best_period_return_pct"]


@then("each holding should have a median periodic return")
def then_median_return(context: dict[str, Any]) -> None:
    for symbol, stats in context["holding_stats"].items():
        assert "median_return_pct" in stats, f"{symbol} missing median_return_pct"


@then("each holding should have a standard deviation of returns")
def then_std_returns(context: dict[str, Any]) -> None:
    for symbol, stats in context["holding_stats"].items():
        assert "return_std_pct" in stats, f"{symbol} missing return_std_pct"
        assert stats["return_std_pct"] >= 0


# ── THEN: Portfolio-level value extremes ──────────


@then("the portfolio should have a peak value and its date")
def then_peak_value(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert "peak_value" in stats
    assert "peak_value_date" in stats
    assert stats["peak_value"] > 0


@then("the portfolio should have a trough value and its date")
def then_trough_value(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert "trough_value" in stats
    assert "trough_value_date" in stats
    assert stats["trough_value"] > 0


@then("the portfolio should have a current value")
def then_current_value(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert "current_value" in stats
    assert stats["current_value"] > 0


@then("the peak value should be greater than or equal to the trough value")
def then_peak_gte_trough(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert stats["peak_value"] >= stats["trough_value"]


# ── THEN: Portfolio-level return distribution ─────


@then("the portfolio should have a best single-period return and its date")
def then_portfolio_best(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert "best_period_return_pct" in stats
    assert "best_period_date" in stats


@then("the portfolio should have a worst single-period return and its date")
def then_portfolio_worst(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert "worst_period_return_pct" in stats
    assert "worst_period_date" in stats
    assert stats["worst_period_return_pct"] <= stats["best_period_return_pct"]


@then("the portfolio should have a median periodic return")
def then_portfolio_median(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert "median_return_pct" in stats


@then("the portfolio should have a mean periodic return")
def then_portfolio_mean(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert "mean_return_pct" in stats


@then("the portfolio should have positive and negative period counts")
def then_pos_neg_counts(context: dict[str, Any]) -> None:
    stats = context["portfolio_stats"]
    assert "positive_periods" in stats
    assert "negative_periods" in stats
    assert stats["positive_periods"] >= 0
    assert stats["negative_periods"] >= 0
    assert stats["positive_periods"] + stats["negative_periods"] > 0


# ── THEN: Statistics in full report ───────────────


@then("the report should contain a statistics section")
def then_report_has_stats(context: dict[str, Any]) -> None:
    assert "statistics" in context["report"]


@then("the statistics section should include per-holding stats")
def then_report_holding_stats(context: dict[str, Any]) -> None:
    stats = context["report"]["statistics"]
    assert "per_holding" in stats
    for symbol in context["portfolio"].symbols:
        assert symbol in stats["per_holding"], f"{symbol} missing from per-holding stats"


@then("the statistics section should include portfolio-level stats")
def then_report_portfolio_stats(context: dict[str, Any]) -> None:
    stats = context["report"]["statistics"]
    assert "portfolio" in stats
    assert "peak_value" in stats["portfolio"]
