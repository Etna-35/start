"""Orchestration around daily review: rendering numbered lists, applying scores,
and building the per-user daily summary from DB entries."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.review_session import DailyReviewSession
from app.models.time_entry import TimeEntry, VALID_SCORES
from app.repositories import review_sessions as review_repo
from app.repositories import time_entries as entry_repo
from app.services import messages
from app.services.formatting import esc
from app.services.summary_service import EntryStat, build_summary, format_summary
from app.services.timefmt import format_minutes


def _render_list(entries: list[TimeEntry], with_scores: bool) -> str:
    lines: list[str] = []
    for idx, entry in enumerate(entries, start=1):
        tail = ""
        if with_scores:
            tail = f" [{entry.abc_score}]" if entry.abc_score else " [без оценки]"
        lines.append(
            f"<b>{idx}.</b> {format_minutes(entry.duration_min)} — {esc(entry.action_text)}{tail}"
        )
    return "\n".join(lines)


def render_today(session: Session, user_id: uuid.UUID, day: date) -> str | None:
    """Build the /today list and persist a review session with the shown order.
    Returns None if there are no entries today."""
    entries = entry_repo.list_for_day(session, user_id, day)
    if not entries:
        return None
    review_repo.create(session, user_id, day, [str(e.id) for e in entries])
    body = _render_list(entries, with_scores=True)
    return (
        "<b>Твои действия сегодня</b>\n\n"
        f"{body}\n\n"
        "Чтобы оценить, напиши:\n"
        "<b>1A 2B 3D</b>"
    )


def render_evening_review(session: Session, user_id: uuid.UUID, day: date) -> str | None:
    """Build the evening prompt over unscored entries. Returns None if none."""
    entries = entry_repo.list_unscored_for_day(session, user_id, day)
    if not entries:
        return None
    review_repo.create(session, user_id, day, [str(e.id) for e in entries])
    body = _render_list(entries, with_scores=False)
    return (
        f"{messages.REVIEW_PROMPT_HEADER}\n\n"
        f"{body}\n\n"
        f"{messages.REVIEW_INSTRUCTIONS}"
    )


def apply_scores(
    session: Session, user_id: uuid.UUID, day: date, scores: dict[int, str]
) -> tuple[int, DailyReviewSession | None]:
    """Apply numbered scores against the latest pending session for the day.
    Returns (applied_count, session). applied_count == -1 means no session."""
    review = review_repo.latest_pending_for_day(session, user_id, day)
    if review is None:
        review = review_repo.latest_for_day(session, user_id, day)
    if review is None or not review.entry_ids:
        return -1, None

    entry_ids: list[str] = list(review.entry_ids)
    by_id = entry_repo.get_by_ids(session, entry_ids)

    applied = 0
    for number, score in scores.items():
        if score not in VALID_SCORES:
            continue
        if 1 <= number <= len(entry_ids):
            entry = by_id.get(entry_ids[number - 1])
            if entry is not None:
                entry.abc_score = score
                applied += 1

    if applied:
        review_repo.mark_completed(session, review)
    return applied, review


def build_day_summary_text(session: Session, user_id: uuid.UUID, day: date) -> str:
    entries = entry_repo.list_for_day(session, user_id, day)
    if not entries:
        return messages.NO_ENTRIES_TODAY
    stats = [EntryStat(duration_min=e.duration_min, abc_score=e.abc_score) for e in entries]
    return format_summary(build_summary(stats))
