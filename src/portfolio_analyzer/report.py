"""Report formatting for portfolio analysis results."""

from __future__ import annotations

from typing import Any

import pandas as pd


def format_dca_report(result: dict[str, Any]) -> str:
    """Format a DCA simulation result as a human-readable text report.

    Args:
        result: The dict returned by DCASimulator.run().

    Returns:
        A formatted multi-line string report.
    """
    lines: list[str] = []
    sep = "=" * 60

    summary = result["summary"]

    # ── Summary ───────────────────────────────
    lines.append(sep)
    lines.append("  DCA INVESTMENT REPORT")
    lines.append(sep)
    lines.append(
        f"  Monthly Investment:  ${summary['total_invested'] / summary['num_investments']:,.0f}"
    )
    lines.append(f"  Total Invested:      ${summary['total_invested']:,.2f}")
    lines.append(f"  Final Value:         ${summary['final_value']:,.2f}")
    profit = summary["final_value"] - summary["total_invested"]
    lines.append(f"  Profit/Loss:         ${profit:+,.2f}")
    lines.append(f"  Total Return:        {summary['total_return_pct']:+.2f}%")
    lines.append(f"  Annualized Return:   {summary['annualized_return_pct']:+.2f}%")
    lines.append(f"  Investment Periods:  {summary['num_investments']}")
    lines.append(f"  Rebalances:          {summary['num_rebalances']}")
    lines.append("")

    # ── Value History (first/last 5) ──────────
    lines.append("-" * 60)
    lines.append("  INVESTMENT GROWTH")
    lines.append("-" * 60)
    value_history: pd.Series = result["value_history"]
    lines.append(f"  {'Date':<14} {'Value':>14} {'Invested':>14}")
    lines.append(f"  {'----':<14} {'-----':>14} {'--------':>14}")

    total_per_month = summary["total_invested"] / summary["num_investments"]
    n = len(value_history)
    show_indices: list[int] = []
    if n <= 10:
        show_indices = list(range(n))
    else:
        show_indices = [*list(range(5)), -1, *list(range(n - 4, n))]

    prev_idx = -1
    for idx in show_indices:
        if idx == -1:
            lines.append(f"  {'  ...':>14}")
            continue
        if prev_idx != -1 and idx - prev_idx > 1 and idx != show_indices[0]:
            pass  # already handled by -1 sentinel
        date_str = str(value_history.index[idx].date())
        invested_so_far = total_per_month * (idx + 1)
        lines.append(
            f"  {date_str:<14} ${value_history.iloc[idx]:>12,.2f} ${invested_so_far:>12,.2f}"
        )
        prev_idx = idx
    lines.append("")

    # ── Rebalancing Log ───────────────────────
    lines.append("-" * 60)
    lines.append(f"  REBALANCING LOG ({len(result['rebalancing_log'])} events)")
    lines.append("-" * 60)
    for entry in result["rebalancing_log"]:
        date_str = (
            str(entry["date"].date()) if hasattr(entry["date"], "date") else str(entry["date"])
        )
        lines.append(f"  {date_str}  Value: ${entry['portfolio_value']:,.2f}")
        for sym in entry["weights_before"]:
            before = entry["weights_before"][sym]
            after = entry["weights_after"][sym]
            target = entry["target_weights"][sym]
            lines.append(f"    {sym:<6} {before:5.1f}% → {after:5.1f}%  (target {target:.0f}%)")
    lines.append("")

    # ── Comparison ────────────────────────────
    lines.append("-" * 60)
    lines.append("  DCA vs LUMP-SUM vs BENCHMARK")
    lines.append("-" * 60)
    comp = result["comparison"]
    lines.append(f"  Total Invested:            ${comp['total_invested']:>12,.2f}")
    lines.append("")
    lines.append(f"  DCA Final Value:           ${comp['dca_final_value']:>12,.2f}")
    lines.append(f"  DCA Return:                {comp['dca_return_pct']:>+11.2f}%")
    lines.append("")
    lines.append(f"  Lump-Sum Final Value:      ${comp['lump_sum_final_value']:>12,.2f}")
    lines.append(f"  Lump-Sum Return:           {comp['lump_sum_return_pct']:>+11.2f}%")
    lines.append("")
    lines.append(f"  Benchmark Final Value:     ${comp['benchmark_final_value']:>12,.2f}")
    lines.append(f"  Benchmark Return:          {comp['benchmark_return_pct']:>+11.2f}%")
    lines.append("")
    lines.append(sep)

    return "\n".join(lines)


