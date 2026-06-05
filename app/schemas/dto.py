from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomingMessage:
    """Normalized inbound message, independent of the raw MAX payload shape."""

    max_user_id: str
    text: str
    display_name: str | None = None
    chat_id: int | str | None = None
    update_type: str | None = None
