"""Domain models for the portfolio analyzer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Holding:
    """A single security holding in a portfolio."""

    symbol: str
    shares: int
    name: str = ""


@dataclass
class Portfolio:
    """A collection of holdings."""

    holdings: list[Holding]

    @property
    def symbols(self) -> list[str]:
        """Return the list of ticker symbols in the portfolio."""
        return [h.symbol for h in self.holdings]


@dataclass
class TargetAllocation:
    """Target allocation for one asset in a DCA portfolio."""

    symbol: str
    name: str
    target_weight_pct: float
