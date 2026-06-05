"""A/B/C/D legend image, uploaded to MAX once at startup and reused by token.

If the image file is missing or the upload fails, the hint is silently
disabled — scoring still works, just without the picture.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_token: str | None = None


def load_legend(max_client, image_path: str) -> None:
    """Upload the legend image once and cache its token."""
    global _token
    if not image_path or not os.path.exists(image_path):
        logger.info("Legend image not found (%s) — image hint disabled", image_path)
        return
    token = max_client.upload_image(image_path)
    if token:
        _token = token
        logger.info("Legend image uploaded to MAX")
    else:
        logger.warning("Legend image upload failed — image hint disabled")


def legend_attachment() -> dict | None:
    """The image attachment to prepend to a scoring message, or None."""
    if _token:
        return {"type": "image", "payload": {"token": _token}}
    return None
