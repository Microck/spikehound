from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv(override=False)


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str

    azure_subscription_id: str | None
    slack_webhook_url: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "dev"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            azure_subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID") or None,
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL") or None,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
