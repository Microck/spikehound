from __future__ import annotations

import logging
import os
from typing import Any

import httpx


logger = logging.getLogger("incident-war-room.integrations.slack")


def send_webhook(text: str, blocks: list[dict[str, Any]] | None = None) -> None:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.info(
            "slack_webhook_skipped",
            extra={"reason": "missing SLACK_WEBHOOK_URL"},
        )
        return

    payload: dict[str, Any] = {"text": text}
    if blocks is not None:
        payload["blocks"] = blocks

    try:
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning(
            "slack_webhook_send_failed",
            extra={"error": str(exc)},
        )
