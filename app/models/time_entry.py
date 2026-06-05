from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

VALID_SCORES = ("A", "B", "C", "D")


class TimeEntry(Base, TimestampMixin):
    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Categories were removed from the product; column kept nullable for history.
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    abc_score: Mapped[str | None] = mapped_column(String(1), nullable=True)
    source: Mapped[str] = mapped_column(String(16), default="text", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="entries")
