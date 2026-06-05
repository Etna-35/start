"""Extraction of a normalized message from a raw MAX Bot API Update.

NOTE FOR INTEGRATION: This follows the MAX / TamTam-style webhook shape:

    {
      "update_type": "message_created",
      "timestamp": 1700000000000,
      "message": {
        "sender":    {"user_id": 123, "name": "Иван", "username": "ivan"},
        "recipient": {"chat_id": 456, "chat_type": "dialog", "user_id": 789},
        "body":      {"mid": "...", "seq": 1, "text": "20 минут финансы"}
      }
    }

If the live MAX schema differs, this is the ONLY place that needs adapting:
adjust the key paths below. The rest of the app consumes ``IncomingMessage``.
"""

from __future__ import annotations

import logging

from app.schemas.dto import IncomingMessage

logger = logging.getLogger(__name__)

# Update types that carry user text we should react to.
_MESSAGE_UPDATE_TYPES = {"message_created", "message_edited"}
# A user opening the bot — treated like /start downstream.
_BOT_STARTED_TYPES = {"bot_started"}


def extract_message(update: dict) -> IncomingMessage | None:
    """Return a normalized IncomingMessage, or None if the update is not a
    text message we handle. Never raises on malformed input."""
    if not isinstance(update, dict):
        return None

    update_type = update.get("update_type")

    if update_type in _BOT_STARTED_TYPES:
        user_id = _safe_str(update.get("user_id") or _dig(update, "user", "user_id"))
        if not user_id:
            return None
        name = _dig(update, "user", "name")
        return IncomingMessage(
            max_user_id=user_id, text="/start", display_name=name, update_type=update_type
        )

    if update_type is not None and update_type not in _MESSAGE_UPDATE_TYPES:
        # Callbacks, chat membership changes, etc. — ignored in MVP.
        return None

    message = update.get("message") or {}
    sender = message.get("sender") or {}
    body = message.get("body") or {}
    recipient = message.get("recipient") or {}

    user_id = _safe_str(sender.get("user_id"))
    text = body.get("text")
    if not user_id or not isinstance(text, str) or not text.strip():
        return None

    return IncomingMessage(
        max_user_id=user_id,
        text=text.strip(),
        display_name=sender.get("name"),
        chat_id=recipient.get("chat_id"),
        update_type=update_type or "message_created",
    )


def _safe_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _dig(data: dict, *keys: str):
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
