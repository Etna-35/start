import pytest

from app.services.duration_parser import parse_duration, parse_entry


@pytest.mark.parametrize(
    "text,expected",
    [
        ("20 минут говорил с поставщиком", 20),
        ("говорил с поставщиком 20 минут", 20),
        ("1 час разбирал финансы", 60),
        ("1 час 20 минут финансы", 80),
        ("1ч 20м финансы", 80),
        ("полчаса отдыхал", 30),
        ("полтора часа встреча", 90),
        ("час звонил", 60),
        ("20 мин разбирал", 20),
        ("20м разбирал", 20),
        ("10 минут ел", 10),
        ("ел 10 минут", 10),
        ("финансы без времени", None),
    ],
)
def test_parse_duration(text, expected):
    assert parse_duration(text) == expected


def test_parse_entry_strips_duration_from_action():
    parsed = parse_entry("20 минут говорил с поставщиком по мясу")
    assert parsed is not None
    assert parsed.duration_min == 20
    assert parsed.action_text == "говорил с поставщиком по мясу"


def test_parse_entry_action_when_duration_trailing():
    parsed = parse_entry("говорил с поставщиком 20 минут")
    assert parsed is not None
    assert parsed.action_text == "говорил с поставщиком"


def test_parse_entry_none_without_duration():
    assert parse_entry("просто текст без длительности") is None
