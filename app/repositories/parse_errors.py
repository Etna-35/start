from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.parse_error import ParseError


def record(
    session: Session, user_id: uuid.UUID | None, raw_text: str, error_type: str
) -> None:
    session.add(ParseError(user_id=user_id, raw_text=raw_text, error_type=error_type))


def count_for_day(session: Session, day: date) -> int:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = datetime.combine(day, time.max, tzinfo=timezone.utc)
    stmt = (
        select(func.count())
        .select_from(ParseError)
        .where(ParseError.created_at >= start, ParseError.created_at <= end)
    )
    return session.scalar(stmt) or 0
