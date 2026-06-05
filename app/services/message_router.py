"""Central dispatch: takes a raw MAX update, figures out intent, mutates the DB,
and sends the reply back. Never raises on bad input."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.handlers import callbacks as callback_handler
from app.handlers import commands as command_handler
from app.handlers import reviews as review_handler
from app.handlers import text_entries as entry_handler
from app.repositories import time_entries as entry_repo
from app.repositories import users as user_repo
from app.schemas.dto import CallbackQuery, IncomingMessage, Reply
from app.schemas.max_update import extract_callback, extract_message
from app.services import messages, review_service
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

    callback = extract_callback(update)
    if callback is not None:
        _handle_callback(session, callback, max_client, settings)
        return

    incoming = extract_message(update)
    if incoming is None:
        logger.debug("Ignoring non-text / unsupported update")
        return

    try:
        reply = _route(session, incoming, settings)
    except Exception:  # one bad message must never take down the webhook
        logger.exception("Error handling message from %s", incoming.max_user_id)
        reply = "Что-то пошло не так. Попробуй еще раз чуть позже."

    _send(max_client, incoming.max_user_id, reply)


def _send(max_client: MaxClient, user_id: str, reply: str | Reply | None) -> None:
    if not reply:
        return
    if isinstance(reply, Reply):
        max_client.send_message(user_id, reply.text, attachments=reply.attachments)
    else:
        max_client.send_message(user_id, reply)


def _handle_callback(
    session: Session, cb: CallbackQuery, max_client: MaxClient, settings: Settings
) -> None:
    try:
        user = user_repo.get_or_create(
            session,
            max_user_id=cb.max_user_id,
            display_name=cb.display_name,
            admin_ids=settings.admin_max_user_ids,
            default_tz=settings.default_timezone,
        )
        day = today_in(user.timezone)
        result = callback_handler.handle_callback(session, user, cb.payload, day, settings)
    except Exception:
        logger.exception("Error handling callback from %s", cb.max_user_id)
        result = None

    if result is None:
        max_client.answer_callback(
            cb.callback_id,
            notification="Не понял действие. Обнови список командой /today.",
        )
    elif result.view is not None:
        text, attachments = result.view
        max_client.answer_callback(cb.callback_id, text=text, attachments=attachments)
    elif result.notification:
        max_client.answer_callback(cb.callback_id, notification=result.notification)
    else:
        max_client.answer_callback(cb.callback_id, notification="Готово")


def _route(session: Session, incoming: IncomingMessage, settings: Settings) -> str | Reply:
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
        user_repo.hard_delete(session, user)
        return messages.DELETED_ME

    if text.startswith("/"):
        return command_handler.handle_command(session, user, text, settings, day)

    # Plain-text help triggers (work even before consent).
    if text.lower() in messages.HELP_ALIASES:
        return messages.HELP

    if not user.consent_accepted:
        return messages.NEED_CONSENT

    # Plain-text "finish the day early" triggers.
    if text.lower() in messages.FINISH_ALIASES:
        view = review_service.start_interactive(session, user.id, day)
        if view is None:
            return review_service.build_day_summary_text(session, user.id, day)
        return Reply(*view)

    if is_review_format(text):
        return review_handler.handle_review(session, user, text, day)

    return entry_handler.handle_entry(session, user, text, day, settings)
