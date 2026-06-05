from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import ROLE_ADMIN, ROLE_MEMBER, User


def get_by_max_id(session: Session, max_user_id: str) -> User | None:
    stmt = select(User).where(User.max_user_id == max_user_id, User.deleted_at.is_(None))
    return session.scalar(stmt)


def get_by_max_id_any(session: Session, max_user_id: str) -> User | None:
    """Look up by max_user_id ignoring soft-delete (max_user_id is unique)."""
    return session.scalar(select(User).where(User.max_user_id == max_user_id))


def get_or_create(
    session: Session, max_user_id: str, display_name: str | None, admin_ids: list[str], default_tz: str
) -> User:
    # Look up ignoring deleted_at so a leftover (soft-deleted) row never collides
    # with the unique max_user_id constraint on insert.
    user = get_by_max_id_any(session, max_user_id)
    role = ROLE_ADMIN if max_user_id in admin_ids else ROLE_MEMBER
    if user is None:
        user = User(
            max_user_id=max_user_id,
            display_name=display_name,
            role=role,
            timezone=default_tz,
        )
        session.add(user)
        session.flush()
        return user

    # Revive a previously soft-deleted profile (fresh start → re-consent).
    if user.deleted_at is not None:
        user.deleted_at = None
        user.consent_accepted = False

    # Keep display name and admin role fresh.
    if display_name and user.display_name != display_name:
        user.display_name = display_name
    if max_user_id in admin_ids and user.role != ROLE_ADMIN:
        user.role = ROLE_ADMIN
    return user


def accept_consent(session: Session, user: User) -> None:
    user.consent_accepted = True


def set_review_time(session: Session, user: User, hour: int, minute: int) -> None:
    user.review_hour = hour
    user.review_minute = minute


def soft_delete(session: Session, user: User) -> None:
    user.deleted_at = datetime.now(timezone.utc)


def hard_delete(session: Session, user: User) -> None:
    """Fully remove the profile and all its data (entries, review sessions
    cascade via ORM; parse_errors.user_id is set NULL by the DB)."""
    session.delete(user)


def all_consented(session: Session) -> list[User]:
    stmt = select(User).where(User.consent_accepted.is_(True), User.deleted_at.is_(None))
    return list(session.scalars(stmt))


def count_total(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(User).where(User.deleted_at.is_(None))) or 0


def count_consented(session: Session) -> int:
    stmt = (
        select(func.count())
        .select_from(User)
        .where(User.consent_accepted.is_(True), User.deleted_at.is_(None))
    )
    return session.scalar(stmt) or 0
