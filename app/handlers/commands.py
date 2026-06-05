from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.config import Settings
from app.handlers.admin import handle_admin_stats
from app.models.user import User
from app.schemas.dto import Reply
from app.repositories import time_entries as entry_repo
from app.repositories import users as user_repo
from app.services import community_stats_service as community
from app.services import messages, review_service
from app.services.clock import today_in
from app.services.privacy_service import ExportEntry, build_export
from app.services.summary_service import EntryStat
from app.services.time_settings import effective_review_time, format_hhmm, parse_review_time


def handle_command(
    session: Session, user: User, text: str, settings: Settings, day: date
) -> str | Reply:
    command = text.split()[0].lower().lstrip("/")
    command = command.split("@")[0]  # tolerate /cmd@botname

    if command == "start":
        return messages.START
    if command == "agree":
        return _agree(session, user)
    if command == "help":
        return messages.HELP

    # Everything below requires consent.
    if not user.consent_accepted:
        return messages.NEED_CONSENT

    if command == "today":
        view = review_service.render_today(session, user.id, day)
        if view is None:
            return messages.NO_ENTRIES_TODAY
        text, attachments = view
        return Reply(text, attachments)
    if command in ("done", "finish", "review", "оценить", "завершить"):
        view = review_service.start_interactive(session, user.id, day)
        if view is None:
            return review_service.build_day_summary_text(session, user.id, day)
        text, attachments = view
        return Reply(text, attachments)
    if command == "summary":
        return review_service.build_day_summary_text(session, user.id, day)
    if command == "community":
        return _community(session, settings)
    if command == "export":
        return _export(session, user)
    if command in ("time", "время", "vremya"):
        return _set_time(session, user, text, settings)
    if command == "delete_today":
        return messages.CONFIRM_DELETE_TODAY
    if command == "delete_me":
        return messages.CONFIRM_DELETE_ME
    if command == "admin_stats":
        return handle_admin_stats(session, user, day)

    return messages.UNKNOWN_COMMAND


def _agree(session: Session, user: User) -> str:
    user_repo.accept_consent(session, user)
    return messages.AGREE_DONE


def _set_time(session: Session, user: User, text: str, settings: Settings) -> str:
    parts = text.split(maxsplit=1)
    arg = parts[1] if len(parts) > 1 else ""
    parsed = parse_review_time(arg)
    if parsed is None:
        current = format_hhmm(*effective_review_time(user, settings))
        return (
            f"Сейчас вечерняя оценка приходит в <b>{current}</b> "
            f"(часовой пояс {user.timezone}).\n"
            "Чтобы изменить, укажи время в формате ЧЧ:ММ, например:\n/time 21:30"
        )
    hour, minute = parsed
    user_repo.set_review_time(session, user, hour, minute)
    return (
        f"Готово ✅ Список для вечерней оценки буду присылать в "
        f"<b>{format_hhmm(hour, minute)}</b> (часовой пояс {user.timezone})."
    )


def _community(session: Session, settings: Settings) -> str:
    day = today_in(settings.default_timezone)
    entries = entry_repo.all_for_day(session, day)
    per_user: dict[str, list[EntryStat]] = {}
    for e in entries:
        per_user.setdefault(str(e.user_id), []).append(
            EntryStat(duration_min=e.duration_min, abc_score=e.abc_score)
        )
    stats = community.aggregate(per_user)
    return community.format_community_stats(stats)


def _export(session: Session, user: User) -> str:
    entries = entry_repo.list_recent_for_user(session, user.id, days=7)
    export_rows = [
        ExportEntry(
            entry_date=e.entry_date,
            duration_min=e.duration_min,
            abc_score=e.abc_score,
            action_text=e.action_text,
        )
        for e in entries
    ]
    return build_export(export_rows)
