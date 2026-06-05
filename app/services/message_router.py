"""Central dispatch: takes a raw MAX update, figures out intent, mutates the DB,
and returns the text reply to send back. Never raises on bad input."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.handlers import commands as command_handler
from app.handlers import reviews as review_handler
from app.handlers import text_entries as entry_handler
from app.repositories import time_entries as entry_repo
from app.repositories import users as user_repo
from app.schemas.dto import IncomingMessage
from app.schemas.max_update import extract_message
from app.services import messages
from app.services.clock import today_in
from app.services.max_client import MaxClient, get_max_client
from app.services.review_parser import is_review_format

logger = logging.getLogger(__name__)


def handle_update(
    update: dict,
    session: Session,
    max_client: MaxClient | None = None,
    settings: Settings | None = None,
) -> None:
    """Process one MAX update end to end. Sends the reply via MAX."""
    settings = settings or get_settings()
    max_client = max_client or get_max_client()

    incoming = extract_message(update)
    if incoming is None:
        logger.debug("Ignoring non-text / unsupported update")
        return

    try:
        reply = _route(session, incoming, settings)
    except Exception:  # one bad message must never take down the webhook
        logger.exception("Error handling message from %s", incoming.max_user_id)
        reply = "Что-то пошло не так. Попробуй еще раз чуть позже."

    if reply:
        max_client.send_message(incoming.max_user_id, reply)


def _route(session: Session, incoming: IncomingMessage, settings: Settings) -> str:
    user = user_repo.get_or_create(
        session,
        max_user_id=incoming.max_user_id,
        display_name=incoming.display_name,
        admin_ids=settings.admin_max_user_ids,
        default_tz=settings.default_timezone,
    )
    day = today_in(user.timezone)
    text = incoming.text.strip()

    # Exact destructive-confirmation phrases (explicit by design).
    if text == messages.CONFIRM_PHRASE_TODAY:
        entry_repo.soft_delete_for_day(session, user.id, day)
        return messages.DELETED_TODAY
    if text == messages.CONFIRM_PHRASE_ME:
        user_repo.soft_delete(session, user)
        return messages.DELETED_ME

    if text.startswith("/"):
        return command_handler.handle_command(session, user, text, settings, day)

    # Plain-text help triggers (work even before consent).
    if text.lower() in messages.HELP_ALIASES:
        return messages.HELP

    if not user.consent_accepted:
        return messages.NEED_CONSENT

    if is_review_format(text):
        return review_handler.handle_review(session, user, text, day)

    return entry_handler.handle_entry(session, user, text, day, settings)
