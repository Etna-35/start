"""A/B/C/D legend image, uploaded to MAX once at startup and reused by token.

If the image file is missing or the upload fails, the hint is silently
disabled — scoring still works, just without the picture.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_payload: dict | None = None


def load_legend(max_client, image_path: str) -> None:
    """Upload the legend image once and cache its attachment payload."""
    global _payload
    if not image_path or not os.path.exists(image_path):
        logger.info("Legend image not found (%s) — image hint disabled", image_path)
        return
    payload = max_client.upload_image(image_path)
    if payload:
        _payload = payload
        logger.info("Legend image uploaded to MAX")
    else:
        logger.warning("Legend image upload failed — image hint disabled")


def legend_attachment() -> dict | None:
    """The image attachment to prepend to a scoring message, or None."""
    if _payload:
        return {"type": "image", "payload": _payload}
    return None
