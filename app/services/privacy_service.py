"""Privacy boundary helpers.

The core privacy guarantees of the product are enforced here:
- community stats and admin stats never carry action texts;
- export only ever returns a single user's own data.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from app.services.formatting import esc
from app.services.timefmt import format_minutes


@dataclass
class ExportEntry:
    """A user-facing export row. ``action_text`` is shown ONLY to its owner."""

    entry_date: date
    duration_min: int
    abc_score: str | None
    action_text: str


@dataclass
class AdminStats:
    total_users: int
    consented_users: int
    active_today: int
    entries_today: int
    scored_entries_today: int
    parse_errors_today: int


def filter_user_entries(entries: Iterable, user_id) -> list:
    """Return only the entries that belong to ``user_id``.

    Used by export so one user can never receive another user's rows.
    """
    return [e for e in entries if getattr(e, "user_id", None) == user_id]


def build_export(entries: Iterable[ExportEntry], max_rows: int = 200) -> str:
    entries = sorted(entries, key=lambda e: (e.entry_date, e.duration_min), reverse=True)
    if not entries:
        return "За последние 7 дней нет записей."

    truncated = entries[:max_rows]
    by_date: dict[date, list[ExportEntry]] = {}
    for e in truncated:
        by_date.setdefault(e.entry_date, []).append(e)

    blocks: list[str] = ["<b>Экспорт за последние 7 дней</b>", ""]
    for day in sorted(by_date.keys(), reverse=True):
        blocks.append(f"<b>{day.strftime('%Y-%m-%d')}</b>")
        for e in by_date[day]:
            score = e.abc_score or "—"
            blocks.append(f"• {format_minutes(e.duration_min)} | {score} | {esc(e.action_text)}")
        blocks.append("")

    if len(entries) > max_rows:
        blocks.append(
            f"<i>Показаны последние {max_rows} записей. Полный CSV-экспорт добавим позже.</i>"
        )
    return "\n".join(blocks).strip()


def format_admin_stats(stats: AdminStats) -> str:
    """Admin-facing aggregate. Deliberately contains NO action texts or names."""
    return "\n".join(
        [
            "<b>Админ-статистика на сегодня</b>",
            "",
            f"Всего пользователей: <b>{stats.total_users}</b>",
            f"С согласием: <b>{stats.consented_users}</b>",
            f"Активных сегодня: <b>{stats.active_today}</b>",
            f"Записей сегодня: <b>{stats.entries_today}</b>",
            f"Оцененных записей сегодня: <b>{stats.scored_entries_today}</b>",
            f"Ошибок парсинга сегодня: <b>{stats.parse_errors_today}</b>",
        ]
    )
