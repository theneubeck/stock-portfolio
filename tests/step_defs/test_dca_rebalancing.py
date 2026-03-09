"""Step definitions for DCA with periodic rebalancing feature."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when


@scenario(
    "../features/dca_rebalancing.feature",
    "Simulate monthly DCA investments",
)
def test_dca_simulation() -> None:
    """Simulate monthly DCA investments."""


@scenario(
    "../features/dca_rebalancing.feature",
    "Rebalancing restores target weights",
)
def test_rebalancing() -> None:
    """Rebalancing restores target weights."""


@scenario(
    "../features/dca_rebalancing.feature",
    "Track portfolio value over time",
)
def test_portfolio_value_timeseries() -> None:
    """Track portfolio value over time."""


@scenario(
    "../features/dca_rebalancing.feature",
    "Calculate DCA investment returns",
)
def test_dca_returns() -> None:
    """Calculate DCA investment returns."""


@scenario(
    "../features/dca_rebalancing.feature",
    "Compare DCA to lump-sum and benchmark",
)
def test_dca_vs_lump_sum() -> None:
    """Compare DCA to lump-sum and benchmark."""


@scenario(
    "../features/dca_rebalancing.feature",
    "Generate a full DCA report",
)
def test_dca_report() -> None:
    """Generate a full DCA report."""


# ── Shared context ────────────────────────────────


@pytest.fixture()
def context() -> dict[str, Any]:
    """Shared mutable state across steps."""
    return {}


# ── GIVEN steps ───────────────────────────────────


@given(
    parsers.parse("a DCA portfolio with the following holdings:"),
    target_fixture="context",
)
def given_dca_portfolio(context: dict[str, Any], datatable: list[list[str]]) -> dict[str, Any]:
    """Build target allocation from the Gherkin data table."""
    from portfolio_analyzer.models import TargetAllocation

    headers = datatable[0]
    rows = datatable[1:]
    targets: list[TargetAllocation] = []
    for row in rows:
        parsed = dict(zip(headers, row, strict=True))
        targets.append(
            TargetAllocation(
                symbol=parsed["symbol"],
                name=parsed["name"],
                target_weight_pct=float(parsed["target_weight"]),
            )
        )
    context["targets"] = targets
    return context


@given(parsers.parse("the monthly investment is {amount:d} USD"))
def given_monthly_investment(context: dict[str, Any], amount: int) -> None:
    """Set the monthly DCA investment amount."""
    context["monthly_investment"] = amount


@given(parsers.parse("rebalancing occurs every {months:d} months"))
def given_rebalance_frequency(context: dict[str, Any], months: int) -> None:
    """Set rebalancing frequency in months."""
    context["rebalance_every_months"] = months


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


@when("I run the DCA simulation")
def when_run_dca(context: dict[str, Any]) -> None:
    """Run the full DCA simulation."""
    from portfolio_analyzer.dca import DCASimulator

    simulator = DCASimulator(
        targets=context["targets"],
        monthly_investment=context["monthly_investment"],
        rebalance_every_months=context["rebalance_every_months"],
        benchmark_symbol=context["benchmark"],
        period=context["period"],
        interval=context.get("interval", "1mo"),
    )
    context["result"] = simulator.run()
    context["simulator"] = simulator


# ── THEN steps: Simulate monthly DCA investments ──


@then("the total amount invested should be positive")
def then_total_invested_positive(context: dict[str, Any]) -> None:
    result = context["result"]
    assert result["summary"]["total_invested"] > 0


@then("the final portfolio value should be positive")
def then_final_value_positive(context: dict[str, Any]) -> None:
    result = context["result"]
    assert result["summary"]["final_value"] > 0


@then("the number of investment periods should match the price history length")
def then_periods_match(context: dict[str, Any]) -> None:
    result = context["result"]
    # Number of investments should be close to the number of price data points
    # (minus 1 because we can't invest on the very first data point before we have a price)
    n_investments = result["summary"]["num_investments"]
    n_periods = result["summary"]["num_periods"]
    assert n_investments > 0
    assert n_investments == n_periods


# ── THEN steps: Rebalancing restores target weights ──


@then("rebalancing should have occurred at least once")
def then_rebalanced_at_least_once(context: dict[str, Any]) -> None:
    result = context["result"]
    assert len(result["rebalancing_log"]) >= 1


@then("after each rebalance the weights should be within 1 percent of targets")
def then_weights_near_targets(context: dict[str, Any]) -> None:
    result = context["result"]
    for entry in result["rebalancing_log"]:
        for symbol, actual_weight in entry["weights_after"].items():
            target_weight = entry["target_weights"][symbol]
            assert abs(actual_weight - target_weight) <= 1.0, (
                f"After rebalance on {entry['date']}: {symbol} weight "
                f"{actual_weight:.2f}% vs target {target_weight:.2f}%"
            )


# ── THEN steps: Track portfolio value over time ──


@then("I should have a time series of portfolio values")
def then_timeseries_exists(context: dict[str, Any]) -> None:
    result = context["result"]
    assert "value_history" in result
    assert len(result["value_history"]) > 0


@then("the time series should start near the first monthly investment")
def then_timeseries_start(context: dict[str, Any]) -> None:
    result = context["result"]
    first_value = result["value_history"].iloc[0]
    monthly = context["monthly_investment"]
    # First period: invested one month's worth, value should be close
    assert abs(first_value - monthly) < monthly * 0.20  # within 20% (market moved)


@then("the time series should end at the final portfolio value")
def then_timeseries_end(context: dict[str, Any]) -> None:
    result = context["result"]
    last_value = result["value_history"].iloc[-1]
    final = result["summary"]["final_value"]
    assert abs(last_value - final) < 1.0  # within $1 rounding


# ── THEN steps: Calculate DCA investment returns ──


@then("I should see the total amount invested")
def then_total_invested(context: dict[str, Any]) -> None:
    result = context["result"]
    assert "total_invested" in result["summary"]
    expected = context["monthly_investment"] * result["summary"]["num_investments"]
    assert abs(result["summary"]["total_invested"] - expected) < 0.01


@then("I should see the final portfolio value")
def then_final_value(context: dict[str, Any]) -> None:
    result = context["result"]
    assert "final_value" in result["summary"]
    assert isinstance(result["summary"]["final_value"], float)


@then("I should see the total return on invested capital")
def then_total_return_on_capital(context: dict[str, Any]) -> None:
    result = context["result"]
    assert "total_return_pct" in result["summary"]
    # Verify it's calculated correctly
    invested = result["summary"]["total_invested"]
    final = result["summary"]["final_value"]
    expected = ((final - invested) / invested) * 100.0
    assert abs(result["summary"]["total_return_pct"] - expected) < 0.01


@then("I should see the annualized return on invested capital")
def then_annualized_return_on_capital(context: dict[str, Any]) -> None:
    result = context["result"]
    assert "annualized_return_pct" in result["summary"]
    assert isinstance(result["summary"]["annualized_return_pct"], float)


# ── THEN steps: Compare DCA to lump-sum and benchmark ──


@then("I should see the DCA final value")
def then_dca_final(context: dict[str, Any]) -> None:
    result = context["result"]
    assert "dca_final_value" in result["comparison"]
    assert result["comparison"]["dca_final_value"] > 0


@then("I should see what a lump-sum investment would have returned")
def then_lump_sum(context: dict[str, Any]) -> None:
    result = context["result"]
    assert "lump_sum_final_value" in result["comparison"]
    assert "lump_sum_return_pct" in result["comparison"]


@then("I should see what the benchmark returned over the same period")
def then_benchmark_return(context: dict[str, Any]) -> None:
    result = context["result"]
    assert "benchmark_return_pct" in result["comparison"]


# ── THEN steps: Generate a full DCA report ──


@then("the DCA report should contain a summary section")
def then_report_summary(context: dict[str, Any]) -> None:
    assert "summary" in context["result"]


@then("the DCA report should contain an investment history section")
def then_report_investment_history(context: dict[str, Any]) -> None:
    assert "value_history" in context["result"]


@then("the DCA report should contain a rebalancing log section")
def then_report_rebalancing_log(context: dict[str, Any]) -> None:
    assert "rebalancing_log" in context["result"]


@then("the DCA report should contain a comparison section")
def then_report_comparison(context: dict[str, Any]) -> None:
    assert "comparison" in context["result"]
