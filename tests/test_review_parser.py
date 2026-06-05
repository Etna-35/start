import pytest

from app.services.review_parser import is_review_format, parse_review

EXPECTED = {1: "A", 2: "B", 3: "C"}
EXPECTED_ABD = {1: "A", 2: "B", 3: "D"}


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1A 2B 3C", EXPECTED),
        ("1 A, 2 B, 3 C", EXPECTED),
        ("1a 2b 3c", EXPECTED),
        ("1-А 2-Б 3-Д", EXPECTED_ABD),
        ("1а 2б 3д", EXPECTED_ABD),
        ("1A 2B 3D", EXPECTED_ABD),
    ],
)
def test_parse_review(text, expected):
    assert parse_review(text) == expected


@pytest.mark.parametrize(
    "text",
    ["1A 2B 3D", "1 A, 2 B, 3 C", "1-А 2-Б 3-Д", "1а 2б 3д", "1a"],
)
def test_is_review_format_true(text):
    assert is_review_format(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "20 минут говорил с поставщиком",
        "1 час разбирал финансы",
        "/today",
        "просто текст",
        "",
    ],
)
def test_is_review_format_false(text):
    assert is_review_format(text) is False


def test_later_token_overrides():
    assert parse_review("1A 1B") == {1: "B"}
