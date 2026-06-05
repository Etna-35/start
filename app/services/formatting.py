"""Helpers for MAX HTML message formatting.

All outgoing messages are sent with format="html". User-provided content
(action texts) MUST be escaped with ``esc`` before being embedded, so it can
never break the markup.
"""

from __future__ import annotations

# MAX HTML supports a small tag set (<b>, <i>, <a>, ...). For text content only
# the three structural characters need escaping (same rule as Telegram HTML).
def esc(text: str | None) -> str:
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
