from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health, webhook
from app.config import get_settings
from app.logging_config import configure_logging
from app.services.scheduler import build_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()

    scheduler = None
    if settings.scheduler_enabled:
        scheduler = build_scheduler(settings)
        scheduler.start()
        logger.info("Daily review scheduler started")

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(title="MAX Chrono Bot", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(webhook.router)
