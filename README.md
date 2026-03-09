# Portfolio Analyzer

A Python portfolio analyzer that fetches real market data via **yfinance**, evaluates a balanced portfolio of securities, compares performance against a world index benchmark, and generates a comprehensive text report.

Built **BDD, outside-in** with `pytest-bdd`.

## Features

- **Real market data** — fetches historical prices from Yahoo Finance
- **4-security balanced portfolio** — stocks + bonds
- **Allocation analysis** — market values and portfolio weights
- **Performance metrics** — total and annualized returns per holding
- **Risk metrics** — annualized volatility, Sharpe ratio, maximum drawdown
- **Benchmark comparison** — portfolio vs MSCI World ETF (URTH)
- **Formatted report** — clean, readable text output

## Quickstart

```bash
# Install dependencies
uv sync --all-extras --group dev

# Run the example
uv run python examples/basic_usage.py

# Run all checks
make check
```

## Example Output

```
============================================================
  PORTFOLIO ANALYSIS REPORT
============================================================
  Holdings:        4
  Total Value:     $44,093.10
  Benchmark:       URTH
  Period:          1y

------------------------------------------------------------
  ALLOCATION
------------------------------------------------------------
  Symbol     Market Value     Weight
  ------     ------------     ------
  AAPL         $12,994.00      29.5%
  MSFT         $16,376.40      37.1%
  JNJ           $7,277.70      16.5%
  BND           $7,445.00      16.9%

------------------------------------------------------------
  PERFORMANCE
------------------------------------------------------------
  Symbol     Total Return    Ann. Return
  ------     ------------    -----------
  AAPL            +14.74%        +14.80%
  MSFT             +8.52%         +8.55%
  JNJ             +48.69%        +48.92%
  BND              +5.20%         +5.22%

------------------------------------------------------------
  RISK METRICS
------------------------------------------------------------
  Volatility (ann.):  16.68%
  Sharpe Ratio:       0.75
  Max Drawdown:       -11.93%

------------------------------------------------------------
  BENCHMARK COMPARISON
------------------------------------------------------------
  Portfolio Return:   +16.15%
  Benchmark Return:   +23.52%
  Excess Return:      -7.37%

============================================================
```

## Usage

```python
from portfolio_analyzer import Holding, Portfolio, PortfolioAnalyzer
from portfolio_analyzer.report import format_report

portfolio = Portfolio(
    holdings=[
        Holding(symbol="AAPL", shares=50, name="Apple Inc."),
        Holding(symbol="MSFT", shares=40, name="Microsoft Corp."),
        Holding(symbol="JNJ", shares=30, name="Johnson & Johnson"),
        Holding(symbol="BND", shares=100, name="Vanguard Total Bond Market ETF"),
    ]
)

analyzer = PortfolioAnalyzer(
    portfolio=portfolio,
    benchmark_symbol="URTH",  # iShares MSCI World ETF
    period="1y",
)

report = analyzer.run()
print(format_report(report))
```

## Development

See [AGENTS.md](AGENTS.md) for the full BDD workflow, coding conventions, and review checklist.

```bash
make sync        # Install dependencies
make format      # Auto-format + auto-fix
make lint        # Lint check
make typecheck   # mypy strict
make tests       # pytest (BDD + unit)
make check       # All of the above
```
