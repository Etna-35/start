from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review_session import (
    STATUS_COMPLETED,
    STATUS_PENDING,
    DailyReviewSession,
)


def create(
    session: Session, user_id: uuid.UUID, review_date: date, entry_ids: list[str]
) -> DailyReviewSession:
    review = DailyReviewSession(
        user_id=user_id,
        review_date=review_date,
        entry_ids=entry_ids,
        status=STATUS_PENDING,
        created_at=datetime.now(timezone.utc),
    )
    session.add(review)
    session.flush()
    return review


def latest_for_day(
    session: Session, user_id: uuid.UUID, review_date: date
) -> DailyReviewSession | None:
    stmt = (
        select(DailyReviewSession)
        .where(
            DailyReviewSession.user_id == user_id,
            DailyReviewSession.review_date == review_date,
        )
        .order_by(DailyReviewSession.created_at.desc())
    )
    return session.scalars(stmt).first()


def latest_pending_for_day(
    session: Session, user_id: uuid.UUID, review_date: date
) -> DailyReviewSession | None:
    stmt = (
        select(DailyReviewSession)
        .where(
            DailyReviewSession.user_id == user_id,
            DailyReviewSession.review_date == review_date,
            DailyReviewSession.status == STATUS_PENDING,
        )
        .order_by(DailyReviewSession.created_at.desc())
    )
    return session.scalars(stmt).first()


def mark_completed(session: Session, review: DailyReviewSession) -> None:
    review.status = STATUS_COMPLETED
    review.completed_at = datetime.now(timezone.utc)
