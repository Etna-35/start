from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg2://chrono:chrono@localhost:5432/chrono"

    # MAX Bot API
    max_bot_token: str = ""
    max_webhook_secret: str = ""
    webhook_secret_header: str = "X-Max-Bot-Api-Secret"
    max_api_base_url: str = "https://botapi.max.ru"

    # App
    app_env: str = "local"
    log_level: str = "INFO"
    default_timezone: str = "Europe/Moscow"

    # Path to the A/B/C/D legend image shown at the start of scoring.
    # If the file is absent, the image hint is silently disabled.
    legend_image_path: str = "assets/legend.png"

    # Daily review schedule (interpreted in each user's local timezone)
    daily_review_hour: int = 22
    daily_review_minute: int = 30
    scheduler_enabled: bool = True

    # Admins. NoDecode disables pydantic-settings' default JSON parsing for this
    # list field so an empty / CSV env value is handed to the validator as-is.
    admin_max_user_ids: Annotated[list[str], NoDecode] = []

    @field_validator("admin_max_user_ids", mode="before")
    @classmethod
    def _split_admin_ids(cls, value: object) -> object:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
