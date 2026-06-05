"""Privacy guarantees: anonymized aggregates never leak action texts, and
export only ever returns one user's own data."""

from dataclasses import dataclass
from datetime import date

from app.services.community_stats_service import aggregate, format_community_stats
from app.services.privacy_service import (
    AdminStats,
    ExportEntry,
    build_export,
    filter_user_entries,
    format_admin_stats,
)
from app.services.summary_service import EntryStat

SECRET_TEXT = "секретный разговор с поставщиком про мясо"


def test_community_stats_has_no_action_text():
    per_user = {
        "u1": [EntryStat(duration_min=60, abc_score="A"), EntryStat(60, "B")],
        "u2": [EntryStat(duration_min=30, abc_score="C")],
    }
    stats = aggregate(per_user)
    rendered = format_community_stats(stats)

    assert stats.active_users == 2
    assert stats.total_entries == 3
    assert SECRET_TEXT not in rendered
    # No raw action text concept exists in the community pipeline at all.
    assert "поставщик" not in rendered.lower()


def test_admin_stats_has_no_action_text():
    stats = AdminStats(
        total_users=50,
        consented_users=37,
        active_today=12,
        entries_today=84,
        scored_entries_today=60,
        parse_errors_today=3,
    )
    rendered = format_admin_stats(stats)
    assert SECRET_TEXT not in rendered
    assert "поставщик" not in rendered.lower()


@dataclass
class _Row:
    user_id: str
    entry_date: date
    duration_min: int
    abc_score: str | None
    action_text: str


def test_export_returns_only_target_user_data():
    rows = [
        _Row("me", date(2026, 6, 4), 20, "B", "мои финансы"),
        _Row("other", date(2026, 6, 4), 30, "A", SECRET_TEXT),
        _Row("me", date(2026, 6, 3), 45, "A", "мои переговоры"),
    ]
    mine = filter_user_entries(rows, "me")
    assert len(mine) == 2
    assert all(r.user_id == "me" for r in mine)

    export = build_export(
        [
            ExportEntry(
                entry_date=r.entry_date,
                duration_min=r.duration_min,
                abc_score=r.abc_score,
                action_text=r.action_text,
            )
            for r in mine
        ]
    )
    assert "мои финансы" in export
    assert "мои переговоры" in export
    assert SECRET_TEXT not in export


def test_export_empty():
    assert build_export([]) == "За последние 7 дней нет записей."
