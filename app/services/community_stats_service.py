"""Anonymized, aggregated community statistics. Never includes action texts,
names, or per-user breakdowns."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.services.summary_service import SCORES, EntryStat, build_summary
from app.services.timefmt import format_minutes


@dataclass
class CommunityStats:
    active_users: int
    total_entries: int
    total_min: int
    avg_percent_by_score: dict[str, int]


def aggregate(per_user_entries: dict[str, list[EntryStat]]) -> CommunityStats:
    """Aggregate across users.

    ``per_user_entries`` maps an opaque user key -> that user's entries for the
    day. The keys are only used for counting/averaging and never surfaced.
    """
    active_users = 0
    total_entries = 0
    total_min = 0
    pct_accumulator = {s: 0 for s in SCORES}
    rated_users = 0

    for entries in per_user_entries.values():
        if not entries:
            continue
        active_users += 1
        summary = build_summary(entries)
        total_entries += summary.entries_count
        total_min += summary.total_min
        # Only users who have at least one scored entry contribute to averages.
        if any(e.abc_score for e in entries):
            rated_users += 1
            for s in SCORES:
                pct_accumulator[s] += summary.percent_by_score[s]

    avg = {
        s: round(pct_accumulator[s] / rated_users) if rated_users else 0 for s in SCORES
    }
    return CommunityStats(
        active_users=active_users,
        total_entries=total_entries,
        total_min=total_min,
        avg_percent_by_score=avg,
    )


def format_community_stats(stats: CommunityStats) -> str:
    lines = [
        "<b>Статистика сообщества сегодня</b>",
        "",
        f"Активных участников: <b>{stats.active_users}</b>",
        f"Всего записей: <b>{stats.total_entries}</b>",
        f"Общее зафиксированное время: <b>{format_minutes(stats.total_min)}</b>",
        "",
        "<b>Средняя структура дня</b>",
    ]
    for s in SCORES:
        lines.append(f"<b>{s}</b> — {stats.avg_percent_by_score[s]}%")
    lines.append("")
    lines.append("<i>Данные обезличены. Конкретные действия участников не показываются.</i>")
    return "\n".join(lines)
