from __future__ import annotations

import logging
import os
import time
from typing import Any
from typing import Mapping

import httpx
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


logger = logging.getLogger("incident-war-room.integrations.discord")
DISCORD_SIGNATURE_MAX_AGE_SECONDS = 60 * 5


def verify_discord_signature(raw_body: str | bytes, headers: Mapping[str, str]) -> bool:
    public_key_hex = os.getenv("DISCORD_INTERACTIONS_PUBLIC_KEY")
    if not public_key_hex:
        logger.warning(
            "discord_signature_verification_failed",
            extra={"reason": "missing DISCORD_INTERACTIONS_PUBLIC_KEY"},
        )
        return False

    timestamp = _get_header(headers, "X-Signature-Timestamp")
    signature_hex = _get_header(headers, "X-Signature-Ed25519")
    if not timestamp or not signature_hex:
        return False

    try:
        timestamp_int = int(timestamp)
    except ValueError:
        return False

    if abs(int(time.time()) - timestamp_int) > DISCORD_SIGNATURE_MAX_AGE_SECONDS:
        return False

    if isinstance(raw_body, str):
        body_bytes = raw_body.encode("utf-8")
    else:
        body_bytes = raw_body

    try:
        public_key = VerifyKey(bytes.fromhex(public_key_hex))
        signature = bytes.fromhex(signature_hex)
    except ValueError:
        return False

    signed_payload = timestamp.encode("utf-8") + body_bytes
    try:
        public_key.verify(signed_payload, signature)
    except BadSignatureError:
        return False

    return True


def build_discord_custom_id(action: str, investigation_id: str) -> str:
    return f"{action}:{investigation_id}"


def parse_discord_custom_id(custom_id: str) -> tuple[str, str] | None:
    action, separator, investigation_id = custom_id.partition(":")
    if separator != ":" or not action or not investigation_id:
        return None
    return action, investigation_id


def send_discord_webhook(payload: dict[str, Any]) -> None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.info(
            "discord_webhook_skipped",
            extra={"reason": "missing DISCORD_WEBHOOK_URL"},
        )
        return

    request_payload = dict(payload)
    request_payload.setdefault("allowed_mentions", {"parse": []})

    webhook_username = os.getenv("DISCORD_WEBHOOK_USERNAME")
    if webhook_username and "username" not in request_payload:
        request_payload["username"] = webhook_username

    webhook_avatar_url = os.getenv("DISCORD_WEBHOOK_AVATAR_URL")
    if webhook_avatar_url and "avatar_url" not in request_payload:
        request_payload["avatar_url"] = webhook_avatar_url

    params: dict[str, str] = {}
    thread_id = os.getenv("DISCORD_WEBHOOK_THREAD_ID")
    if thread_id:
        params["thread_id"] = thread_id

    timeout_seconds = _float_env("DISCORD_WEBHOOK_TIMEOUT_SECONDS", default=10.0)
    max_retries = _int_env("DISCORD_WEBHOOK_MAX_RETRIES", default=2)
    backoff_seconds = _float_env("DISCORD_WEBHOOK_BACKOFF_SECONDS", default=1.0)

    for attempt in range(max_retries + 1):
        try:
            response = httpx.post(
                webhook_url,
                json=request_payload,
                timeout=timeout_seconds,
                params=params or None,
            )

            status_code = response.status_code
            if status_code == 429:
                if attempt < max_retries:
                    delay = _retry_after_seconds(
                        response,
                        fallback=backoff_seconds * (2**attempt),
                    )
                    time.sleep(delay)
                    continue

                logger.warning(
                    "discord_webhook_rate_limited",
                    extra={"status_code": status_code, "attempt": attempt + 1},
                )
                return

            if 500 <= status_code < 600:
                if attempt < max_retries:
                    delay = min(backoff_seconds * (2**attempt), 30.0)
                    time.sleep(delay)
                    continue

                logger.warning(
                    "discord_webhook_server_error",
                    extra={"status_code": status_code, "attempt": attempt + 1},
                )
                return

            if 400 <= status_code < 500:
                logger.warning(
                    "discord_webhook_client_error",
                    extra={"status_code": status_code, "attempt": attempt + 1},
                )
                return

            return
        except httpx.RequestError as exc:
            if attempt < max_retries:
                delay = min(backoff_seconds * (2**attempt), 30.0)
                time.sleep(delay)
                continue

            logger.warning(
                "discord_webhook_send_failed",
                extra={"error": str(exc), "attempt": attempt + 1},
            )
            return


def _retry_after_seconds(response: httpx.Response, fallback: float) -> float:
    header_value = response.headers.get("Retry-After")
    if header_value is not None:
        try:
            parsed = float(header_value)
            if parsed > 0:
                return min(parsed, 30.0)
        except ValueError:
            pass

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if isinstance(payload, dict):
        retry_after_value = payload.get("retry_after")
        if isinstance(retry_after_value, (int, float)) and retry_after_value > 0:
            return min(float(retry_after_value), 30.0)

    return min(max(fallback, 0.1), 30.0)


def _int_env(name: str, *, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return max(parsed, 0)


def _float_env(name: str, *, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = float(raw)
    except ValueError:
        return default
    return max(parsed, 0.1)


def _get_header(headers: Mapping[str, str], name: str) -> str:
    value = headers.get(name)
    if isinstance(value, str) and value:
        return value

    lowered_name = name.lower()
    for key, header_value in headers.items():
        if key.lower() == lowered_name and header_value:
            return header_value

    return ""
