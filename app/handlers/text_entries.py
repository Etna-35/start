from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.config import Settings
from app.models.user import User
from app.repositories import parse_errors as parse_error_repo
from app.repositories import time_entries as entry_repo
from app.schemas.dto import Reply
from app.services import keyboards, messages
from app.services.duration_parser import parse_entry
from app.services.formatting import esc
from app.services.time_settings import effective_review_time, format_hhmm
from app.services.timefmt import format_minutes


def handle_entry(
    session: Session, user: User, raw_text: str, day: date, settings: Settings
) -> str | Reply:
    parsed = parse_entry(raw_text)
    if parsed is None:
        # No duration: treat any free text ("конец", "я спать", forgot the time)
        # as a gentle prompt offering the finish-day button, not a hard error.
        parse_error_repo.record(session, user.id, raw_text, "duration_not_found")
        return Reply(messages.DURATION_NOT_FOUND, keyboards.finish_keyboard())

    # Is this the first entry of the day? (check before inserting)
    is_first = not entry_repo.list_for_day(session, user.id, day)

    entry_repo.create(
        session,
        user=user,
        entry_date=day,
        duration_min=parsed.duration_min,
        action_text=parsed.action_text,
        raw_text=raw_text,
    )

    if is_first:
        review_time = format_hhmm(*effective_review_time(user, settings))
        text = messages.first_entry_reply(
            format_minutes(parsed.duration_min), esc(parsed.action_text), review_time
        )
        return Reply(text, keyboards.time_and_finish_keyboard())

    # Subsequent entries: a quiet, lightweight green-check ack (no buttons).
    return messages.ENTRY_ACK
