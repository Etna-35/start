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


@dataclass(frozen=True)
class CallbackQuery:
    """Normalized inline-button press (message_callback update)."""

    max_user_id: str
    payload: str
    callback_id: str
    display_name: str | None = None


@dataclass
class Reply:
    """A handler reply that may carry an inline keyboard (attachments)."""

    text: str
    attachments: list | None = None


@dataclass
class CallbackResult:
    """Result of an inline-button press.

    - ``view`` = (text, attachments) → edit the original message in place.
    - ``notification`` → show a transient toast, leave the message unchanged.
    - ``silent`` → just acknowledge the press (no edit, no toast).
    """

    view: tuple | None = None
    notification: str | None = None
    silent: bool = False
