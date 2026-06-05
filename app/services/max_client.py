"""Thin, isolated client for the MAX Bot API.

Kept free of business logic so it can be mocked/tested on its own.

Auth: the current MAX Bot API expects the bot token in the ``Authorization``
header (raw token, NOT ``Bearer <token>``). The legacy ``access_token`` query
parameter is deprecated.
"""

from __future__ import annotations

import logging

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class MaxClient:
    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None):
        self._settings = settings or get_settings()
        headers = {}
        if self._settings.max_bot_token:
            headers["Authorization"] = self._settings.max_bot_token
        self._client = client or httpx.Client(
            base_url=self._settings.max_api_base_url, timeout=10.0, headers=headers
        )

    def get_me(self) -> dict | None:
        """Return the bot's own profile (handy for verifying the token)."""
        try:
            response = self._client.get("/me")
            if response.status_code >= 400:
                logger.error("MAX get_me failed: %s %s", response.status_code, response.text)
                return None
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("MAX get_me error: %s", exc)
            return None

    def send_message(self, user_id: str | int, text: str, fmt: str | None = "html") -> bool:
        """Send a text message to a user. Returns True on success.

        MAX: POST /messages?user_id=<id> with JSON body {"text": "...",
        "format": "html"}, token in the Authorization header.
        """
        body: dict = {"text": text}
        if fmt:
            body["format"] = fmt
        try:
            response = self._client.post(
                "/messages",
                params={"user_id": str(user_id)},
                json=body,
            )
            if response.status_code >= 400:
                logger.error("MAX send_message failed: %s %s", response.status_code, response.text)
                return False
            return True
        except httpx.HTTPError as exc:  # never let MAX I/O crash a handler
            logger.exception("MAX send_message error: %s", exc)
            return False

    def set_webhook(self, url: str, secret: str | None = None) -> bool:
        """Register the webhook URL with MAX (subscriptions endpoint).

        If ``secret`` is provided, MAX will echo it back on each delivery in the
        ``X-Max-Bot-Api-Secret`` header so we can verify the source.
        """
        body: dict = {"url": url}
        if secret:
            body["secret"] = secret
        try:
            response = self._client.post("/subscriptions", json=body)
            if response.status_code >= 400:
                logger.error("MAX set_webhook failed: %s %s", response.status_code, response.text)
                return False
            return True
        except httpx.HTTPError as exc:
            logger.exception("MAX set_webhook error: %s", exc)
            return False

    def close(self) -> None:
        self._client.close()


_default_client: MaxClient | None = None


def get_max_client() -> MaxClient:
    global _default_client
    if _default_client is None:
        _default_client = MaxClient()
    return _default_client
