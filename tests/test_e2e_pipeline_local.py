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
from models.findings import CostFinding
from models.findings import InvestigationFindings
from models.findings import UnifiedFindings
from models.history_findings import HistoryFindings
from models.remediation import RemediationAction
from models.remediation import RemediationActionType
from models.remediation import RemediationPlan
from models.remediation import RemediationRiskLevel
from models.resource_findings import ResourceFindings
import web.app as web_app


def _agent_result(agent: AgentName, data: Any) -> AgentResult[Any]:
    started_at = datetime(2026, 2, 11, 4, 30, tzinfo=timezone.utc)
    finished_at = datetime(2026, 2, 11, 4, 31, tzinfo=timezone.utc)
    return AgentResult[Any](
        agent=agent,
        status=AgentStatus.OK,
        started_at=started_at,
        finished_at=finished_at,
        data=data,
        errors=[],
    )


def test_webhook_local_e2e_returns_all_pipeline_sections(monkeypatch) -> None:
    resource_id = (
        "/subscriptions/sub-123/resourceGroups/rg/providers/"
        "Microsoft.Compute/virtualMachines/vm-e2e"
    )

    cost_result = _agent_result(
        AgentName.COST,
        InvestigationFindings(
            alert_id="alert-local-e2e",
            received_at=datetime(2026, 2, 11, 4, 0, tzinfo=timezone.utc),
            cost_findings=[
                CostFinding(
                    resource_id=resource_id,
                    cost=155.25,
                    currency="USD",
                )
            ],
            notes="deterministic local test",
        ),
    )
    resource_result = _agent_result(
        AgentName.RESOURCE,
        ResourceFindings(
            target_resource_id=resource_id,
            notes="resource lookup ok",
        ),
    )
    history_result = _agent_result(
        AgentName.HISTORY,
        HistoryFindings(
            query="gpu vm cost spike",
            matches=[],
            notes="no prior incident",
        ),
    )
    diagnosis_result = _agent_result(
        AgentName.DIAGNOSIS,
        Diagnosis(
            hypothesis=RootCauseHypothesis(
                title="GPU VM left running",
                explanation="Running VM with no shutdown policy drove the anomaly.",
                evidence=["vm-e2e is top cost driver"],
            ),
            confidence=80,
            alternatives=["Legitimate load test"],
            risks=["Stopping may interrupt active jobs"],
        ),
    )
    remediation_result = _agent_result(
        AgentName.REMEDIATION,
        RemediationPlan(
            summary="Add shutdown automation and notify owner",
            actions=[
                RemediationAction(
                    type=RemediationActionType.ADD_AUTO_SHUTDOWN,
                    target_resource_id=resource_id,
                    parameters={"schedule_utc": "22:00"},
                    risk_level=RemediationRiskLevel.LOW,
                )
            ],
            rollback_notes="Remove shutdown schedule if false positive.",
        ),
    )

    monkeypatch.setattr(
        web_app.coordinator_agent.cost_analyst, "run", lambda _: cost_result
    )
    monkeypatch.setattr(
        web_app.coordinator_agent.resource_agent,
        "run",
        lambda _: resource_result,
    )
    monkeypatch.setattr(
        web_app.coordinator_agent.history_agent,
        "run",
        lambda _: history_result,
    )

    def fake_diagnosis(unified_findings: UnifiedFindings) -> AgentResult[Any]:
        assert isinstance(unified_findings, UnifiedFindings)
        return diagnosis_result

    def fake_remediation(
        unified_findings: UnifiedFindings,
        diagnosis: Diagnosis,
    ) -> AgentResult[Any]:
        assert isinstance(unified_findings, UnifiedFindings)
        assert isinstance(diagnosis, Diagnosis)
        return remediation_result

    monkeypatch.setattr(
        web_app.coordinator_agent.diagnosis_agent, "run", fake_diagnosis
    )
    monkeypatch.setattr(
        web_app.coordinator_agent.remediation_agent,
        "run",
        fake_remediation,
    )

    client = TestClient(web_app.app)
    response = client.post(
        "/webhooks/alert",
        json={
            "alert_id": "alert-local-e2e",
            "summary": "GPU VM spend spike",
            "resource_id": resource_id,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert set(payload.keys()) == {
        "unified_findings",
        "diagnosis_result",
        "remediation_result",
    }

    unified_findings = payload["unified_findings"]
    assert unified_findings["alert_id"] == "alert-local-e2e"
    assert set(unified_findings["results"].keys()) == {"cost", "resource", "history"}
    assert unified_findings["results"]["cost"]["status"] == "ok"
    assert unified_findings["results"]["resource"]["status"] == "ok"
    assert unified_findings["results"]["history"]["status"] == "ok"

    assert payload["diagnosis_result"]["agent"] == "diagnosis"
    assert payload["diagnosis_result"]["status"] == "ok"
    assert payload["diagnosis_result"]["data"]["confidence"] == 80

    assert payload["remediation_result"]["agent"] == "remediation"
    assert payload["remediation_result"]["status"] == "ok"
    assert (
        payload["remediation_result"]["data"]["actions"][0]["type"]
        == "add_auto_shutdown"
    )
    assert (
        payload["remediation_result"]["data"]["actions"][0]["human_approval_required"]
        is True
    )
