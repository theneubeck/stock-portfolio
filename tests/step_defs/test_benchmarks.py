"""Step definitions for the benchmark indices feature."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import parsers, scenario, then, when


@scenario("../features/benchmarks.feature", "Benchmarks page loads successfully")
def test_benchmarks_loads() -> None:
    """Benchmarks page loads successfully."""


@scenario("../features/benchmarks.feature", "Benchmarks page shows major index names")
def test_benchmarks_indices() -> None:
    """Benchmarks page shows major index names."""


@scenario("../features/benchmarks.feature", "Benchmarks page shows performance data")
def test_benchmarks_performance() -> None:
    """Benchmarks page shows performance data."""


@scenario("../features/benchmarks.feature", "Benchmarks API returns JSON")
def test_benchmarks_api() -> None:
    """Benchmarks API returns JSON."""


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


@when("I request the benchmarks page", target_fixture="context")
def when_request_benchmarks(context: dict[str, Any], app: Any) -> dict[str, Any]:
    """Request the benchmarks page."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/benchmarks")

    context["response"] = asyncio.run(_get())
    context["page_text"] = context["response"].text
    return context


@when("I request the benchmarks API endpoint", target_fixture="context")
def when_request_benchmarks_api(context: dict[str, Any], app: Any) -> dict[str, Any]:
    """Request the benchmarks API endpoint."""
    import asyncio

    async def _get() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/api/benchmarks")

    context["response"] = asyncio.run(_get())
    return context


# ── THEN steps (reuse from web_interface where possible) ──


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
    assert isinstance(context["json_data"], dict)


@then(parsers.parse('the JSON should contain key "{key}"'))
def then_json_has_key(context: dict[str, Any], key: str) -> None:
    """Check the JSON response contains the given key."""
    assert key in context["json_data"], f"Expected key '{key}' in JSON response"
