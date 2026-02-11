from __future__ import annotations

from datetime import datetime
from datetime import timezone
import hashlib
import hmac
import json
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from execution.remediation import ExecutionOutcome
from execution.remediation import ExecutionStatus
from models.approval import ApprovalDecision
from models.remediation import RemediationAction
from models.remediation import RemediationActionType
from models.remediation import RemediationPlan
from models.remediation import RemediationRiskLevel
import web.app as web_app


def _sign(secret: str, timestamp: str, raw_body: str) -> str:
    payload = f"v0:{timestamp}:{raw_body}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_slack_approve_triggers_execution_and_follow_up(monkeypatch) -> None:
    secret = "test-signing-secret"
    now_epoch = 1_777_777_777
    timestamp = str(now_epoch)
    investigation_id = "alert-approve-001"

    monkeypatch.setenv("SLACK_SIGNING_SECRET", secret)
    monkeypatch.setattr("integrations.slack.time.time", lambda: now_epoch)

    web_app.approval_records.clear()
    web_app.latest_reports.clear()
    web_app.latest_remediation_plans.clear()
    web_app.latest_remediation_plans[investigation_id] = RemediationPlan(
        summary="Stop runaway VM",
        actions=[
            RemediationAction(
                type=RemediationActionType.STOP_VM,
                target_resource_id=(
                    "/subscriptions/sub-123/resourceGroups/rg-demo/providers/"
                    "Microsoft.Compute/virtualMachines/vm-demo"
                ),
                parameters={},
                risk_level=RemediationRiskLevel.MEDIUM,
            )
        ],
        rollback_notes="Restart VM if needed.",
    )

    executed: dict[str, str] = {}
    sent_messages: list[dict[str, object]] = []

    def fake_execute(plan, approval_record):
        executed["summary"] = plan.summary
        executed["decision"] = approval_record.decision.value
        return [
            ExecutionOutcome(
                action="stop_vm",
                status=ExecutionStatus.OK,
                message="Stopped vm-demo",
                started_at=datetime(2026, 2, 11, 18, 10, tzinfo=timezone.utc),
                finished_at=datetime(2026, 2, 11, 18, 11, tzinfo=timezone.utc),
            )
        ]

    def fake_send_webhook(text: str, blocks=None) -> None:
        sent_messages.append({"text": text, "blocks": blocks})

    monkeypatch.setattr(web_app, "execute_remediation", fake_execute)
    monkeypatch.setattr(web_app, "send_webhook", fake_send_webhook)

    action_payload = {
        "type": "block_actions",
        "user": {"id": "U123"},
        "actions": [
            {
                "action_id": "approve_remediation",
                "value": investigation_id,
            }
        ],
    }
    raw_body = urlencode({"payload": json.dumps(action_payload)})

    headers = {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": _sign(secret, timestamp, raw_body),
        "content-type": "application/x-www-form-urlencoded",
    }

    client = TestClient(web_app.app)
    response = client.post("/webhooks/slack/actions", data=raw_body, headers=headers)

    assert response.status_code == 200
    assert "queued" in response.json()["text"]
    assert (
        web_app.approval_records[investigation_id].decision is ApprovalDecision.APPROVE
    )
    assert executed == {"summary": "Stop runaway VM", "decision": "approve"}
    assert len(sent_messages) == 1
    assert investigation_id in str(sent_messages[0]["text"])

    web_app.approval_records.clear()
    web_app.latest_reports.clear()
    web_app.latest_remediation_plans.clear()
