"""Portfolio Analyzer — evaluate holdings, calculate metrics, gain insights."""

from portfolio_analyzer.analyzer import PortfolioAnalyzer
from portfolio_analyzer.comparison import PortfolioComparator
from portfolio_analyzer.dca import DCASimulator
from portfolio_analyzer.models import Holding, Portfolio, TargetAllocation
from portfolio_analyzer.report import format_report

__all__ = [
    "DCASimulator",
    "Holding",
    "Portfolio",
    "PortfolioAnalyzer",
    "PortfolioComparator",
    "TargetAllocation",
    "format_report",
]
