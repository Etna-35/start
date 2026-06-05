"""Parser for A/B/C/D scoring replies like '1A 2B 3D' or '1-А 2-Б 3-Д'."""

from __future__ import annotations

import re

# Cyrillic look-alikes / phonetic equivalents → canonical Latin score.
_SCORE_MAP = {
    "a": "A",
    "b": "B",
    "c": "C",
    "d": "D",
    "а": "A",  # Cyrillic a
    "б": "B",  # Cyrillic be
    "в": "B",  # Cyrillic ve (looks like Latin B)
    "с": "C",  # Cyrillic es (looks like Latin C)
    "д": "D",  # Cyrillic de
}

_LETTERS = "abcdабвсд"
_TOKEN = rf"(\d+)\s*[-–—.)]?\s*([{_LETTERS}])"
# Whole message must be only score tokens (separated by spaces/commas) to count.
_FULL = rf"^\s*(?:{_TOKEN}\s*[,;]?\s*)+$"


def is_review_format(text: str) -> bool:
    """True only if the entire message is a list of score tokens."""
    if not text:
        return False
    return re.fullmatch(_FULL, text.strip().lower()) is not None


def parse_review(text: str) -> dict[int, str]:
    """Map item numbers to canonical scores. Returns {} if nothing parses.

    A later token for the same number overrides an earlier one.
    """
    result: dict[int, str] = {}
    if not text:
        return result
    for m in re.finditer(_TOKEN, text.lower()):
        number = int(m.group(1))
        score = _SCORE_MAP.get(m.group(2))
        if score:
            result[number] = score
    return result
