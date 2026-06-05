"""Rule-based parser that extracts a duration (in minutes) and the action text
from a free-form Russian message. No LLM, no external calls."""

from __future__ import annotations

import re
from dataclasses import dataclass

# (pattern, minutes-from-match). Order matters: word-forms first, then numbered
# hours, then numbered minutes. Each matched span is masked so it is neither
# double-counted nor left in the action text.
_PATTERNS: list[tuple[str, "callable"]] = [
    (r"полтора\s+час(?:ов|а)?", lambda m: 90),
    (r"полчаса", lambda m: 30),
    (r"(\d+)\s*(?:час(?:ов|а)?|ч)\b", lambda m: int(m.group(1)) * 60),
    (r"(\d+)\s*(?:минут[ыау]?|мин|м)\b", lambda m: int(m.group(1))),
]

# Standalone "час"/"часа" with no leading number → 60 minutes.
_STANDALONE_HOUR = r"\bчас(?:ов|а)?\b"

_TRIM = r"^[\s,;.:\-–—]+|[\s,;.:\-–—]+$"


@dataclass(frozen=True)
class ParsedEntry:
    duration_min: int
    action_text: str


def _mask(text: str, start: int, end: int) -> str:
    return text[:start] + " " * (end - start) + text[end:]


def _extract(text: str) -> tuple[int | None, str]:
    lowered = text.lower()
    masked = lowered
    total = 0
    found = False
    spans: list[tuple[int, int]] = []

    for pattern, minutes_fn in _PATTERNS:
        for m in re.finditer(pattern, masked):
            total += minutes_fn(m)
            found = True
            spans.append(m.span())
        # Mask in place so later patterns can't re-match the same characters.
        for m in list(re.finditer(pattern, masked)):
            masked = _mask(masked, *m.span())

    for m in re.finditer(_STANDALONE_HOUR, masked):
        total += 60
        found = True
        spans.append(m.span())
        masked = _mask(masked, *m.span())

    if not found:
        return None, ""

    action = _build_action(text, spans)
    return total, action


def _build_action(original: str, spans: list[tuple[int, int]]) -> str:
    spans = sorted(spans)
    parts: list[str] = []
    prev = 0
    for start, end in spans:
        parts.append(original[prev:start])
        prev = end
    parts.append(original[prev:])
    action = " ".join("".join(parts).split())
    action = re.sub(_TRIM, "", action)
    return action.strip()


def parse_duration(text: str) -> int | None:
    """Return the duration in minutes, or None if no duration is found."""
    minutes, _ = _extract(text or "")
    return minutes


def parse_entry(text: str) -> ParsedEntry | None:
    """Return a ParsedEntry (duration + action text) or None if no duration."""
    minutes, action = _extract(text or "")
    if minutes is None:
        return None
    return ParsedEntry(duration_min=minutes, action_text=action or text.strip())
