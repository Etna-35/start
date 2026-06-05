from app.services.summary_service import EntryStat, build_summary, format_summary


def _entries(pairs):
    return [EntryStat(duration_min=m, abc_score=s) for m, s in pairs]


def test_minutes_and_percentages():
    # 35A, 80B, 80C, 10D => 205 scored minutes.
    summary = build_summary(
        _entries([(35, "A"), (80, "B"), (80, "C"), (10, "D")])
    )
    assert summary.total_min == 205
    assert summary.minutes_by_score == {"A": 35, "B": 80, "C": 80, "D": 10}
    assert summary.percent_by_score["A"] == 17
    assert summary.percent_by_score["B"] == 39
    assert summary.percent_by_score["C"] == 39
    assert summary.percent_by_score["D"] == 5
    assert summary.entries_count == 4
    assert summary.unscored_count == 0


def test_unscored_counted_in_total_not_in_percentages():
    summary = build_summary(_entries([(60, "A"), (60, None)]))
    assert summary.total_min == 120
    assert summary.unscored_count == 1
    # Percentages are over scored minutes only (60 min, all A).
    assert summary.percent_by_score["A"] == 100


def test_conclusion_low_a():
    summary = build_summary(_entries([(10, "A"), (200, "B")]))
    assert summary.percent_by_score["A"] < 20
    assert "мало времени ушло на задачи уровня собственника" in summary.conclusion


def test_conclusion_high_c():
    summary = build_summary(_entries([(50, "A"), (50, "B"), (100, "C")]))
    assert summary.percent_by_score["C"] > 35
    assert "Много операционки" in summary.conclusion


def test_conclusion_high_d():
    summary = build_summary(_entries([(100, "A"), (100, "B"), (50, "D")]))
    assert summary.percent_by_score["D"] > 15
    assert "Заметная доля времени ушла на отвлечения" in summary.conclusion


def test_conclusion_strong_day():
    summary = build_summary(_entries([(120, "A"), (60, "B")]))
    assert summary.percent_by_score["A"] >= 40
    assert "Сильный день" in summary.conclusion


def test_conclusion_low_data():
    summary = build_summary(_entries([(30, "A")]))
    assert summary.total_min < 120
    assert "Мало данных" in summary.conclusion


def test_format_summary_contains_sections():
    text = format_summary(build_summary(_entries([(35, "A"), (80, "B")])))
    assert "Итог дня:" in text
    assert "Всего зафиксировано:" in text
    assert "Вывод:" in text
