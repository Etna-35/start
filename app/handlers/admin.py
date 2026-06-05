from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import parse_errors as parse_error_repo
from app.repositories import time_entries as entry_repo
from app.repositories import users as user_repo
from app.services import messages
from app.services.privacy_service import AdminStats, format_admin_stats


def handle_admin_stats(session: Session, user: User, day: date) -> str:
    if not user.is_admin:
        return messages.ADMIN_ONLY

    stats = AdminStats(
        total_users=user_repo.count_total(session),
        consented_users=user_repo.count_consented(session),
        active_today=entry_repo.count_active_users_for_day(session, day),
        entries_today=entry_repo.count_for_day(session, day),
        scored_entries_today=entry_repo.count_scored_for_day(session, day),
        parse_errors_today=parse_error_repo.count_for_day(session, day),
    )
    return format_admin_stats(stats)
