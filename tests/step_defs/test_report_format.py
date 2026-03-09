"""Step definitions for report formatting feature."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when


@scenario(
    "../features/report_format.feature",
    "Format a report from analysis results",
)
def test_format_report() -> None:
    """Format a report from analysis results."""


@pytest.fixture()
def context() -> dict[str, Any]:
    """Shared mutable state across steps."""
    return {}


@given("a completed analysis report", target_fixture="context")
def given_completed_report(context: dict[str, Any]) -> dict[str, Any]:
    """Provide a canned analysis report dict."""
    context["report"] = {
        "summary": {
            "num_holdings": 4,
            "total_portfolio_value": 25000.0,
            "benchmark": "URTH",
            "period": "1y",
        },
        "allocation": {
            "AAPL": {"market_value": 10000.0, "weight_pct": 40.0},
            "MSFT": {"market_value": 8000.0, "weight_pct": 32.0},
            "JNJ": {"market_value": 4000.0, "weight_pct": 16.0},
            "BND": {"market_value": 3000.0, "weight_pct": 12.0},
        },
        "performance": {
            "AAPL": {"total_return_pct": 15.0, "annualized_return_pct": 15.0},
            "MSFT": {"total_return_pct": 12.0, "annualized_return_pct": 12.0},
            "JNJ": {"total_return_pct": -3.0, "annualized_return_pct": -3.0},
            "BND": {"total_return_pct": 2.0, "annualized_return_pct": 2.0},
        },
        "risk": {
            "volatility_pct": 14.5,
            "sharpe_ratio": 0.85,
            "max_drawdown_pct": -8.2,
        },
        "benchmark_comparison": {
            "portfolio_return_pct": 10.5,
            "benchmark_return_pct": 9.0,
            "excess_return_pct": 1.5,
        },
    }
    return context


@when("I format the report as text")
def when_format_report(context: dict[str, Any]) -> None:
    """Format the report using the report module."""
    from portfolio_analyzer.report import format_report

    context["text"] = format_report(context["report"])


@then(parsers.parse('the text should contain "{expected}"'))
def then_text_contains(context: dict[str, Any], expected: str) -> None:
    """The formatted text must contain the expected substring."""
    assert expected in context["text"], f"Expected '{expected}' in report text"
