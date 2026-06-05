from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import parse_errors as parse_error_repo
from app.repositories import time_entries as entry_repo
from app.services import messages
from app.services.duration_parser import parse_entry
from app.services.timefmt import format_minutes


def handle_entry(session: Session, user: User, raw_text: str, day: date) -> str:
    parsed = parse_entry(raw_text)
    if parsed is None:
        # On MVP we do not store entries without a duration; log the parse miss.
        parse_error_repo.record(session, user.id, raw_text, "duration_not_found")
        return messages.DURATION_NOT_FOUND

    entry_repo.create(
        session,
        user=user,
        entry_date=day,
        duration_min=parsed.duration_min,
        action_text=parsed.action_text,
        raw_text=raw_text,
    )
    return (
        "Записал:\n"
        f"{format_minutes(parsed.duration_min)} - {parsed.action_text}\n"
        "Оценку A/B/C/D поставим вечером."
    )
