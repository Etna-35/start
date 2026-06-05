"""Parsing and resolution of the per-user evening review time."""

from __future__ import annotations

import re


def parse_review_time(arg: str) -> tuple[int, int] | None:
    """Parse a user-supplied time. Accepts '21:30', '21.30', '21 30', '21'.
    Returns (hour, minute) or None if invalid."""
    if not arg:
        return None
    m = re.fullmatch(r"\s*(\d{1,2})\s*[:.\s]\s*(\d{1,2})\s*", arg)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
    else:
        m2 = re.fullmatch(r"\s*(\d{1,2})\s*", arg)
        if not m2:
            return None
        hour, minute = int(m2.group(1)), 0
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    return None


def effective_review_time(user, settings) -> tuple[int, int]:
    """The user's review time, falling back to the global default."""
    hour = user.review_hour if getattr(user, "review_hour", None) is not None else settings.daily_review_hour
    minute = (
        user.review_minute
        if getattr(user, "review_minute", None) is not None
        else settings.daily_review_minute
    )
    return hour, minute


def format_hhmm(hour: int, minute: int) -> str:
    return f"{hour:02d}:{minute:02d}"
