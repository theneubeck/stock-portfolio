"""Step definitions for multi-portfolio comparison feature."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when


@scenario(
    "../features/portfolio_comparison.feature",
    "Run all strategies and collect results",
)
def test_run_all_strategies() -> None:
    """Run all strategies and collect results."""


@scenario(
    "../features/portfolio_comparison.feature",
    "Rank strategies by total return",
)
def test_rank_by_return() -> None:
    """Rank strategies by total return."""


@scenario(
    "../features/portfolio_comparison.feature",
    "Compare risk across strategies",
)
def test_compare_risk() -> None:
    """Compare risk across strategies."""


@scenario(
    "../features/portfolio_comparison.feature",
    "Compare strategies against the benchmark",
)
def test_compare_vs_benchmark() -> None:
    """Compare strategies against the benchmark."""


@scenario(
    "../features/portfolio_comparison.feature",
    "Generate a comparison report",
)
def test_comparison_report() -> None:
    """Generate a comparison report."""


# ── Shared context ────────────────────────────────


@pytest.fixture()
def context() -> dict[str, Any]:
    """Shared mutable state across steps."""
    return {}


# ── GIVEN steps ───────────────────────────────────


@given(
    parsers.parse("the following portfolio strategies:"),
    target_fixture="context",
)
def given_strategies(context: dict[str, Any], datatable: list[list[str]]) -> dict[str, Any]:
    """Parse strategy definitions from the data table."""
    headers = datatable[0]
    rows = datatable[1:]
    # headers: name, GLD, GSG, ACWI, AGG
    # symbols are everything except the first column
    symbols = headers[1:]

    strategies: list[dict[str, Any]] = []
    for row in rows:
        parsed = dict(zip(headers, row, strict=True))
        name = parsed["name"]
        weights: dict[str, float] = {sym: float(parsed[sym]) for sym in symbols}
        strategies.append({"name": name, "weights": weights})

    context["strategies"] = strategies
    context["symbols"] = symbols
    return context


@given(parsers.parse("the monthly investment is {amount:d} USD for all strategies"))
def given_monthly_investment(context: dict[str, Any], amount: int) -> None:
    """Set the monthly DCA investment amount for all strategies."""
    context["monthly_investment"] = amount


@given(parsers.parse("rebalancing occurs every {months:d} months for all strategies"))
def given_rebalance_frequency(context: dict[str, Any], months: int) -> None:
    """Set rebalancing frequency for all strategies."""
    context["rebalance_every_months"] = months


@given(parsers.parse('the benchmark is "{benchmark}"'))
def given_benchmark(context: dict[str, Any], benchmark: str) -> None:
    """Set the benchmark symbol."""
    context["benchmark"] = benchmark


@given(parsers.parse("the comparison period is {period}"))
def given_comparison_period(context: dict[str, Any], period: str) -> None:
    """Set the comparison look-back period."""
    period_map: dict[str, str] = {
        "1 year": "1y",
        "5 years": "5y",
    }
    context["period"] = period_map.get(period, period)


@given(parsers.parse("the comparison interval is {interval}"))
def given_comparison_interval(context: dict[str, Any], interval: str) -> None:
    """Set the data interval."""
    interval_map: dict[str, str] = {
        "daily": "1d",
        "weekly": "1wk",
        "monthly": "1mo",
    }
    context["interval"] = interval_map.get(interval, interval)


# ── WHEN steps ────────────────────────────────────


@when("I run the portfolio comparison")
def when_run_comparison(context: dict[str, Any]) -> None:
    """Run the multi-portfolio comparison."""
    from portfolio_analyzer.comparison import PortfolioComparator

    comparator = PortfolioComparator(
        strategies=context["strategies"],
        monthly_investment=context["monthly_investment"],
        rebalance_every_months=context["rebalance_every_months"],
        benchmark_symbol=context["benchmark"],
        period=context["period"],
        interval=context.get("interval", "1mo"),
    )
    context["comparison_result"] = comparator.run()
    context["comparator"] = comparator


# ── THEN: Run all strategies ─────────────────────


@then(parsers.parse("I should have results for {count:d} strategies"))
def then_strategy_count(context: dict[str, Any], count: int) -> None:
    result = context["comparison_result"]
    assert len(result["strategies"]) == count


@then("each strategy should have a final value")
def then_each_final_value(context: dict[str, Any]) -> None:
    for strategy in context["comparison_result"]["strategies"]:
        assert "final_value" in strategy
        assert strategy["final_value"] > 0


@then("each strategy should have a total return")
def then_each_total_return(context: dict[str, Any]) -> None:
    for strategy in context["comparison_result"]["strategies"]:
        assert "total_return_pct" in strategy


# ── THEN: Rank strategies by total return ─────────


@then("I should see strategies ranked by total return")
def then_ranked(context: dict[str, Any]) -> None:
    result = context["comparison_result"]
    assert "ranking" in result
    assert len(result["ranking"]) == len(result["strategies"])


@then("the best performing strategy should be listed first")
def then_best_first(context: dict[str, Any]) -> None:
    ranking = context["comparison_result"]["ranking"]
    returns = [r["total_return_pct"] for r in ranking]
    assert returns[0] == max(returns)


@then("the worst performing strategy should be listed last")
def then_worst_last(context: dict[str, Any]) -> None:
    ranking = context["comparison_result"]["ranking"]
    returns = [r["total_return_pct"] for r in ranking]
    assert returns[-1] == min(returns)


# ── THEN: Compare risk across strategies ──────────


@then("each strategy should have a volatility measure")
def then_each_volatility(context: dict[str, Any]) -> None:
    for strategy in context["comparison_result"]["strategies"]:
        assert "volatility_pct" in strategy


@then("each strategy should have a max drawdown")
def then_each_drawdown(context: dict[str, Any]) -> None:
    for strategy in context["comparison_result"]["strategies"]:
        assert "max_drawdown_pct" in strategy
        assert strategy["max_drawdown_pct"] <= 0


@then("each strategy should have a Sharpe ratio")
def then_each_sharpe(context: dict[str, Any]) -> None:
    for strategy in context["comparison_result"]["strategies"]:
        assert "sharpe_ratio" in strategy


# ── THEN: Compare vs benchmark ────────────────────


@then("each strategy should show excess return vs the benchmark")
def then_each_excess(context: dict[str, Any]) -> None:
    for strategy in context["comparison_result"]["strategies"]:
        assert "excess_return_pct" in strategy


@then("I should see which strategies beat the benchmark")
def then_beat_benchmark(context: dict[str, Any]) -> None:
    result = context["comparison_result"]
    assert "beat_benchmark" in result
    # It's a list of strategy names (could be empty)
    assert isinstance(result["beat_benchmark"], list)


@then("I should see which strategies underperformed the benchmark")
def then_underperformed(context: dict[str, Any]) -> None:
    result = context["comparison_result"]
    assert "underperformed_benchmark" in result
    assert isinstance(result["underperformed_benchmark"], list)
    # beat + underperformed should cover all strategies
    total = len(result["beat_benchmark"]) + len(result["underperformed_benchmark"])
    assert total == len(result["strategies"])


# ── THEN: Generate comparison report ──────────────


@then("the comparison report should list all strategy names")
def then_report_names(context: dict[str, Any]) -> None:
    from portfolio_analyzer.report import format_comparison_report

    text = format_comparison_report(context["comparison_result"])
    for strategy in context["comparison_result"]["strategies"]:
        assert strategy["name"] in text


@then("the comparison report should show a side-by-side summary table")
def then_report_table(context: dict[str, Any]) -> None:
    from portfolio_analyzer.report import format_comparison_report

    text = format_comparison_report(context["comparison_result"])
    # Table headers should be present
    assert "Total Return" in text
    assert "Volatility" in text
    assert "Sharpe" in text


@then("the comparison report should identify the best and worst strategies")
def then_report_best_worst(context: dict[str, Any]) -> None:
    from portfolio_analyzer.report import format_comparison_report

    text = format_comparison_report(context["comparison_result"])
    assert "Best" in text or "BEST" in text or "best" in text
    assert "Worst" in text or "WORST" in text or "worst" in text
