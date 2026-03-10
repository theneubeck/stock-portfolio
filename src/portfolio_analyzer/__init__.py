"""Portfolio Analyzer — evaluate holdings, calculate metrics, gain insights."""

from portfolio_analyzer.analyzer import PortfolioAnalyzer
from portfolio_analyzer.comparison import PortfolioComparator
from portfolio_analyzer.dca import DCASimulator
from portfolio_analyzer.models import Holding, Portfolio, TargetAllocation
from portfolio_analyzer.report import format_report
from portfolio_analyzer.rolling import rolling_return_statistics, rolling_returns
from portfolio_analyzer.web import create_app

__all__ = [
    "DCASimulator",
    "Holding",
    "Portfolio",
    "PortfolioAnalyzer",
    "PortfolioComparator",
    "TargetAllocation",
    "create_app",
    "format_report",
    "rolling_return_statistics",
    "rolling_returns",
]
