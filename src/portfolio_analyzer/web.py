"""Lightweight read-only web interface using FastAPI + Jinja2."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from portfolio_analyzer.analyzer import PortfolioAnalyzer
from portfolio_analyzer.models import Holding, Portfolio

TEMPLATES_DIR = Path(__file__).parent / "templates"


# ── Portfolio registry ────────────────────────────────────────────────────────


@dataclass
class PortfolioConfig:
    """Configuration for a single portfolio in the registry."""

    slug: str
    name: str
    holdings: list[Holding]
    benchmark_symbol: str = "ACWI"
    period: str = "max"
    interval: str = "1mo"
    strategy_type: str = "Buy & Hold"
    tags: list[str] = field(default_factory=list)


def _all_portfolios() -> list[PortfolioConfig]:
    """Return the full list of portfolio configurations."""
    return [
        # ── User portfolio ────────────────────────────────
        PortfolioConfig(
            slug="global-multi-asset",
            name="Global Multi-Asset",
            holdings=[
                Holding(symbol="GLD", shares=50, name="SPDR Gold Shares"),
                Holding(symbol="GSG", shares=80, name="iShares S&P GSCI Commodity ETF"),
                Holding(symbol="ACWI", shares=60, name="iShares MSCI ACWI ETF"),
                Holding(symbol="AGG", shares=100, name="iShares Core US Aggregate Bond ETF"),
            ],
            tags=["custom"],
        ),
        # ── Benchmark indices (single-holding portfolios) ─
        PortfolioConfig(
            slug="sp500",
            name="S&P 500",
            holdings=[Holding(symbol="SPY", shares=100, name="SPDR S&P 500 ETF")],
            tags=["benchmark", "us"],
        ),
        PortfolioConfig(
            slug="nasdaq100",
            name="Nasdaq 100",
            holdings=[
                Holding(symbol="QQQ", shares=100, name="Invesco QQQ Trust"),
            ],
            tags=["benchmark", "us"],
        ),
        PortfolioConfig(
            slug="msci-acwi",
            name="MSCI ACWI",
            holdings=[
                Holding(symbol="ACWI", shares=100, name="iShares MSCI ACWI ETF"),
            ],
            tags=["benchmark", "global"],
        ),
        PortfolioConfig(
            slug="ftse-europe",
            name="FTSE Europe",
            holdings=[
                Holding(symbol="VGK", shares=100, name="Vanguard FTSE Europe ETF"),
            ],
            tags=["benchmark", "europe"],
        ),
        PortfolioConfig(
            slug="euro-stoxx-50",
            name="EURO STOXX 50",
            holdings=[
                Holding(symbol="FEZ", shares=100, name="SPDR EURO STOXX 50 ETF"),
            ],
            tags=["benchmark", "europe"],
        ),
        PortfolioConfig(
            slug="sweden",
            name="MSCI Sweden",
            holdings=[
                Holding(symbol="EWD", shares=100, name="iShares MSCI Sweden ETF"),
            ],
            tags=["benchmark", "europe"],
        ),
        PortfolioConfig(
            slug="japan",
            name="MSCI Japan",
            holdings=[
                Holding(symbol="EWJ", shares=100, name="iShares MSCI Japan ETF"),
            ],
            tags=["benchmark", "asia"],
        ),
        PortfolioConfig(
            slug="emerging-markets",
            name="Emerging Markets",
            holdings=[
                Holding(symbol="EEM", shares=100, name="iShares MSCI Emerging Markets ETF"),
            ],
            tags=["benchmark", "emerging"],
        ),
        PortfolioConfig(
            slug="us-bonds",
            name="US Aggregate Bond",
            holdings=[
                Holding(
                    symbol="AGG",
                    shares=100,
                    name="iShares Core US Aggregate Bond ETF",
                ),
            ],
            tags=["benchmark", "bonds"],
        ),
        PortfolioConfig(
            slug="gold",
            name="Gold",
            holdings=[
                Holding(symbol="GLD", shares=100, name="SPDR Gold Shares"),
            ],
            tags=["benchmark", "commodity"],
        ),
        # ── Strategy portfolios ───────────────────────────
        PortfolioConfig(
            slug="equal-weight",
            name="Equal Weight",
            holdings=[
                Holding(symbol="GLD", shares=25, name="SPDR Gold Shares"),
                Holding(symbol="GSG", shares=25, name="iShares S&P GSCI Commodity ETF"),
                Holding(symbol="ACWI", shares=25, name="iShares MSCI ACWI ETF"),
                Holding(symbol="AGG", shares=25, name="iShares Core US Aggregate Bond ETF"),
            ],
            tags=["strategy"],
        ),
        PortfolioConfig(
            slug="heavy-gold",
            name="Heavy Gold",
            holdings=[
                Holding(symbol="GLD", shares=50, name="SPDR Gold Shares"),
                Holding(symbol="GSG", shares=10, name="iShares S&P GSCI Commodity ETF"),
                Holding(symbol="ACWI", shares=20, name="iShares MSCI ACWI ETF"),
                Holding(symbol="AGG", shares=20, name="iShares Core US Aggregate Bond ETF"),
            ],
            tags=["strategy"],
        ),
        PortfolioConfig(
            slug="stocks-and-bonds",
            name="Stocks & Bonds",
            holdings=[
                Holding(symbol="ACWI", shares=60, name="iShares MSCI ACWI ETF"),
                Holding(symbol="AGG", shares=40, name="iShares Core US Aggregate Bond ETF"),
            ],
            tags=["strategy"],
        ),
        PortfolioConfig(
            slug="all-weather",
            name="All Weather",
            holdings=[
                Holding(symbol="GLD", shares=30, name="SPDR Gold Shares"),
                Holding(symbol="GSG", shares=15, name="iShares S&P GSCI Commodity ETF"),
                Holding(symbol="ACWI", shares=30, name="iShares MSCI ACWI ETF"),
                Holding(symbol="AGG", shares=25, name="iShares Core US Aggregate Bond ETF"),
            ],
            tags=["strategy"],
        ),
    ]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_json_safe(obj: Any) -> Any:
    """Recursively convert pandas/numpy types to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]
    if isinstance(obj, pd.Series):
        return {str(k): _make_json_safe(v) for k, v in obj.to_dict().items()}
    if isinstance(obj, pd.Timestamp):
        return str(obj.date())
    if hasattr(obj, "item"):
        return obj.item()  # numpy scalar → Python scalar
    return obj


