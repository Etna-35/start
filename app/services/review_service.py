"""Orchestration around daily review: the interactive button flow, the text
fallback ("1A 2B"), and the per-user daily summary built from DB entries."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.review_session import DailyReviewSession
from app.models.time_entry import VALID_SCORES, TimeEntry
from app.repositories import review_sessions as review_repo
from app.repositories import time_entries as entry_repo
from app.services import keyboards, messages
from app.services.formatting import esc
from app.services.summary_service import EntryStat, build_summary, format_summary
from app.services.timefmt import format_minutes

# A reply that carries an inline keyboard: (text, attachments | None).
ReviewView = tuple[str, list | None]


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


# --- Interactive (button) flow -------------------------------------------------

def render_item(entries: list[TimeEntry], entry: TimeEntry) -> ReviewView:
    """Render a single action to score, with the A/B/C/D keyboard."""
    total = len(entries)
    remaining = sum(1 for e in entries if e.abc_score is None)
    text = (
        f"<b>Оценка дня</b> · осталось {remaining} из {total}\n\n"
        f"<b>{format_minutes(entry.duration_min)}</b> — {esc(entry.action_text)}\n\n"
        "<i>A — собственник · B — управление · C — операционка · D — слив</i>"
    )
    return text, keyboards.score_keyboard(str(entry.id))


def render_done(session: Session, user_id: uuid.UUID, day: date) -> ReviewView:
    """Scoring finished: show the day's summary and clear the keyboard ([]).
    An empty attachments list removes the buttons from the edited message."""
    return build_day_summary_text(session, user_id, day), []


def _next_unscored_after(entries: list[TimeEntry], after_id: str) -> TimeEntry | None:
    seen = False
    for e in entries:
        if seen and e.abc_score is None:
            return e
        if str(e.id) == after_id:
            seen = True
    return None


def render_next_item(
    session: Session, user_id: uuid.UUID, day: date, after: str | None = None
) -> ReviewView:
    entries = entry_repo.list_for_day(session, user_id, day)
    if after is not None:
        nxt = _next_unscored_after(entries, after)
    else:
        nxt = next((e for e in entries if e.abc_score is None), None)
    if nxt is None:
        return render_done(session, user_id, day)
    return render_item(entries, nxt)


def start_interactive(session: Session, user_id: uuid.UUID, day: date) -> ReviewView | None:
    """Begin the button-based scoring. Returns None if nothing to score.
    Also records a review session so the text fallback ('1A 2B') keeps working."""
    entries = entry_repo.list_for_day(session, user_id, day)
    unscored = [e for e in entries if e.abc_score is None]
    if not unscored:
        return None
    review_repo.create(session, user_id, day, [str(e.id) for e in entries])
    return render_item(entries, unscored[0])


def set_score_by_id(session: Session, entry_id: str, score: str) -> None:
    if score not in VALID_SCORES:
        return
    entry = entry_repo.get_by_ids(session, [entry_id]).get(entry_id)
    if entry is not None:
        entry.abc_score = score


def bulk_score_remaining(session: Session, user_id: uuid.UUID, day: date, score: str) -> int:
    if score not in VALID_SCORES:
        return 0
    applied = 0
    for entry in entry_repo.list_for_day(session, user_id, day):
        if entry.abc_score is None:
            entry.abc_score = score
            applied += 1
    return applied


# --- Overview (/today) ---------------------------------------------------------

def render_today(session: Session, user_id: uuid.UUID, day: date) -> ReviewView | None:
    """Build the /today overview list + an 'Оценить' button. None if no entries."""
    entries = entry_repo.list_for_day(session, user_id, day)
    if not entries:
        return None
    review_repo.create(session, user_id, day, [str(e.id) for e in entries])
    body = _render_list(entries, with_scores=True)
    text = (
        "<b>Твои действия сегодня</b>\n\n"
        f"{body}\n\n"
        "Оцени кнопкой ниже или напиши, например: <b>1A 2B 3D</b>"
    )
    return text, keyboards.start_keyboard()


# --- Text fallback ("1A 2B 3D") ------------------------------------------------

def apply_scores(
    session: Session, user_id: uuid.UUID, day: date, scores: dict[int, str]
) -> tuple[int, DailyReviewSession | None]:
    """Apply numbered scores against the latest session for the day.
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
