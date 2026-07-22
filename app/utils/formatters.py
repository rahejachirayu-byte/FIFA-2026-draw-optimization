"""
formatters.py
-------------
Lightweight formatting helpers so every page shows numbers the same way.
"""

from __future__ import annotations


def fmt_currency(value: float, precision: int = 1) -> str:
    """Turn a dollar amount into a short, readable string ($1.23B / $45.6M / $789K)."""
    if value is None:
        return "—"
    abs_v = abs(value)
    if abs_v >= 1_000_000_000:
        return f"${value / 1_000_000_000:.{precision}f}B"
    if abs_v >= 1_000_000:
        return f"${value / 1_000_000:.{precision}f}M"
    if abs_v >= 1_000:
        return f"${value / 1_000:.{precision}f}K"
    return f"${value:,.0f}"


def fmt_currency_full(value: float) -> str:
    """Full-precision currency for tables ($1,234,567)."""
    if value is None:
        return "—"
    return f"${value:,.0f}"


def fmt_pct(value: float, precision: int = 1) -> str:
    """Format a 0–1 ratio as a percentage string."""
    if value is None:
        return "—"
    return f"{value * 100:.{precision}f}%"


def fmt_delta_pct(value: float, precision: int = 1) -> str:
    """Signed percent for delta displays."""
    if value is None:
        return "—"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{precision}f}%"


def fmt_int(value: float) -> str:
    if value is None:
        return "—"
    return f"{int(value):,}"


def stage_emoji(stage: str) -> str:
    """Optional tiny visual hook for stages."""
    return {
        "Group": "●",
        "Early knockout": "◆",
        "Round of 16": "◈",
        "Third place": "◉",
        "Quarter-finals": "▲",
        "Semi-finals": "★",
        "Final": "◆",
    }.get(stage, "•")
