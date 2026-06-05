from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.services import messages, review_service
from app.services.review_parser import parse_review


def handle_review(session: Session, user: User, raw_text: str, day: date) -> str:
    scores = parse_review(raw_text)
    if not scores:
        return messages.REVIEW_NO_SESSION

    applied, _ = review_service.apply_scores(session, user.id, day, scores)
    if applied == -1:
        return messages.REVIEW_NO_SESSION
    if applied == 0:
        return (
            "Не получилось сопоставить оценки с действиями. "
            "Запроси список командой /today и попробуй снова."
        )

    summary = review_service.build_day_summary_text(session, user.id, day)
    return f"Принял оценки: <b>{applied}</b>.\n\n{summary}"
