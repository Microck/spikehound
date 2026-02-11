from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Any
from typing import Mapping

import httpx
from pydantic import BaseModel


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


def format_execution_outcomes_for_slack(
    investigation_id: str,
    outcomes: list[Any],
) -> dict[str, Any]:
    if not outcomes:
        return {
            "text": (
                "Remediation execution completed for "
                f"{investigation_id}, but no outcomes were recorded."
            )
        }

    status_counts: dict[str, int] = {}
    lines: list[str] = []

    for outcome in outcomes:
        payload = _to_mapping(outcome)
        action = str(payload.get("action") or "unknown-action")
        status = str(payload.get("status") or "unknown")
        message = str(payload.get("message") or "")

        status_counts[status] = status_counts.get(status, 0) + 1
        if message:
            lines.append(f"*{action}* -> `{status}`: {message}")
        else:
            lines.append(f"*{action}* -> `{status}`")

    status_summary = ", ".join(
        f"{status}: {count}" for status, count in sorted(status_counts.items())
    )
    details = "\n".join(lines)
    text = (
        f"Remediation execution completed for {investigation_id}. "
        f"Outcome summary: {status_summary}."
    )

    return {
        "text": text,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Remediation results for `{investigation_id}`*\n{details}"
                    ),
                },
            }
        ],
    }


def _to_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return dict(value)
    return {}
