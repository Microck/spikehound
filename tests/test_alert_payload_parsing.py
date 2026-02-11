from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from fastapi.testclient import TestClient

from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.diagnosis import Diagnosis
from models.diagnosis import RootCauseHypothesis
from models.findings import InvestigationReport
from models.findings import UnifiedFindings
from models.remediation import RemediationAction
from models.remediation import RemediationActionType
from models.remediation import RemediationPlan
from models.remediation import RemediationRiskLevel
import web.app as web_app


def _agent_result(
    agent: AgentName,
    *,
    status: AgentStatus,
    data: Any,
    errors: list[str] | None = None,
) -> AgentResult[Any]:
    started_at = datetime(2026, 2, 11, 19, 0, tzinfo=timezone.utc)
    finished_at = datetime(2026, 2, 11, 19, 1, tzinfo=timezone.utc)
    return AgentResult[Any](
        agent=agent,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        data=data,
        errors=errors or [],
    )


def _build_report(
    alert_id: str,
    *,
    notes: str,
    diagnosis_status: AgentStatus = AgentStatus.OK,
    diagnosis_errors: list[str] | None = None,
) -> InvestigationReport:
    unified_findings = UnifiedFindings(
        alert_id=alert_id,
        received_at=datetime(2026, 2, 11, 19, 0, tzinfo=timezone.utc),
        alert_summary={"alert_id": alert_id},
        notes=notes,
    )

    diagnosis_data: Diagnosis | None = None
    if diagnosis_status is AgentStatus.OK:
        diagnosis_data = Diagnosis(
            hypothesis=RootCauseHypothesis(
                title="GPU VM left running",
                explanation="VM remained active overnight.",
                evidence=["High spend from vm-demo"],
            ),
            confidence=80,
            alternatives=[],
            risks=[],
        )

    remediation_data = RemediationPlan(
        summary="Stop the GPU VM",
        actions=[
            RemediationAction(
                type=RemediationActionType.STOP_VM,
                target_resource_id=(
                    "/subscriptions/sub-123/resourceGroups/rg-demo/providers/"
                    "Microsoft.Compute/virtualMachines/vm-demo"
                ),
                parameters={"mode": "deallocate"},
                risk_level=RemediationRiskLevel.MEDIUM,
            )
        ],
        rollback_notes="Restart VM if this was a false positive.",
    )

    return InvestigationReport(
        unified_findings=unified_findings,
        diagnosis_result=_agent_result(
            AgentName.DIAGNOSIS,
            status=diagnosis_status,
            data=diagnosis_data,
            errors=diagnosis_errors,
        ),
        remediation_result=_agent_result(
            AgentName.REMEDIATION,
            status=AgentStatus.OK,
            data=remediation_data,
        ),
    )


def test_webhook_normalizes_azure_monitor_common_schema_payload(
    monkeypatch,
) -> None:
    resource_id = (
        "/subscriptions/sub-123/resourceGroups/rg-demo/providers/"
        "Microsoft.Compute/virtualMachines/vm-demo"
    )
    azure_payload = {
        "schemaId": "azureMonitorCommonAlertSchema",
        "data": {
            "essentials": {
                "alertId": (
                    "/subscriptions/sub-123/providers/Microsoft.AlertsManagement/"
                    "alerts/alert-azure-001"
                ),
                "alertRule": "GPU VM Cost Spike",
                "severity": "Sev2",
                "firedDateTime": "2026-02-11T19:00:00Z",
                "alertTargetIDs": [resource_id],
            },
            "alertContext": {
                "conditionType": "SingleResourceMultipleMetricCriteria",
            },
        },
    }

    captured_payload: dict[str, Any] = {}

    async def fake_handle_alert_async(
        normalized_payload: dict[str, Any],
    ) -> InvestigationReport:
        captured_payload.update(normalized_payload)
        return _build_report(normalized_payload["alert_id"], notes="normalized")

    monkeypatch.setattr(
        web_app.coordinator_agent,
        "handle_alert_async",
        fake_handle_alert_async,
    )

    client = TestClient(web_app.app)
    response = client.post("/webhooks/alert", json=azure_payload)

    assert response.status_code == 200
    assert captured_payload["alert_id"].endswith("alert-azure-001")
    assert captured_payload["rule_name"] == "GPU VM Cost Spike"
    assert captured_payload["severity"] == "Sev2"
    assert captured_payload["fired_date_time"] == "2026-02-11T19:00:00Z"
    assert captured_payload["resource_id"] == resource_id

    response_payload = response.json()
    assert response_payload["unified_findings"]["alert_id"].endswith("alert-azure-001")
    assert response_payload["unified_findings"]["notes"] == "normalized"
    assert response_payload["diagnosis_result"]["status"] == "ok"


def test_duplicate_webhooks_return_cached_report_without_rerunning_pipeline(
    monkeypatch,
) -> None:
    invocation_count = 0

    async def fake_handle_alert_async(
        normalized_payload: dict[str, Any],
    ) -> InvestigationReport:
        nonlocal invocation_count
        invocation_count += 1
        return _build_report(
            normalized_payload["alert_id"],
            notes=f"run-{invocation_count}",
        )

    monkeypatch.setattr(
        web_app.coordinator_agent,
        "handle_alert_async",
        fake_handle_alert_async,
    )

    client = TestClient(web_app.app)
    payload = {"alert_id": "alert-idempotency-001", "summary": "duplicate test"}

    first = client.post("/webhooks/alert", json=payload)
    second = client.post("/webhooks/alert", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert invocation_count == 1
    assert first.json()["unified_findings"]["notes"] == "run-1"
    assert second.json()["unified_findings"]["notes"] == "run-1"


def test_transient_agent_errors_trigger_single_retry(monkeypatch) -> None:
    invocation_count = 0

    async def fake_handle_alert_async(
        normalized_payload: dict[str, Any],
    ) -> InvestigationReport:
        nonlocal invocation_count
        invocation_count += 1
        if invocation_count == 1:
            return _build_report(
                normalized_payload["alert_id"],
                notes="first-run",
                diagnosis_status=AgentStatus.ERROR,
                diagnosis_errors=["Network timeout while calling diagnosis backend"],
            )

        return _build_report(normalized_payload["alert_id"], notes="retry-run")

    monkeypatch.setattr(
        web_app.coordinator_agent,
        "handle_alert_async",
        fake_handle_alert_async,
    )

    client = TestClient(web_app.app)
    response = client.post("/webhooks/alert", json={"alert_id": "alert-retry-001"})

    assert response.status_code == 200
    assert invocation_count == 2
    payload = response.json()
    assert payload["unified_findings"]["notes"] == "retry-run"
    assert payload["diagnosis_result"]["status"] == "ok"
