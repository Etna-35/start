from dataclasses import dataclass

import pytest

from app.services.time_settings import (
    effective_review_time,
    format_hhmm,
    parse_review_time,
)


@pytest.mark.parametrize(
    "arg,expected",
    [
        ("21:30", (21, 30)),
        ("21.30", (21, 30)),
        ("21 30", (21, 30)),
        ("9:05", (9, 5)),
        ("21", (21, 0)),
        ("0:0", (0, 0)),
        ("23:59", (23, 59)),
    ],
)
def test_parse_review_time_valid(arg, expected):
    assert parse_review_time(arg) == expected


@pytest.mark.parametrize("arg", ["", "24:00", "21:60", "25", "abc", "-1:00", "12:ab"])
def test_parse_review_time_invalid(arg):
    assert parse_review_time(arg) is None


@dataclass
class _User:
    review_hour: int | None = None
    review_minute: int | None = None


@dataclass
class _Settings:
    daily_review_hour: int = 22
    daily_review_minute: int = 30


def test_effective_review_time_falls_back_to_default():
    assert effective_review_time(_User(), _Settings()) == (22, 30)


def test_effective_review_time_uses_user_value():
    assert effective_review_time(_User(21, 0), _Settings()) == (21, 0)


def test_format_hhmm():
    assert format_hhmm(9, 5) == "09:05"
    assert format_hhmm(21, 30) == "21:30"