# Module-level cache to avoid re-fetching on every request
_cache: dict[str, Any] = {}


def _symbol_names() -> dict[str, str]:
    """Build a symbol → display name mapping from all portfolios."""
    names: dict[str, str] = {}
    for cfg in _all_portfolios():
        for h in cfg.holdings:
            names[h.symbol] = h.name if h.name else h.symbol
    return names


def _analyze_portfolio(cfg: PortfolioConfig) -> dict[str, Any]:
    """Run analysis for one portfolio config (cached)."""
    cache_key = f"portfolio:{cfg.slug}"
    if cache_key not in _cache:
        portfolio = Portfolio(holdings=cfg.holdings)
        # For single-holding portfolios, use SPY as benchmark
        # For multi-holding, use the configured benchmark
        bench = cfg.benchmark_symbol
        if len(cfg.holdings) == 1 and cfg.holdings[0].symbol == bench:
            bench = "SPY"

        analyzer = PortfolioAnalyzer(
            portfolio=portfolio,
            benchmark_symbol=bench,
            period=cfg.period,
            interval=cfg.interval,
        )
        result = analyzer.run()
        # Attach portfolio metadata
        result["meta"] = {
            "slug": cfg.slug,
            "name": cfg.name,
            "strategy": cfg.strategy_type,
            "tags": cfg.tags,
        }
        _cache[cache_key] = result
    out: dict[str, Any] = _cache[cache_key]
    return out


def _get_portfolio_list() -> list[dict[str, Any]]:
    """Get summary data for all portfolios (for the list page)."""
    if "portfolio_list" not in _cache:
        summaries: list[dict[str, Any]] = []
        for cfg in _all_portfolios():
            data = _analyze_portfolio(cfg)
            summaries.append(
                {
                    "slug": cfg.slug,
                    "name": cfg.name,
                    "strategy": cfg.strategy_type,
                    "tags": cfg.tags,
                    "num_holdings": data["summary"]["num_holdings"],
                    "total_value": data["summary"]["total_portfolio_value"],
                    "total_return_pct": data["benchmark_comparison"]["portfolio_return_pct"],
                    "volatility_pct": data["risk"]["volatility_pct"],
                    "sharpe_ratio": data["risk"]["sharpe_ratio"],
                    "max_drawdown_pct": data["risk"]["max_drawdown_pct"],
                }
            )
        _cache["portfolio_list"] = summaries
    result: list[dict[str, Any]] = _cache["portfolio_list"]
    return result


def _find_config(slug: str) -> PortfolioConfig | None:
    """Find a portfolio config by slug."""
    for cfg in _all_portfolios():
        if cfg.slug == slug:
            return cfg
    return None


# ── App factory ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="Portfolio Analyzer", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    @application.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        """Render the portfolio list page."""
        portfolios = _get_portfolio_list()
        safe = _make_json_safe(portfolios)
        return templates.TemplateResponse(
            request,
            "index.html",
            {"portfolios": safe},
        )

    @application.get("/portfolio/{slug}", response_class=HTMLResponse)
    async def portfolio_detail(request: Request, slug: str) -> HTMLResponse:
        """Render a single portfolio detail page."""
        cfg = _find_config(slug)
        if cfg is None:
            return HTMLResponse(content="Not found", status_code=404)
        data = _analyze_portfolio(cfg)
        safe = _make_json_safe(data)
        return templates.TemplateResponse(
            request,
            "detail.html",
            {"data": safe, "names": _symbol_names()},
        )

    @application.get("/api/portfolios")
    async def api_portfolios() -> JSONResponse:
        """Return summary list of all portfolios as JSON."""
        portfolios = _get_portfolio_list()
        safe = _make_json_safe(portfolios)
        return JSONResponse(content=safe)

    @application.get("/api/portfolio/{slug}")
    async def api_portfolio_detail(slug: str) -> JSONResponse:
        """Return full analysis for one portfolio as JSON."""
        cfg = _find_config(slug)
        if cfg is None:
            return JSONResponse(content={"error": "Not found"}, status_code=404)
        data = _analyze_portfolio(cfg)
        safe = _make_json_safe(data)
        return JSONResponse(content=safe)

    return application


# Module-level instance for `uvicorn portfolio_analyzer.web:app`
app = create_app()
