"""Step definitions for the web interface feature."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import parsers, scenario, then, when


@scenario("../features/web_interface.feature", "Dashboard page loads successfully")
def test_dashboard_loads() -> None:
    """Dashboard page loads successfully."""


@scenario("../features/web_interface.feature", "Dashboard shows allocation breakdown")
def test_dashboard_allocation() -> None:
    """Dashboard shows allocation breakdown."""


@scenario("../features/web_interface.feature", "Dashboard shows performance metrics")
def test_dashboard_performance() -> None:
    """Dashboard shows performance metrics."""


@scenario("../features/web_interface.feature", "Dashboard shows risk metrics")
def test_dashboard_risk() -> None:
    """Dashboard shows risk metrics."""


@scenario("../features/web_interface.feature", "Dashboard shows statistics section")
def test_dashboard_statistics() -> None:
    """Dashboard shows statistics section."""


@scenario("../features/web_interface.feature", "Comparison page loads successfully")
def test_comparison_loads() -> None:
    """Comparison page loads successfully."""


@scenario("../features/web_interface.feature", "Comparison page shows strategy ranking")
def test_comparison_ranking() -> None:
    """Comparison page shows strategy ranking."""


@scenario("../features/web_interface.feature", "API returns portfolio JSON")
def test_api_portfolio() -> None:
    """API returns portfolio JSON."""


@scenario("../features/web_interface.feature", "API returns comparison JSON")
def test_api_comparison() -> None:
    """API returns comparison JSON."""


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


@when("I request the dashboard page", target_fixture="context")
def when_request_dashboard(context: dict[str, Any], app: Any) -> dict[str, Any]:
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/")

    context["response"] = asyncio.run(_get())
    context["page_text"] = context["response"].text
    return context


@when("I request the comparison page", target_fixture="context")
def when_request_comparison(context: dict[str, Any], app: Any) -> dict[str, Any]:
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/comparison")

    context["response"] = asyncio.run(_get())
    context["page_text"] = context["response"].text
    return context


@when("I request the portfolio API endpoint", target_fixture="context")
def when_request_api_portfolio(context: dict[str, Any], app: Any) -> dict[str, Any]:
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/api/portfolio")

    context["response"] = asyncio.run(_get())
    return context


@when("I request the comparison API endpoint", target_fixture="context")
def when_request_api_comparison(context: dict[str, Any], app: Any) -> dict[str, Any]:
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/api/comparison")

    context["response"] = asyncio.run(_get())
    return context


# ── THEN steps ────────────────────────────────


@then(parsers.parse("the response status should be {code:d}"))
def then_status_code(context: dict[str, Any], code: int) -> None:
    assert context["response"].status_code == code


@then(parsers.parse('the page should contain "{text}"'))
def then_page_contains(context: dict[str, Any], text: str) -> None:
    assert text in context["page_text"], f"Expected '{text}' in page but not found"


@then("the page should list each holding symbol")
def then_page_lists_symbols(context: dict[str, Any]) -> None:
    for symbol in ["GLD", "GSG", "ACWI", "AGG"]:
        assert symbol in context["page_text"]


@then("the response should be valid JSON")
def then_valid_json(context: dict[str, Any]) -> None:
    context["json_data"] = context["response"].json()
    assert isinstance(context["json_data"], dict)


@then(parsers.parse('the JSON should contain key "{key}"'))
def then_json_has_key(context: dict[str, Any], key: str) -> None:
    assert key in context["json_data"], f"Expected key '{key}' in JSON response"
