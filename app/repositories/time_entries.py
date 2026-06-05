from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.time_entry import TimeEntry
from app.models.user import User


def create(
    session: Session,
    user: User,
    entry_date: date,
    duration_min: int,
    action_text: str,
    raw_text: str,
) -> TimeEntry:
    entry = TimeEntry(
        user_id=user.id,
        entry_date=entry_date,
        duration_min=duration_min,
        action_text=action_text,
        raw_text=raw_text,
        abc_score=None,
        source="text",
    )
    session.add(entry)
    session.flush()
    return entry


def _base_today(user_id: uuid.UUID, day: date):
    return select(TimeEntry).where(
        TimeEntry.user_id == user_id,
        TimeEntry.entry_date == day,
        TimeEntry.deleted_at.is_(None),
    )


def list_for_day(session: Session, user_id: uuid.UUID, day: date) -> list[TimeEntry]:
    stmt = _base_today(user_id, day).order_by(TimeEntry.created_at)
    return list(session.scalars(stmt))


def list_unscored_for_day(session: Session, user_id: uuid.UUID, day: date) -> list[TimeEntry]:
    stmt = _base_today(user_id, day).where(TimeEntry.abc_score.is_(None)).order_by(
        TimeEntry.created_at
    )
    return list(session.scalars(stmt))


def get_by_ids(session: Session, entry_ids: list[str]) -> dict[str, TimeEntry]:
    if not entry_ids:
        return {}
    uuids = [uuid.UUID(eid) for eid in entry_ids]
    stmt = select(TimeEntry).where(TimeEntry.id.in_(uuids), TimeEntry.deleted_at.is_(None))
    return {str(e.id): e for e in session.scalars(stmt)}


def list_recent_for_user(session: Session, user_id: uuid.UUID, days: int = 7) -> list[TimeEntry]:
    since = date.today() - timedelta(days=days - 1)
    stmt = (
        select(TimeEntry)
        .where(
            TimeEntry.user_id == user_id,
            TimeEntry.entry_date >= since,
            TimeEntry.deleted_at.is_(None),
        )
        .order_by(TimeEntry.entry_date.desc(), TimeEntry.created_at.desc())
    )
    return list(session.scalars(stmt))


def soft_delete_for_day(session: Session, user_id: uuid.UUID, day: date) -> int:
    entries = list_for_day(session, user_id, day)
    now = datetime.now(timezone.utc)
    for e in entries:
        e.deleted_at = now
    return len(entries)


def all_for_day(session: Session, day: date) -> list[TimeEntry]:
    stmt = select(TimeEntry).where(
        TimeEntry.entry_date == day, TimeEntry.deleted_at.is_(None)
    )
    return list(session.scalars(stmt))


def count_for_day(session: Session, day: date) -> int:
    stmt = (
        select(func.count())
        .select_from(TimeEntry)
        .where(TimeEntry.entry_date == day, TimeEntry.deleted_at.is_(None))
    )
    return session.scalar(stmt) or 0


def count_scored_for_day(session: Session, day: date) -> int:
    stmt = (
        select(func.count())
        .select_from(TimeEntry)
        .where(
            TimeEntry.entry_date == day,
            TimeEntry.deleted_at.is_(None),
            TimeEntry.abc_score.is_not(None),
        )
    )
    return session.scalar(stmt) or 0


def count_active_users_for_day(session: Session, day: date) -> int:
    stmt = (
        select(func.count(func.distinct(TimeEntry.user_id)))
        .where(TimeEntry.entry_date == day, TimeEntry.deleted_at.is_(None))
    )
    return session.scalar(stmt) or 0
