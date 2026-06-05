"""MAX inline-keyboard builders for the interactive scoring flow.

Keyboard JSON shape (inside a message's ``attachments``):

    {"type": "inline_keyboard",
     "payload": {"buttons": [[ {"type":"callback","text":..,"payload":..,"intent":..}, ... ], ...]}}

Callback payloads use a compact pipe-delimited scheme:
    rv|start              start scoring
    rv|s|<entry_id>|A     score one entry
    rv|k|<entry_id>       skip one entry
    rv|b|B                set all remaining unscored entries to B
    rv|done               finish now and show the summary
    tm|22:00              set the evening review time
"""

from __future__ import annotations

RV = "rv"
TM = "tm"

# Quick presets offered in the first-entry message.
TIME_PRESETS = ["20:00", "21:00", "22:00", "23:00"]

FINISH_LABEL = "🌙 Завершить день и оценить"


def _cb(text: str, payload: str, intent: str = "default") -> dict:
    return {"type": "callback", "text": text, "payload": payload, "intent": intent}


def _keyboard(rows: list[list[dict]]) -> list:
    return [{"type": "inline_keyboard", "payload": {"buttons": rows}}]


# Public helpers for building custom keyboards (e.g. the paged scoring list).
def button(text: str, payload: str, intent: str = "default") -> dict:
    return _cb(text, payload, intent)


def inline(rows: list[list[dict]]) -> list:
    return _keyboard(rows)


def score_keyboard(entry_id: str) -> list:
    return _keyboard(
        [
            [
                _cb("A", f"{RV}|s|{entry_id}|A", "positive"),
                _cb("B", f"{RV}|s|{entry_id}|B"),
                _cb("C", f"{RV}|s|{entry_id}|C"),
                _cb("D", f"{RV}|s|{entry_id}|D", "negative"),
            ],
            [
                _cb("⏭ Пропустить", f"{RV}|k|{entry_id}"),
                _cb("✅ Завершить", f"{RV}|done", "positive"),
            ],
            [
                _cb("Остальное B", f"{RV}|b|B"),
                _cb("Остальное C", f"{RV}|b|C"),
                _cb("Остальное D", f"{RV}|b|D"),
            ],
        ]
    )


def start_keyboard() -> list:
    return _keyboard([[_cb("▶️ Оценить по одному", f"{RV}|start", "positive")]])


def finish_keyboard() -> list:
    """Single 'finish the day early' button — attached to entry acknowledgements."""
    return _keyboard([[_cb(FINISH_LABEL, f"{RV}|start", "positive")]])


def time_and_finish_keyboard() -> list:
    """Time presets + the finish button — attached to the first entry of the day."""
    return _keyboard(
        [
            [_cb(t, f"{TM}|{t}") for t in TIME_PRESETS],
            [_cb(FINISH_LABEL, f"{RV}|start", "positive")],
        ]
    )


def parse_callback(payload: str) -> list[str] | None:
    """Return the payload parts for a known callback namespace, else None."""
    parts = (payload or "").split("|")
    if len(parts) < 2 or parts[0] not in (RV, TM):
        return None
    return parts
