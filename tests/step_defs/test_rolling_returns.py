"""Step definitions for the rolling N-year return analysis feature."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenario, then, when


@scenario(
    "../features/rolling_returns.feature", "Calculate rolling 5-year returns from a price series"
)
def test_rolling_returns_series() -> None:
    """Calculate rolling 5-year returns from a price series."""


@scenario(
    "../features/rolling_returns.feature",
    "Rolling return statistics include mean and Sharpe",
)
def test_rolling_return_statistics() -> None:
    """Rolling return statistics include mean and Sharpe."""


@scenario("../features/rolling_returns.feature", "Web page shows rolling returns tab")
def test_rolling_returns_web_page() -> None:
    """Web page shows rolling returns tab."""


@scenario("../features/rolling_returns.feature", "Rolling returns API returns JSON data")
def test_rolling_returns_api() -> None:
    """Rolling returns API returns JSON data."""


# ── Fixtures ──────────────────────────────────


@pytest.fixture()
def context() -> dict[str, Any]:
    """Shared mutable state across steps."""
    return {}


@pytest.fixture()
def app() -> Any:
    """Create the FastAPI app."""
    from portfolio_analyzer.web import create_app

    return create_app()


# ── GIVEN steps ───────────────────────────────


@given(
    "a monthly price series rising steadily over 10 years",
    target_fixture="context",
)
def given_steady_price_series(context: dict[str, Any]) -> dict[str, Any]:
    """Create a synthetic monthly price series: 120 months, ~8% annual growth."""
    months = 120
    monthly_rate = 1.08 ** (1.0 / 12.0)
    dates = pd.date_range("2010-01-01", periods=months, freq="MS")
    prices = pd.Series(
        100.0 * (monthly_rate ** np.arange(months)),
        index=dates,
        name="price",
    )
    context["prices"] = prices
    return context


# ── WHEN steps ────────────────────────────────


@when("I calculate rolling 5-year returns", target_fixture="context")
def when_calculate_rolling_returns(context: dict[str, Any]) -> dict[str, Any]:
    """Calculate rolling 5-year returns."""
    from portfolio_analyzer.rolling import rolling_returns

    context["rolling"] = rolling_returns(context["prices"], horizon_years=5, interval="1mo")
    return context


@when("I calculate rolling 5-year return statistics", target_fixture="context")
def when_calculate_rolling_stats(context: dict[str, Any]) -> dict[str, Any]:
    """Calculate rolling 5-year return statistics."""
    from portfolio_analyzer.rolling import rolling_return_statistics, rolling_returns

    returns = rolling_returns(context["prices"], horizon_years=5, interval="1mo")
    context["stats"] = rolling_return_statistics(returns)
    return context


@when(
    parsers.parse('I request the rolling returns page for "{slug}" with horizon {horizon:d}'),
    target_fixture="context",
)
def when_request_rolling_page(
    context: dict[str, Any], app: Any, slug: str, horizon: int
) -> dict[str, Any]:
    """Request a rolling returns page."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(f"/portfolio/{slug}/rolling?horizon={horizon}")

    context["response"] = asyncio.run(_get())
    context["page_text"] = context["response"].text
    return context


@when(
    parsers.parse('I request the rolling returns API for "{slug}" with horizon {horizon:d}'),
    target_fixture="context",
)
def when_request_rolling_api(
    context: dict[str, Any], app: Any, slug: str, horizon: int
) -> dict[str, Any]:
    """Request the rolling returns JSON API."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(f"/api/portfolio/{slug}/rolling?horizon={horizon}")

    context["response"] = asyncio.run(_get())
    return context


# ── THEN steps ────────────────────────────────


@then("I should get a series of 5-year return values")
def then_get_series(context: dict[str, Any]) -> None:
    """Check we got a pandas Series of return values."""
    assert isinstance(context["rolling"], pd.Series)
    assert len(context["rolling"]) > 0


@then("the number of rolling returns should equal the number of prices minus the 5-year offset")
def then_correct_length(context: dict[str, Any]) -> None:
    """Check the series length is prices - offset."""
    prices = context["prices"]
    rolling = context["rolling"]
    offset = 5 * 12  # 5 years * 12 months
    expected = len(prices) - offset
    assert len(rolling) == expected


@then(parsers.parse('the statistics should include "{key}"'))
def then_stats_include_key(context: dict[str, Any], key: str) -> None:
    """Check the statistics dict contains the given key."""
    assert key in context["stats"], f"Expected '{key}' in statistics"


@then(parsers.parse("the response status should be {code:d}"))
def then_status_code(context: dict[str, Any], code: int) -> None:
    """Check HTTP status code."""
    assert context["response"].status_code == code


@then(parsers.parse('the page should contain "{text}"'))
def then_page_contains(context: dict[str, Any], text: str) -> None:
    """Check the page contains the given text."""
    assert text in context["page_text"], f"Expected '{text}' in page but not found"


@then("the response should be valid JSON")
def then_valid_json(context: dict[str, Any]) -> None:
    """Check the response is valid JSON."""
    context["json_data"] = context["response"].json()


@then(parsers.parse('the JSON should contain key "{key}"'))
def then_json_has_key(context: dict[str, Any], key: str) -> None:
    """Check the JSON response contains the given key."""
    assert key in context["json_data"], f"Expected key '{key}' in JSON response"
