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
    idempotency_ttl_seconds: int
    max_agent_retries: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "dev"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            azure_subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID") or None,
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL") or None,
            idempotency_ttl_seconds=_parse_int_env(
                "IDEMPOTENCY_TTL_SECONDS",
                default=600,
                minimum=1,
            ),
            max_agent_retries=_parse_int_env(
                "MAX_AGENT_RETRIES",
                default=1,
                minimum=0,
            ),
        )


def _parse_int_env(name: str, *, default: int, minimum: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except ValueError:
        return default

    if parsed < minimum:
        return minimum
    return parsed


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
