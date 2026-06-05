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
from app.services import keyboards, legend, messages
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


# --- Interactive paged scoring -------------------------------------------------

PAGE_SIZE = 10


def render_page(entries: list[TimeEntry], page: int) -> ReviewView:
    """Render a page of up to PAGE_SIZE actions: numbered list with ✅ marks,
    plus per-item A/B/C/D buttons, page navigation, and bulk options."""
    total = len(entries)
    max_page = max(0, (total - 1) // PAGE_SIZE) if total else 0
    page = max(0, min(page, max_page))
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_entries = entries[start:end]
    scored = sum(1 for e in entries if e.abc_score)

    lines = [f"<b>Оценка дня</b> · оценено {scored}/{total}", ""]
    for i, e in enumerate(page_entries):
        num = start + i + 1
        base = f"<b>{num}.</b> {format_minutes(e.duration_min)} — {esc(e.action_text)}"
        if e.abc_score:
            lines.append(f"✅ {base} · <b>{e.abc_score}</b>")
        else:
            lines.append(f"▫️ {base}")
    text = "\n".join(lines)

    rows: list[list[dict]] = []
    for i, e in enumerate(page_entries):
        num = start + i + 1
        eid = str(e.id)
        rows.append(
            [
                keyboards.button(f"{num}", "rv|x"),
                keyboards.button("A", f"rv|s|{eid}|A|{page}", "positive"),
                keyboards.button("B", f"rv|s|{eid}|B|{page}"),
                keyboards.button("C", f"rv|s|{eid}|C|{page}"),
                keyboards.button("D", f"rv|s|{eid}|D|{page}", "negative"),
            ]
        )
    nav: list[dict] = []
    if start > 0:
        nav.append(keyboards.button("◀ Пред. 10", f"rv|p|{page - 1}"))
    if end < total:
        nav.append(keyboards.button("След. 10 ▶", f"rv|p|{page + 1}"))
    nav.append(keyboards.button("✅ Завершить", "rv|done", "positive"))
    rows.append(nav)
    rows.append(
        [
            keyboards.button("Остальным B", "rv|b|B"),
            keyboards.button("Остальным C", "rv|b|C"),
            keyboards.button("Остальным D", "rv|b|D"),
        ]
    )

    attachments = keyboards.inline(rows)
    image = legend.legend_attachment()
    if image is not None:
        attachments = [image, *attachments]
    return text, attachments


def render_done(session: Session, user_id: uuid.UUID, day: date) -> ReviewView:
    """Scoring finished: show the day's summary and clear the keyboard ([])."""
    return build_day_summary_text(session, user_id, day), []


def begin_view(session: Session, user_id: uuid.UUID, day: date) -> ReviewView:
    """Manual start (button / command / text). Always returns a view."""
    entries = entry_repo.list_for_day(session, user_id, day)
    if not entries:
        return messages.NO_ENTRIES_TODAY, []
    review_repo.create(session, user_id, day, [str(e.id) for e in entries])
    if all(e.abc_score for e in entries):
        return render_done(session, user_id, day)
    return render_page(entries, 0)


def start_interactive(session: Session, user_id: uuid.UUID, day: date) -> ReviewView | None:
    """Scheduler start: None if nothing left to score (don't spam)."""
    entries = entry_repo.list_for_day(session, user_id, day)
    if not any(e.abc_score is None for e in entries):
        return None
    review_repo.create(session, user_id, day, [str(e.id) for e in entries])
    return render_page(entries, 0)


def render_page_view(session: Session, user_id: uuid.UUID, day: date, page: int) -> ReviewView:
    entries = entry_repo.list_for_day(session, user_id, day)
    if not entries:
        return render_done(session, user_id, day)
    return render_page(entries, page)


def after_score_view(session: Session, user_id: uuid.UUID, day: date, page: int) -> ReviewView:
    entries = entry_repo.list_for_day(session, user_id, day)
    if entries and all(e.abc_score for e in entries):
        return render_done(session, user_id, day)
    # Auto-advance when the current page is fully scored and more pages remain.
    total = len(entries)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_entries = entries[start:end]
    if page_entries and all(e.abc_score for e in page_entries) and end < total:
        page += 1
    return render_page(entries, page)


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