def format_report(report: dict[str, Any]) -> str:
    """Format a structured analysis report as a human-readable text report.

    Args:
        report: The dict returned by PortfolioAnalyzer.run().

    Returns:
        A formatted multi-line string report.
    """
    lines: list[str] = []
    sep = "=" * 60

    # ── Summary ───────────────────────────────
    lines.append(sep)
    lines.append("  PORTFOLIO ANALYSIS REPORT")
    lines.append(sep)
    summary = report["summary"]
    lines.append(f"  Holdings:        {summary['num_holdings']}")
    lines.append(f"  Total Value:     ${summary['total_portfolio_value']:,.2f}")
    lines.append(f"  Benchmark:       {summary['benchmark']}")
    lines.append(f"  Period:          {summary['period']}")
    interval_labels: dict[str, str] = {
        "1d": "Daily",
        "1wk": "Weekly",
        "1mo": "Monthly",
    }
    interval_label = interval_labels.get(
        summary.get("interval", "1d"), summary.get("interval", "1d")
    )
    lines.append(f"  Interval:        {interval_label}")
    lines.append("")

    # ── Allocation ────────────────────────────
    lines.append("-" * 60)
    lines.append("  ALLOCATION")
    lines.append("-" * 60)
    lines.append(f"  {'Symbol':<8} {'Market Value':>14} {'Weight':>10}")
    lines.append(f"  {'------':<8} {'------------':>14} {'------':>10}")
    for symbol, alloc in report["allocation"].items():
        mv = f"${alloc['market_value']:,.2f}"
        w = f"{alloc['weight_pct']:.1f}%"
        lines.append(f"  {symbol:<8} {mv:>14} {w:>10}")
    lines.append("")

    # ── Performance ───────────────────────────
    lines.append("-" * 60)
    lines.append("  PERFORMANCE")
    lines.append("-" * 60)
    lines.append(f"  {'Symbol':<8} {'Total Return':>14} {'Ann. Return':>14}")
    lines.append(f"  {'------':<8} {'------------':>14} {'-----------':>14}")
    for symbol, perf in report["performance"].items():
        tr = f"{perf['total_return_pct']:+.2f}%"
        ar = f"{perf['annualized_return_pct']:+.2f}%"
        lines.append(f"  {symbol:<8} {tr:>14} {ar:>14}")
    lines.append("")

    # ── Risk ──────────────────────────────────
    lines.append("-" * 60)
    lines.append("  RISK METRICS")
    lines.append("-" * 60)
    risk = report["risk"]
    lines.append(f"  Volatility (ann.):  {risk['volatility_pct']:.2f}%")
    lines.append(f"  Sharpe Ratio:       {risk['sharpe_ratio']:.2f}")
    lines.append(f"  Max Drawdown:       {risk['max_drawdown_pct']:.2f}%")
    lines.append("")

    # ── Benchmark Comparison ──────────────────
    lines.append("-" * 60)
    lines.append("  BENCHMARK COMPARISON")
    lines.append("-" * 60)
    comp = report["benchmark_comparison"]
    lines.append(f"  Portfolio Return:   {comp['portfolio_return_pct']:+.2f}%")
    lines.append(f"  Benchmark Return:   {comp['benchmark_return_pct']:+.2f}%")
    lines.append(f"  Excess Return:      {comp['excess_return_pct']:+.2f}%")
    lines.append("")
    lines.append(sep)

    return "\n".join(lines)
