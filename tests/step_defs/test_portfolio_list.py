"""Step definitions for the portfolio list and detail feature."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import parsers, scenario, then, when


@scenario("../features/portfolio_list.feature", "Homepage lists all portfolios")
def test_homepage_lists_portfolios() -> None:
    """Homepage lists all portfolios."""


@scenario("../features/portfolio_list.feature", "Portfolio detail page loads")
def test_portfolio_detail() -> None:
    """Portfolio detail page loads."""


@scenario("../features/portfolio_list.feature", "Benchmark detail page loads")
def test_benchmark_detail() -> None:
    """Benchmark detail page loads."""


@scenario("../features/portfolio_list.feature", "Portfolio detail shows holding symbols")
def test_portfolio_detail_symbols() -> None:
    """Portfolio detail shows holding symbols."""


@scenario("../features/portfolio_list.feature", "API returns all portfolios")
def test_api_portfolios() -> None:
    """API returns all portfolios."""


@scenario("../features/portfolio_list.feature", "API returns single portfolio detail")
def test_api_portfolio_detail() -> None:
    """API returns single portfolio detail."""


@scenario("../features/portfolio_list.feature", "Unknown portfolio returns 404")
def test_unknown_portfolio_404() -> None:
    """Unknown portfolio returns 404."""


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


@when("I request the homepage", target_fixture="context")
def when_request_homepage(context: dict[str, Any], app: Any) -> dict[str, Any]:
    """Request the homepage."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/")

    context["response"] = asyncio.run(_get())
    context["page_text"] = context["response"].text
    return context


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


@when("I request the portfolios API", target_fixture="context")
def when_request_portfolios_api(context: dict[str, Any], app: Any) -> dict[str, Any]:
    """Request the portfolios API."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/api/portfolios")

    context["response"] = asyncio.run(_get())
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


# ── THEN steps ────────────────────────────────


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


@then("the JSON should be a list")
def then_json_is_list(context: dict[str, Any]) -> None:
    """Check the JSON response is a list."""
    context["json_data"] = context["response"].json()
    assert isinstance(context["json_data"], list)


@then(parsers.parse("the JSON list should have at least {count:d} items"))
def then_json_list_has_items(context: dict[str, Any], count: int) -> None:
    """Check the JSON list has at least N items."""
    assert len(context["json_data"]) >= count, (
        f"Expected at least {count} items, got {len(context['json_data'])}"
    )
