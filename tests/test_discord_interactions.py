from __future__ import annotations

import json

from fastapi.testclient import TestClient
from nacl.signing import SigningKey
import pytest

from integrations import discord as discord_integration
from models.approval import ApprovalDecision
import web.app as web_app


def _signed_headers(
    signing_key: SigningKey, timestamp: str, body: bytes
) -> dict[str, str]:
    signature = signing_key.sign(timestamp.encode("utf-8") + body).signature.hex()
    return {
        "X-Signature-Ed25519": signature,
        "X-Signature-Timestamp": timestamp,
        "content-type": "application/json",
    }


def _configure_signature_key(
    monkeypatch: pytest.MonkeyPatch, signing_key: SigningKey
) -> None:
    monkeypatch.setenv(
        "DISCORD_INTERACTIONS_PUBLIC_KEY",
        signing_key.verify_key.encode().hex(),
    )


def test_verify_discord_signature_accepts_valid_signature(monkeypatch) -> None:
    signing_key = SigningKey.generate()
    now_epoch = 1_777_777_777
    timestamp = str(now_epoch)
    raw_body = b'{"type":1}'

    _configure_signature_key(monkeypatch, signing_key)
    monkeypatch.setattr(discord_integration.time, "time", lambda: now_epoch)

    assert discord_integration.verify_discord_signature(
        raw_body,
        _signed_headers(signing_key, timestamp, raw_body),
    )


def test_verify_discord_signature_rejects_invalid_signature(monkeypatch) -> None:
    signing_key = SigningKey.generate()
    now_epoch = 1_777_777_777
    timestamp = str(now_epoch)
    raw_body = b'{"type":1}'

    _configure_signature_key(monkeypatch, signing_key)
    monkeypatch.setattr(discord_integration.time, "time", lambda: now_epoch)

    headers = _signed_headers(signing_key, timestamp, raw_body)
    headers["X-Signature-Ed25519"] = "00" * 64

    assert not discord_integration.verify_discord_signature(raw_body, headers)


def test_verify_discord_signature_rejects_stale_timestamp(monkeypatch) -> None:
    signing_key = SigningKey.generate()
    now_epoch = 1_777_777_777
    stale_timestamp = str(now_epoch - 301)
    raw_body = b'{"type":1}'

    _configure_signature_key(monkeypatch, signing_key)
    monkeypatch.setattr(discord_integration.time, "time", lambda: now_epoch)

    assert not discord_integration.verify_discord_signature(
        raw_body,
        _signed_headers(signing_key, stale_timestamp, raw_body),
    )


def test_discord_interaction_ping_returns_pong(monkeypatch) -> None:
    signing_key = SigningKey.generate()
    now_epoch = 1_777_777_777
    timestamp = str(now_epoch)
    body = json.dumps({"type": 1}).encode("utf-8")

    _configure_signature_key(monkeypatch, signing_key)
    monkeypatch.setattr(discord_integration.time, "time", lambda: now_epoch)

    client = TestClient(web_app.app)
    response = client.post(
        "/webhooks/discord/interactions",
        data=body,
        headers=_signed_headers(signing_key, timestamp, body),
    )

    assert response.status_code == 200
    assert response.json() == {"type": 1}


def test_discord_interaction_rejects_invalid_signature(monkeypatch) -> None:
    signing_key = SigningKey.generate()
    now_epoch = 1_777_777_777
    timestamp = str(now_epoch)
    body = json.dumps({"type": 1}).encode("utf-8")

    _configure_signature_key(monkeypatch, signing_key)
    monkeypatch.setattr(discord_integration.time, "time", lambda: now_epoch)

    headers = {
        "X-Signature-Ed25519": "00" * 64,
        "X-Signature-Timestamp": timestamp,
        "content-type": "application/json",
    }

    client = TestClient(web_app.app)
    response = client.post(
        "/webhooks/discord/interactions",
        data=body,
        headers=headers,
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("action_id", "expected_decision", "queues_execution"),
    [
        ("approve_remediation", ApprovalDecision.APPROVE, True),
        ("reject_remediation", ApprovalDecision.REJECT, False),
        ("investigate_more", ApprovalDecision.INVESTIGATE, False),
    ],
)
def test_discord_component_interactions_record_approval_decisions(
    monkeypatch,
    action_id: str,
    expected_decision: ApprovalDecision,
    queues_execution: bool,
) -> None:
    signing_key = SigningKey.generate()
    now_epoch = 1_777_777_777
    timestamp = str(now_epoch)
    investigation_id = f"alert-{action_id}"

    _configure_signature_key(monkeypatch, signing_key)
    monkeypatch.setattr(discord_integration.time, "time", lambda: now_epoch)

    queued_executions: list[tuple[str, ApprovalDecision]] = []

    def fake_execute(investigation_id: str, approval_record) -> None:
        queued_executions.append((investigation_id, approval_record.decision))

    monkeypatch.setattr(web_app, "_execute_approved_remediation", fake_execute)

    payload = {
        "type": 3,
        "member": {
            "user": {
                "id": "discord-user-001",
                "username": "discord-user",
            }
        },
        "data": {
            "custom_id": f"{action_id}:{investigation_id}",
        },
    }
    body = json.dumps(payload).encode("utf-8")

    client = TestClient(web_app.app)
    response = client.post(
        "/webhooks/discord/interactions",
        data=body,
        headers=_signed_headers(signing_key, timestamp, body),
    )

    assert response.status_code == 200
    response_payload = response.json()
    assert response_payload["type"] == 4
    assert "Recorded" in response_payload["data"]["content"]

    approval_record = web_app.approval_records[investigation_id]
    assert approval_record.investigation_id == investigation_id
    assert approval_record.decision is expected_decision
    assert approval_record.decided_by == "discord-user"

    if expected_decision is ApprovalDecision.INVESTIGATE:
        assert approval_record.reason == "Requested additional investigation"
    else:
        assert approval_record.reason is None

    if queues_execution:
        assert queued_executions == [(investigation_id, ApprovalDecision.APPROVE)]
    else:
        assert queued_executions == []
