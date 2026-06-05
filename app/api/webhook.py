from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

from app.config import get_settings
from app.db import session_scope
from app.services.message_router import handle_update

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook/max")
async def max_webhook(request: Request) -> Response:
    """Receive an Update from MAX.

    - validates the optional shared secret;
    - always returns 200 quickly so MAX does not retry;
    - never crashes on a single malformed payload.
    """
    settings = get_settings()

    if settings.max_webhook_secret:
        provided = request.headers.get(settings.webhook_secret_header)
        if provided != settings.max_webhook_secret:
            logger.warning("Webhook rejected: bad or missing secret")
            return Response(status_code=403)

    try:
        update = await request.json()
    except Exception:
        logger.warning("Webhook received non-JSON body")
        return Response(status_code=200)  # ack anyway, nothing to do

    try:
        with session_scope() as session:
            handle_update(update, session)
    except Exception:
        # Processing is best-effort in MVP; log and still ack.
        logger.exception("Unhandled error processing webhook update")

    return Response(status_code=200)
