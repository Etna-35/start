"""Human-friendly Russian duration formatting."""

from __future__ import annotations


def format_minutes(total_min: int) -> str:
    """Format minutes as 'X ч Y мин' / 'Y мин' / 'X ч'."""
    total_min = max(0, int(total_min))
    hours, minutes = divmod(total_min, 60)
    if hours and minutes:
        return f"{hours} ч {minutes} мин"
    if hours:
        return f"{hours} ч"
    return f"{minutes} мин"
