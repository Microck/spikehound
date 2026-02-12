from __future__ import annotations

import logging
import os
from typing import Any

import httpx


logger = logging.getLogger("incident-war-room.integrations.discord")


def send_discord_webhook(payload: dict[str, Any]) -> None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.info(
            "discord_webhook_skipped",
            extra={"reason": "missing DISCORD_WEBHOOK_URL"},
        )
        return

    try:
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning(
            "discord_webhook_send_failed",
            extra={"error": str(exc)},
        )
