"""Pure logic for a single user's daily summary (minutes, percentages, verdict)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from app.services.timefmt import format_minutes

SCORES = ("A", "B", "C", "D")


@dataclass
class EntryStat:
    """Minimal view of a time entry needed for summaries (no action text)."""

    duration_min: int
    abc_score: str | None


@dataclass
class DailySummary:
    total_min: int
    entries_count: int
    unscored_count: int
    minutes_by_score: dict[str, int]
    percent_by_score: dict[str, int]
    conclusion: str = ""
    conclusion_lines: list[str] = field(default_factory=list)


def build_summary(entries: Iterable[EntryStat]) -> DailySummary:
    entries = list(entries)
    minutes_by_score = {s: 0 for s in SCORES}
    total_min = 0
    unscored = 0
    scored_total = 0

    for e in entries:
        total_min += e.duration_min
        score = (e.abc_score or "").upper()
        if score in minutes_by_score:
            minutes_by_score[score] += e.duration_min
            scored_total += e.duration_min
        else:
            unscored += 1

    # Percentages are computed against scored minutes (the structure of rated time).
    base = scored_total if scored_total > 0 else 0
    percent_by_score = {
        s: round(minutes_by_score[s] / base * 100) if base else 0 for s in SCORES
    }

    lines = _build_conclusion(total_min, percent_by_score)
    return DailySummary(
        total_min=total_min,
        entries_count=len(entries),
        unscored_count=unscored,
        minutes_by_score=minutes_by_score,
        percent_by_score=percent_by_score,
        conclusion=" ".join(lines),
        conclusion_lines=lines,
    )


def _build_conclusion(total_min: int, pct: dict[str, int]) -> list[str]:
    lines: list[str] = []
    if total_min < 120:
        lines.append("Мало данных для надежного вывода.")

    a = pct["A"]
    if a >= 40:
        lines.append("Сильный день: высокая доля задач уровня собственника.")
    elif a >= 20:
        lines.append("Нормальный день, но есть потенциал увеличить долю A-задач.")
    else:
        lines.append("День занятой, но мало времени ушло на задачи уровня собственника.")

    if pct["C"] > 35:
        lines.append("Много операционки, часть задач стоит делегировать или регламентировать.")
    if pct["D"] > 15:
        lines.append("Заметная доля времени ушла на отвлечения.")
    return lines


def format_summary(summary: DailySummary) -> str:
    lines = ["Итог дня:", "", f"Всего зафиксировано: {format_minutes(summary.total_min)}", ""]
    for s in SCORES:
        mins = format_minutes(summary.minutes_by_score[s])
        lines.append(f"{s} - {mins} / {summary.percent_by_score[s]}%")
    lines.append("")
    if summary.unscored_count:
        lines.append(f"Без оценки: {summary.unscored_count} — оцени их, чтобы итог был точнее.")
        lines.append("")
    lines.append("Вывод:")
    lines.append(summary.conclusion or "Пока нет данных за день.")
    return "\n".join(lines)
