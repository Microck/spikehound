from __future__ import annotations

import hashlib
import hmac

from integrations.slack import verify_signature


def _sign(secret: str, timestamp: str, raw_body: str) -> str:
    payload = f"v0:{timestamp}:{raw_body}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_verify_signature_accepts_valid_signature(monkeypatch) -> None:
    secret = "test-signing-secret"
    raw_body = "payload=%7B%22type%22%3A%22block_actions%22%7D"
    now_epoch = 1_777_777_777
    timestamp = str(now_epoch)

    monkeypatch.setenv("SLACK_SIGNING_SECRET", secret)
    monkeypatch.setattr("integrations.slack.time.time", lambda: now_epoch)

    headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": _sign(secret, timestamp, raw_body),
    }

    assert verify_signature(raw_body, headers)


def test_verify_signature_rejects_invalid_signature(monkeypatch) -> None:
    secret = "test-signing-secret"
    raw_body = "payload=%7B%22type%22%3A%22block_actions%22%7D"
    now_epoch = 1_777_777_777
    timestamp = str(now_epoch)

    monkeypatch.setenv("SLACK_SIGNING_SECRET", secret)
    monkeypatch.setattr("integrations.slack.time.time", lambda: now_epoch)

    headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": "v0=invalid",
    }

    assert not verify_signature(raw_body, headers)


def test_verify_signature_rejects_stale_timestamp(monkeypatch) -> None:
    secret = "test-signing-secret"
    raw_body = "payload=%7B%22type%22%3A%22block_actions%22%7D"
    now_epoch = 1_777_777_777
    stale_timestamp = str(now_epoch - 301)

    monkeypatch.setenv("SLACK_SIGNING_SECRET", secret)
    monkeypatch.setattr("integrations.slack.time.time", lambda: now_epoch)

    headers = {
        "X-Slack-Request-Timestamp": stale_timestamp,
        "X-Slack-Signature": _sign(secret, stale_timestamp, raw_body),
    }

    assert not verify_signature(raw_body, headers)
