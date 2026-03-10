"""Lightweight read-only web interface using FastAPI + Jinja2."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from portfolio_analyzer.dca import DCASimulator
from portfolio_analyzer.metrics import RISK_FREE_RATE, individual_returns
from portfolio_analyzer.models import TargetAllocation
from portfolio_analyzer.rolling import (
    rolling_return_histogram,
    rolling_return_statistics,
    rolling_returns,
)

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


# ── Portfolio registry ────────────────────────────────────────────────────────


@dataclass
class PortfolioConfig:
    """Configuration for a single portfolio in the registry."""

    slug: str
    name: str
    targets: list[TargetAllocation]
    dca_monthly_investment: float = 1000.0
    rebalance_every_months: int = 0
    benchmark_symbol: str = "ACWI"
    period: str = "max"
    interval: str = "1mo"
    strategy_type: str = "DCA (No Rebalance)"
    tags: list[str] = field(default_factory=list)


def _all_portfolios() -> list[PortfolioConfig]:
    """Return the full list of portfolio configurations."""
    return [
        # ── User portfolio ────────────────────────────────
        PortfolioConfig(
            slug="global-multi-asset",
            name="Global Multi-Asset",
            targets=[
                TargetAllocation(symbol="GLD", name="SPDR Gold Shares", target_weight_pct=15.0),
                TargetAllocation(
                    symbol="GSG", name="iShares S&P GSCI Commodity ETF", target_weight_pct=15.0
                ),
                TargetAllocation(
                    symbol="ACWI", name="iShares MSCI ACWI ETF", target_weight_pct=40.0
                ),
                TargetAllocation(
                    symbol="AGG", name="iShares Core US Aggregate Bond ETF", target_weight_pct=30.0
                ),
            ],
            strategy_type="DCA (No Rebalance)",
            tags=["custom"],
        ),
        # ── Benchmark indices (single-holding portfolios) ─
        PortfolioConfig(
            slug="sp500",
            name="S&P 500",
            targets=[
                TargetAllocation(symbol="SPY", name="SPDR S&P 500 ETF", target_weight_pct=100.0)
            ],
            tags=["benchmark", "us"],
        ),
        PortfolioConfig(
            slug="nasdaq100",
            name="Nasdaq 100",
            targets=[
                TargetAllocation(symbol="QQQ", name="Invesco QQQ Trust", target_weight_pct=100.0)
            ],
            tags=["benchmark", "us"],
        ),
        PortfolioConfig(
            slug="msci-acwi",
            name="MSCI ACWI",
            targets=[
                TargetAllocation(
                    symbol="ACWI", name="iShares MSCI ACWI ETF", target_weight_pct=100.0
                )
            ],
            tags=["benchmark", "global"],
        ),
        PortfolioConfig(
            slug="ftse-europe",
            name="FTSE Europe",
            targets=[
                TargetAllocation(
                    symbol="VGK", name="Vanguard FTSE Europe ETF", target_weight_pct=100.0
                )
            ],
            tags=["benchmark", "europe"],
        ),
        PortfolioConfig(
            slug="euro-stoxx-50",
            name="EURO STOXX 50",
            targets=[
                TargetAllocation(
                    symbol="FEZ", name="SPDR EURO STOXX 50 ETF", target_weight_pct=100.0
                )
            ],
            tags=["benchmark", "europe"],
        ),
        PortfolioConfig(
            slug="sweden",
            name="MSCI Sweden",
            targets=[
                TargetAllocation(
                    symbol="EWD", name="iShares MSCI Sweden ETF", target_weight_pct=100.0
                )
            ],
            tags=["benchmark", "europe"],
        ),
        PortfolioConfig(
            slug="japan",
            name="MSCI Japan",
            targets=[
                TargetAllocation(
                    symbol="EWJ", name="iShares MSCI Japan ETF", target_weight_pct=100.0
                )
            ],
            tags=["benchmark", "asia"],
        ),
        PortfolioConfig(
            slug="emerging-markets",
            name="Emerging Markets",
            targets=[
                TargetAllocation(
                    symbol="EEM", name="iShares MSCI Emerging Markets ETF", target_weight_pct=100.0
                )
            ],
            tags=["benchmark", "emerging"],
        ),
        PortfolioConfig(
            slug="us-bonds",
            name="US Aggregate Bond",
            targets=[
                TargetAllocation(
                    symbol="AGG",
                    name="iShares Core US Aggregate Bond ETF",
                    target_weight_pct=100.0,
                )
            ],
            tags=["benchmark", "bonds"],
        ),
        PortfolioConfig(
            slug="gold",
            name="Gold",
            targets=[
                TargetAllocation(symbol="GLD", name="SPDR Gold Shares", target_weight_pct=100.0)
            ],
            tags=["benchmark", "commodity"],
        ),
        # ── Strategy portfolios ───────────────────────────
        PortfolioConfig(
            slug="equal-weight",
            name="Equal Weight",
            targets=[
                TargetAllocation(symbol="GLD", name="SPDR Gold Shares", target_weight_pct=25.0),
                TargetAllocation(
                    symbol="GSG", name="iShares S&P GSCI Commodity ETF", target_weight_pct=25.0
                ),
                TargetAllocation(
                    symbol="ACWI", name="iShares MSCI ACWI ETF", target_weight_pct=25.0
                ),
                TargetAllocation(
                    symbol="AGG", name="iShares Core US Aggregate Bond ETF", target_weight_pct=25.0
                ),
            ],
            rebalance_every_months=6,
            strategy_type="DCA & Rebalance (6mo)",
            tags=["strategy"],
        ),
        PortfolioConfig(
            slug="heavy-gold",
            name="Heavy Gold",
            targets=[
                TargetAllocation(symbol="GLD", name="SPDR Gold Shares", target_weight_pct=50.0),
                TargetAllocation(
                    symbol="GSG", name="iShares S&P GSCI Commodity ETF", target_weight_pct=10.0
                ),
                TargetAllocation(
                    symbol="ACWI", name="iShares MSCI ACWI ETF", target_weight_pct=20.0
                ),
                TargetAllocation(
                    symbol="AGG", name="iShares Core US Aggregate Bond ETF", target_weight_pct=20.0
                ),
            ],
            rebalance_every_months=6,
            strategy_type="DCA & Rebalance (6mo)",
            tags=["strategy"],
        ),
        PortfolioConfig(
            slug="stocks-and-bonds",
            name="Stocks & Bonds",
            targets=[
                TargetAllocation(
                    symbol="ACWI", name="iShares MSCI ACWI ETF", target_weight_pct=60.0
                ),
                TargetAllocation(
                    symbol="AGG", name="iShares Core US Aggregate Bond ETF", target_weight_pct=40.0
                ),
            ],
            rebalance_every_months=6,
            strategy_type="DCA & Rebalance (6mo)",
            tags=["strategy"],
        ),
        PortfolioConfig(
            slug="all-weather",
            name="All Weather",
            targets=[
                TargetAllocation(symbol="GLD", name="SPDR Gold Shares", target_weight_pct=30.0),
                TargetAllocation(
                    symbol="GSG", name="iShares S&P GSCI Commodity ETF", target_weight_pct=15.0
                ),
                TargetAllocation(
                    symbol="ACWI", name="iShares MSCI ACWI ETF", target_weight_pct=30.0
                ),
                TargetAllocation(
                    symbol="AGG", name="iShares Core US Aggregate Bond ETF", target_weight_pct=25.0
                ),
            ],
            rebalance_every_months=6,
            strategy_type="DCA & Rebalance (6mo)",
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
        for t in cfg.targets:
            names[t.symbol] = t.name or t.symbol
    return names


def _analyze_portfolio(cfg: PortfolioConfig) -> dict[str, Any]:
    """Run analysis for one portfolio config (cached)."""
    cache_key = f"portfolio:{cfg.slug}"
    if cache_key not in _cache:
        import numpy as np

        # ── DCA / Rebalancing Portfolio ────────────────────────
        bench = cfg.benchmark_symbol
        if len(cfg.targets) == 1 and cfg.targets[0].symbol == bench:
            bench = "SPY"

        simulator = DCASimulator(
            targets=cfg.targets,
            monthly_investment=cfg.dca_monthly_investment,
            rebalance_every_months=cfg.rebalance_every_months,
            benchmark_symbol=bench,
            period=cfg.period,
            interval=cfg.interval,
        )
        sim_res = simulator.run()

        # Reconstruct the expected 'result' shape
        final_shares = sim_res["summary"]["final_shares"]
        final_prices = sim_res["summary"]["final_prices"]
        total_value = sim_res["summary"]["final_value"]

        alloc: dict[str, dict[str, float]] = {}
        for t in cfg.targets:
            sym = t.symbol
            mv = final_shares[sym] * final_prices[sym]
            alloc[sym] = {
                "market_value": mv,
                "weight_pct": (mv / total_value * 100.0) if total_value > 0 else 0.0,
                "target_weight_pct": t.target_weight_pct,
            }

        # Performance of individual underlying assets
        perf = individual_returns(simulator.price_data, simulator.symbols, interval=cfg.interval)

        # Risk metrics calculated over the DCA value history
        vh = sim_res["value_history"]
        periodic = vh.pct_change().dropna()
        vol = float(periodic.std() * np.sqrt(12)) * 100.0  # 1mo interval = 12 ppy
        ann_ret_dec = sim_res["summary"]["annualized_return_pct"] / 100.0
        sharpe = (ann_ret_dec - RISK_FREE_RATE) / (vol / 100.0) if vol > 0 else 0.0

        cum = vh / float(vh.iloc[0])
        running_max = cum.cummax()
        dd = (cum - running_max) / running_max
        max_dd = float(dd.min()) * 100.0 if len(dd) > 0 else 0.0

        risk = {
            "volatility_pct": vol,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_dd,
        }

        comparison = {
            "portfolio_return_pct": sim_res["summary"]["total_return_pct"],
            "benchmark_return_pct": sim_res["comparison"]["benchmark_return_pct"],
            "excess_return_pct": sim_res["summary"]["total_return_pct"]
            - sim_res["comparison"]["benchmark_return_pct"],
        }

        result: dict[str, Any] = {
            "summary": {
                "num_holdings": len(cfg.targets),
                "total_portfolio_value": total_value,
                "benchmark": bench,
                "period": cfg.period,
                "interval": cfg.interval,
                "total_invested": sim_res["summary"]["total_invested"],
            },
            "allocation": alloc,
            "performance": perf,
            "risk": risk,
            "benchmark_comparison": comparison,
            "statistics": None,  # Skip rich stats for DCA right now
            "activity_log": sim_res["activity_log"],
        }

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


def _rolling_analysis(cfg: PortfolioConfig, horizon: int) -> dict[str, Any]:
    """Compute rolling N-year return analysis for a portfolio (cached).

    For multi-asset portfolios we build a weighted portfolio price series
    from the DCA value history.  For single-asset portfolios we use the
    raw price series directly.
    """
    cache_key = f"rolling:{cfg.slug}:{horizon}"
    if cache_key not in _cache:
        # Get portfolio value history as the "price" series
        analysis = _analyze_portfolio(cfg)

        # Re-run DCA to get the value_history Series
        bench = cfg.benchmark_symbol
        if len(cfg.targets) == 1 and cfg.targets[0].symbol == bench:
            bench = "SPY"

        sim = DCASimulator(
            targets=cfg.targets,
            monthly_investment=cfg.dca_monthly_investment,
            rebalance_every_months=cfg.rebalance_every_months,
            benchmark_symbol=bench,
            period=cfg.period,
            interval=cfg.interval,
        )
        sim.fetch_data()

        # For single-holding: use raw prices (better for rolling analysis)
        # For multi-holding: use the first target's prices as proxy or
        # build a weighted index
        if len(cfg.targets) == 1:
            prices = sim.price_data[cfg.targets[0].symbol]
        else:
            # Build a weighted portfolio price series (normalised to 100)
            weights = {t.symbol: t.target_weight_pct / 100.0 for t in cfg.targets}
            frames: dict[str, pd.Series] = {}
            for t in cfg.targets:
                p = sim.price_data[t.symbol]
                # Normalise each to start at 1
                frames[t.symbol] = p / float(p.iloc[0]) * weights[t.symbol]
            combined = pd.DataFrame(frames).sum(axis=1) * 100.0
            prices = combined

        rets = rolling_returns(prices, horizon_years=horizon, interval=cfg.interval)
        stats = rolling_return_statistics(rets, horizon_years=horizon)
        hist = rolling_return_histogram(rets)

        _cache[cache_key] = {
            "statistics": stats,
            "histogram": hist,
            "meta": analysis.get("meta", {}),
            "horizon": horizon,
        }
    result: dict[str, Any] = _cache[cache_key]
    return result


# ── App factory ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="Portfolio Analyzer", docs_url=None, redoc_url=None)
    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
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

    @application.get("/portfolio/{slug}/rolling", response_class=HTMLResponse)
    async def rolling_returns_page(request: Request, slug: str, horizon: int = 5) -> HTMLResponse:
        """Render the rolling N-year returns page for a portfolio."""
        cfg = _find_config(slug)
        if cfg is None:
            return HTMLResponse(content="Not found", status_code=404)
        data = _rolling_analysis(cfg, horizon)
        safe = _make_json_safe(data)
        return templates.TemplateResponse(
            request,
            "rolling.html",
            {"data": safe, "names": _symbol_names()},
        )

    @application.get("/api/portfolio/{slug}/rolling")
    async def api_rolling_returns(slug: str, horizon: int = 5) -> JSONResponse:
        """Return rolling N-year return analysis as JSON."""
        cfg = _find_config(slug)
        if cfg is None:
            return JSONResponse(content={"error": "Not found"}, status_code=404)
        data = _rolling_analysis(cfg, horizon)
        safe = _make_json_safe(data)
        return JSONResponse(content=safe)

    return application


# Module-level instance for `uvicorn portfolio_analyzer.web:app`
app = create_app()
