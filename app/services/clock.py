from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import get_settings


def _zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(get_settings().default_timezone)


def now_in(tz_name: str) -> datetime:
    return datetime.now(_zone(tz_name))


def today_in(tz_name: str) -> date:
    return now_in(tz_name).date()
