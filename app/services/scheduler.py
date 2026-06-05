"""Daily review scheduler.

Runs a lightweight tick every minute. For each consenting user it checks the
user's *local* time against DAILY_REVIEW_HOUR/MINUTE — this is how a single
process serves users across multiple timezones. A user is pinged at most once
per day because sending also creates a review session for that day (and /today
creates one too), which the tick checks for before sending.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import Settings, get_settings
from app.db import session_scope
from app.repositories import review_sessions as review_repo
from app.repositories import users as user_repo
from app.services import review_service
from app.services.clock import now_in, today_in
from app.services.max_client import MaxClient, get_max_client
from app.services.time_settings import effective_review_time

logger = logging.getLogger(__name__)


def run_daily_review_tick(
    settings: Settings | None = None, max_client: MaxClient | None = None
) -> int:
    """Send evening review prompts to users whose local time matches now.
    Returns the number of prompts sent (handy for tests/manual runs)."""
    settings = settings or get_settings()
    max_client = max_client or get_max_client()
    sent = 0

    with session_scope() as session:
        for user in user_repo.all_consented(session):
            local = now_in(user.timezone)
            hour, minute = effective_review_time(user, settings)
            if local.hour != hour or local.minute != minute:
                continue

            day = today_in(user.timezone)
            if review_repo.latest_for_day(session, user.id, day) is not None:
                continue  # already prompted (or used /today) today

            view = review_service.start_interactive(session, user.id, day)
            if view is None:
                continue  # nothing left to score — don't spam

            text, attachments = view
            if max_client.send_message(user.max_user_id, text, attachments=attachments):
                sent += 1

    if sent:
        logger.info("Daily review: sent %d prompts", sent)
    return sent


def build_scheduler(settings: Settings | None = None) -> BackgroundScheduler:
    settings = settings or get_settings()
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_daily_review_tick,
        trigger="cron",
        minute="*",
        id="daily_review_tick",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
