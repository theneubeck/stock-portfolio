"""Step definitions for sortable table columns feature."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import parsers, scenario, then, when


@scenario("../features/sortable_tables.feature", "Homepage tables have sortable column headers")
def test_homepage_sortable() -> None:
    """Homepage tables have sortable column headers."""


@scenario("../features/sortable_tables.feature", "Detail page tables have sortable column headers")
def test_detail_sortable() -> None:
    """Detail page tables have sortable column headers."""


@scenario("../features/sortable_tables.feature", "Rolling page table has sortable column headers")
def test_rolling_sortable() -> None:
    """Rolling page table has sortable column headers."""


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


@when(
    parsers.parse('I request the rolling returns page for "{slug}" with horizon {horizon:d}'),
    target_fixture="context",
)
def when_request_rolling(
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


# ── THEN steps ────────────────────────────────


@then(parsers.parse("the response status should be {code:d}"))
def then_status_code(context: dict[str, Any], code: int) -> None:
    """Check HTTP status code."""
    assert context["response"].status_code == code


@then(parsers.parse('the page should contain "{text}"'))
def then_page_contains(context: dict[str, Any], text: str) -> None:
    """Check the page contains the given text."""
    assert text in context["page_text"], f"Expected '{text}' in page but not found"
