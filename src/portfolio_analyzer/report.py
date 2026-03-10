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

    # ── Statistics ────────────────────────────
    if "statistics" in report:
        stats = report["statistics"]
        _format_portfolio_stats(lines, stats["portfolio"])
        _format_per_holding_stats(lines, stats["per_holding"])

    lines.append(sep)

    return "\n".join(lines)


def format_comparison_report(result: dict[str, Any]) -> str:
    """Format a multi-portfolio comparison result as a human-readable report.

    Args:
        result: The dict returned by PortfolioComparator.run().

    Returns:
        A formatted multi-line string report.
    """
    lines: list[str] = []
    sep = "=" * 72

    lines.append(sep)
    lines.append("  PORTFOLIO STRATEGY COMPARISON")
    lines.append(sep)
    lines.append(
        f"  Benchmark: {result['benchmark_symbol']}"
        f"  (Return: {result['benchmark_return_pct']:+.2f}%)"
    )
    lines.append(f"  Strategies compared: {len(result['strategies'])}")
    lines.append("")

    # ── Side-by-side summary table ────────────
    lines.append("-" * 72)
    header = (
        f"  {'Strategy':<18}"
        f"{'Total Return':>13}"
        f"{'Volatility':>12}"
        f"{'Sharpe':>9}"
        f"{'Max DD':>9}"
        f"{'Excess':>10}"
    )
    lines.append(header)
    divider = (
        f"  {'--------':<18}"
        f"{'------------':>13}"
        f"{'----------':>12}"
        f"{'------':>9}"
        f"{'------':>9}"
        f"{'------':>10}"
    )
    lines.append(divider)

    for s in result["ranking"]:
        row = (
            f"  {s['name']:<18}"
            f"{s['total_return_pct']:>+12.2f}%"
            f"{s['volatility_pct']:>11.2f}%"
            f"{s['sharpe_ratio']:>9.2f}"
            f"{s['max_drawdown_pct']:>+8.2f}%"
            f"{s['excess_return_pct']:>+9.2f}%"
        )
        lines.append(row)
    lines.append("")

    # ── Best / Worst ──────────────────────────
    ranking = result["ranking"]
    best = ranking[0]
    worst = ranking[-1]

    lines.append("-" * 72)
    lines.append("  VERDICT")
    lines.append("-" * 72)
    lines.append(
        f"  Best strategy:   {best['name']}"
        f"  ({best['total_return_pct']:+.2f}% return,"
        f" {best['sharpe_ratio']:.2f} Sharpe)"
    )
    lines.append(
        f"  Worst strategy:  {worst['name']}"
        f"  ({worst['total_return_pct']:+.2f}% return,"
        f" {worst['sharpe_ratio']:.2f} Sharpe)"
    )
    lines.append("")

    if result["beat_benchmark"]:
        names = ", ".join(result["beat_benchmark"])
        lines.append(f"  Beat benchmark:          {names}")
    if result["underperformed_benchmark"]:
        names = ", ".join(result["underperformed_benchmark"])
        lines.append(f"  Underperformed benchmark: {names}")
    lines.append("")
    lines.append(sep)

    return "\n".join(lines)


def _fmt_date(date: Any) -> str:
    """Format a date/timestamp to YYYY-MM-DD string."""
    if hasattr(date, "date"):
        return str(date.date())
    return str(date)


def _format_portfolio_stats(lines: list[str], ps: dict[str, Any]) -> None:
    """Append portfolio-level statistics lines."""
    lines.append("-" * 60)
    lines.append("  PORTFOLIO STATISTICS")
    lines.append("-" * 60)

    peak_d = _fmt_date(ps["peak_value_date"])
    trough_d = _fmt_date(ps["trough_value_date"])
    lines.append(f"  Peak Value:         ${ps['peak_value']:,.2f}  ({peak_d})")
    lines.append(f"  Trough Value:       ${ps['trough_value']:,.2f}  ({trough_d})")
    lines.append(f"  Current Value:      ${ps['current_value']:,.2f}")
    lines.append("")

    best_d = _fmt_date(ps["best_period_date"])
    worst_d = _fmt_date(ps["worst_period_date"])
    best_r = ps["best_period_return_pct"]
    worst_r = ps["worst_period_return_pct"]
    lines.append(f"  Best Period:        {best_r:+.2f}%  ({best_d})")
    lines.append(f"  Worst Period:       {worst_r:+.2f}%  ({worst_d})")
    lines.append(f"  Median Return:      {ps['median_return_pct']:+.2f}%")
    lines.append(f"  Mean Return:        {ps['mean_return_pct']:+.2f}%")
    total = ps["total_periods"]
    lines.append(f"  Positive Periods:   {ps['positive_periods']}/{total}")
    lines.append(f"  Negative Periods:   {ps['negative_periods']}/{total}")
    lines.append("")


def _format_per_holding_stats(
    lines: list[str],
    per_holding: dict[str, dict[str, Any]],
) -> None:
    """Append per-holding statistics lines."""
    lines.append("-" * 60)
    lines.append("  PER-HOLDING STATISTICS")
    lines.append("-" * 60)
    for symbol, hs in per_holding.items():
        min_d = _fmt_date(hs["min_price_date"])
        max_d = _fmt_date(hs["max_price_date"])
        best_d = _fmt_date(hs["best_period_date"])
        worst_d = _fmt_date(hs["worst_period_date"])

        lines.append(f"  {symbol}")
        lines.append(
            f"    Price  — Min: ${hs['min_price']:,.2f} ({min_d})"
            f"  Max: ${hs['max_price']:,.2f} ({max_d})"
        )
        lines.append(f"    Median Price: ${hs['median_price']:,.2f}")
        lines.append(
            f"    Return — Best: {hs['best_period_return_pct']:+.2f}%"
            f" ({best_d})"
            f"  Worst: {hs['worst_period_return_pct']:+.2f}%"
            f" ({worst_d})"
        )
        total = hs["total_periods"]
        up = hs["positive_periods"]
        dn = hs["negative_periods"]
        lines.append(
            f"    Median: {hs['median_return_pct']:+.2f}%"
            f"  Std: {hs['return_std_pct']:.2f}%"
            f"  Up: {up}/{total}  Down: {dn}/{total}"
        )
    lines.append("")
