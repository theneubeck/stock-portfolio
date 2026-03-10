"""Lightweight read-only web interface using FastAPI + Jinja2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from portfolio_analyzer.analyzer import PortfolioAnalyzer
from portfolio_analyzer.comparison import PortfolioComparator
from portfolio_analyzer.data import fetch_prices
from portfolio_analyzer.metrics import (
    annualized_return,
    periods_per_year_for,
    total_return,
)
from portfolio_analyzer.models import Holding, Portfolio

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _default_portfolio() -> Portfolio:
    """Build the default portfolio for the dashboard."""
    return Portfolio(
        holdings=[
            Holding(symbol="GLD", shares=50, name="SPDR Gold Shares"),
            Holding(
                symbol="GSG",
                shares=80,
                name="iShares S&P GSCI Commodity ETF",
            ),
            Holding(
                symbol="ACWI",
                shares=60,
                name="iShares MSCI ACWI ETF",
            ),
            Holding(
                symbol="AGG",
                shares=100,
                name="iShares Core US Aggregate Bond ETF",
            ),
        ]
    )


def _default_strategies() -> list[dict[str, Any]]:
    """Default comparison strategies."""
    return [
        {
            "name": "Equal Weight",
            "weights": {"GLD": 25, "GSG": 25, "ACWI": 25, "AGG": 25},
        },
        {
            "name": "Heavy Gold",
            "weights": {"GLD": 50, "GSG": 10, "ACWI": 20, "AGG": 20},
        },
        {
            "name": "Stocks & Bonds",
            "weights": {"GLD": 0, "GSG": 0, "ACWI": 60, "AGG": 40},
        },
        {
            "name": "All Weather",
            "weights": {"GLD": 30, "GSG": 15, "ACWI": 30, "AGG": 25},
        },
    ]


@dataclass
class BenchmarkIndex:
    """A benchmark index to track buy-and-hold performance."""

    symbol: str
    name: str
    region: str


BENCHMARK_INDICES: list[BenchmarkIndex] = [
    BenchmarkIndex(symbol="SPY", name="S&P 500", region="United States"),
    BenchmarkIndex(symbol="QQQ", name="Nasdaq 100", region="United States"),
    BenchmarkIndex(symbol="ACWI", name="MSCI ACWI", region="Global"),
    BenchmarkIndex(symbol="VGK", name="FTSE Europe", region="Europe"),
    BenchmarkIndex(symbol="FEZ", name="EURO STOXX 50", region="Eurozone"),
    BenchmarkIndex(symbol="EWD", name="MSCI Sweden", region="Sweden"),
    BenchmarkIndex(symbol="EWJ", name="MSCI Japan", region="Japan"),
    BenchmarkIndex(symbol="EEM", name="Emerging Markets", region="Emerging"),
    BenchmarkIndex(symbol="AGG", name="US Aggregate Bond", region="United States"),
    BenchmarkIndex(symbol="GLD", name="Gold", region="Global"),
]

_BENCHMARK_PERIOD = "max"
_BENCHMARK_INTERVAL = "1mo"


def _get_benchmark_data() -> dict[str, Any]:
    """Get or compute benchmark index data (cached)."""
    if "benchmarks" not in _cache:
        symbols = [b.symbol for b in BENCHMARK_INDICES]
        price_data = fetch_prices(symbols, period=_BENCHMARK_PERIOD, interval=_BENCHMARK_INTERVAL)
        ppy = periods_per_year_for(_BENCHMARK_INTERVAL)

        benchmarks: list[dict[str, Any]] = []
        for bench in BENCHMARK_INDICES:
            prices = price_data[bench.symbol]
            periodic_returns = prices.pct_change().dropna()

            vol = float(periodic_returns.std() * np.sqrt(ppy)) * 100.0

            ann_ret_decimal = float(periodic_returns.mean() * ppy)
            sharpe = 0.0
            if periodic_returns.std() > 0:
                sharpe = float((ann_ret_decimal - 0.04) / (periodic_returns.std() * np.sqrt(ppy)))

            cum = (1 + periodic_returns).cumprod()
            running_max = cum.cummax()
            drawdown = (cum - running_max) / running_max
            max_dd = float(drawdown.min()) * 100.0

            benchmarks.append(
                {
                    "symbol": bench.symbol,
                    "name": bench.name,
                    "region": bench.region,
                    "total_return_pct": total_return(prices),
                    "annualized_return_pct": annualized_return(prices, ppy),
                    "volatility_pct": vol,
                    "sharpe_ratio": sharpe,
                    "max_drawdown_pct": max_dd,
                    "num_periods": len(prices),
                }
            )

        _cache["benchmarks"] = {
            "benchmarks": benchmarks,
            "period": _BENCHMARK_PERIOD,
            "interval": _BENCHMARK_INTERVAL,
        }
    result: dict[str, Any] = _cache["benchmarks"]
    return result


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
    """Build a symbol → display name mapping from all known symbols."""
    names: dict[str, str] = {}
    for h in _default_portfolio().holdings:
        names[h.symbol] = h.name if h.name else h.symbol
    # Also map strategy symbols from comparison
    for strategy in _default_strategies():
        for sym in strategy["weights"]:
            if sym not in names:
                names[sym] = sym
    # Also map benchmark indices
    for bench in BENCHMARK_INDICES:
        names[bench.symbol] = bench.name
    return names


def _get_portfolio_data() -> dict[str, Any]:
    """Get or compute portfolio analysis data (cached)."""
    if "portfolio" not in _cache:
        analyzer = PortfolioAnalyzer(
            portfolio=_default_portfolio(),
            benchmark_symbol="ACWI",
            period="max",
            interval="1mo",
        )
        _cache["portfolio"] = analyzer.run()
    result: dict[str, Any] = _cache["portfolio"]
    return result


def _get_comparison_data() -> dict[str, Any]:
    """Get or compute comparison data (cached)."""
    if "comparison" not in _cache:
        comparator = PortfolioComparator(
            strategies=_default_strategies(),
            monthly_investment=100,
            rebalance_every_months=6,
            benchmark_symbol="ACWI",
            period="max",
            interval="1mo",
        )
        _cache["comparison"] = comparator.run()
    result: dict[str, Any] = _cache["comparison"]
    return result


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Portfolio Analyzer", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        """Render the portfolio dashboard."""
        data = _get_portfolio_data()
        safe = _make_json_safe(data)
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {"data": safe, "names": _symbol_names()},
        )

    @app.get("/comparison", response_class=HTMLResponse)
    async def comparison(request: Request) -> HTMLResponse:
        """Render the strategy comparison page."""
        data = _get_comparison_data()
        safe = _make_json_safe(data)
        return templates.TemplateResponse(
            request,
            "comparison.html",
            {"data": safe, "names": _symbol_names()},
        )

    @app.get("/benchmarks", response_class=HTMLResponse)
    async def benchmarks(request: Request) -> HTMLResponse:
        """Render the benchmark indices page."""
        data = _get_benchmark_data()
        safe = _make_json_safe(data)
        return templates.TemplateResponse(
            request,
            "benchmarks.html",
            {"data": safe, "names": _symbol_names()},
        )

    @app.get("/api/benchmarks")
    async def api_benchmarks() -> JSONResponse:
        """Return benchmark index data as JSON."""
        data = _get_benchmark_data()
        safe = _make_json_safe(data)
        return JSONResponse(content=safe)

    @app.get("/api/portfolio")
    async def api_portfolio() -> JSONResponse:
        """Return portfolio analysis as JSON."""
        data = _get_portfolio_data()
        safe = _make_json_safe(data)
        return JSONResponse(content=safe)

    @app.get("/api/comparison")
    async def api_comparison() -> JSONResponse:
        """Return strategy comparison as JSON."""
        data = _get_comparison_data()
        safe = _make_json_safe(data)
        return JSONResponse(content=safe)

    return app


# Module-level instance for `uvicorn portfolio_analyzer.web:app`
app = create_app()
