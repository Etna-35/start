from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.config import Settings
from app.models.user import User
from app.repositories import users as user_repo
from app.schemas.dto import CallbackResult
from app.services import review_service
from app.services.keyboards import parse_callback
from app.services.time_settings import format_hhmm, parse_review_time


def handle_callback(
    session: Session, user: User, payload: str, day: date, settings: Settings
) -> CallbackResult | None:
    """Process an inline-button press. Returns a CallbackResult, or None if the
    payload is not understood."""
    parts = parse_callback(payload)
    if parts is None:
        return None
    namespace = parts[0]

    if namespace == "tm":
        return _set_time(session, user, parts[1])

    # namespace == "rv"
    action = parts[1]
    args = parts[2:]

    if action == "start":
        return CallbackResult(view=review_service.begin_view(session, user.id, day))

    if action == "p" and args:
        page = _to_int(args[0])
        return CallbackResult(view=review_service.render_page_view(session, user.id, day, page))

    if action == "s" and len(args) >= 3:
        entry_id, score = args[0], args[1]
        page = _to_int(args[2])
        review_service.set_score_by_id(session, entry_id, score)
        return CallbackResult(view=review_service.after_score_view(session, user.id, day, page))

    if action == "b" and args:
        review_service.bulk_score_remaining(session, user.id, day, args[0])
        return CallbackResult(view=review_service.render_done(session, user.id, day))

    if action == "done":
        return CallbackResult(view=review_service.render_done(session, user.id, day))

    if action == "x":  # item-number label — just acknowledge
        return CallbackResult(silent=True)

    return None


def _to_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _set_time(session: Session, user: User, raw: str) -> CallbackResult:
    parsed = parse_review_time(raw)
    if parsed is None:
        return CallbackResult(notification="Не понял время")
    hour, minute = parsed
    user_repo.set_review_time(session, user, hour, minute)
    return CallbackResult(
        notification=f"Готово ✅ Оценка дня будет приходить в {format_hhmm(hour, minute)}"
    )
