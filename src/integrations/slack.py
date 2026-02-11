from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Any
from typing import Mapping

import httpx


logger = logging.getLogger("incident-war-room.integrations.slack")


def verify_signature(raw_body: str | bytes, headers: Mapping[str, str]) -> bool:
    signing_secret = os.getenv("SLACK_SIGNING_SECRET")
    if not signing_secret:
        logger.warning(
            "slack_signature_verification_skipped",
            extra={"reason": "missing SLACK_SIGNING_SECRET"},
        )
        return False

    timestamp = headers.get("X-Slack-Request-Timestamp", "")
    signature = headers.get("X-Slack-Signature", "")
    if not timestamp or not signature:
        return False

    try:
        timestamp_int = int(timestamp)
    except ValueError:
        return False

    if abs(int(time.time()) - timestamp_int) > 60 * 5:
        return False

    if isinstance(raw_body, bytes):
        body_text = raw_body.decode("utf-8")
    else:
        body_text = raw_body

    signed_payload = f"v0:{timestamp}:{body_text}".encode("utf-8")
    computed_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(computed_signature, signature)


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
