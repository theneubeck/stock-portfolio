"""Step definitions for the portfolio detail web interface feature."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import parsers, scenario, then, when


@scenario("../features/web_interface.feature", "Detail page loads for multi-holding portfolio")
def test_detail_loads() -> None:
    """Detail page loads for multi-holding portfolio."""


@scenario("../features/web_interface.feature", "Detail page shows allocation breakdown")
def test_detail_allocation() -> None:
    """Detail page shows allocation breakdown."""


@scenario("../features/web_interface.feature", "Detail page shows performance metrics")
def test_detail_performance() -> None:
    """Detail page shows performance metrics."""


@scenario("../features/web_interface.feature", "Detail page shows risk metrics")
def test_detail_risk() -> None:
    """Detail page shows risk metrics."""


@scenario("../features/web_interface.feature", "Detail page shows statistics section")
def test_detail_statistics() -> None:
    """Detail page shows statistics section."""


@scenario("../features/web_interface.feature", "Single-holding portfolio loads")
def test_single_holding_detail() -> None:
    """Single-holding portfolio loads."""


@scenario("../features/web_interface.feature", "API returns portfolio detail JSON")
def test_api_portfolio_detail() -> None:
    """API returns portfolio detail JSON."""


@scenario("../features/web_interface.feature", "API returns all portfolios list")
def test_api_portfolios_list() -> None:
    """API returns all portfolios list."""


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


# ── WHEN steps ────────────────────────────────


@when(
    parsers.parse('I request the detail page for "{slug}"'),
    target_fixture="context",
)
def when_request_detail(context: dict[str, Any], app: Any, slug: str) -> dict[str, Any]:
    """Request a portfolio detail page."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(f"/portfolio/{slug}")

    context["response"] = asyncio.run(_get())
    context["page_text"] = context["response"].text
    return context


@when(
    parsers.parse('I request the portfolio API for "{slug}"'),
    target_fixture="context",
)
def when_request_portfolio_api(context: dict[str, Any], app: Any, slug: str) -> dict[str, Any]:
    """Request a single portfolio API endpoint."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(f"/api/portfolio/{slug}")

    context["response"] = asyncio.run(_get())
    return context


@when("I request the portfolios API", target_fixture="context")
def when_request_portfolios_api(context: dict[str, Any], app: Any) -> dict[str, Any]:
    """Request the portfolios list API."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/api/portfolios")

    context["response"] = asyncio.run(_get())
    return context


# ── THEN steps ────────────────────────────────


@then(parsers.parse("the response status should be {code:d}"))
def then_status_code(context: dict[str, Any], code: int) -> None:
    """Check HTTP status code."""
    assert context["response"].status_code == code


@then(parsers.parse('the page should contain "{text}"'))
def then_page_contains(context: dict[str, Any], text: str) -> None:
    """Check the page contains the given text."""
    assert text in context["page_text"], f"Expected '{text}' in page but not found"


@then("the page should list each holding symbol")
def then_page_lists_symbols(context: dict[str, Any]) -> None:
    """Check the page lists all holding symbols from Global Multi-Asset."""
    for symbol in ["GLD", "GSG", "ACWI", "AGG"]:
        assert symbol in context["page_text"]


@then("the response should be valid JSON")
def then_valid_json(context: dict[str, Any]) -> None:
    """Check the response is valid JSON."""
    context["json_data"] = context["response"].json()


@then(parsers.parse('the JSON should contain key "{key}"'))
def then_json_has_key(context: dict[str, Any], key: str) -> None:
    """Check the JSON response contains the given key."""
    assert key in context["json_data"], f"Expected key '{key}' in JSON response"
