from __future__ import annotations

from datetime import datetime
from datetime import timezone
import threading
from typing import Any

from fastapi.testclient import TestClient
import pytest

from agents.coordinator import CoordinatorAgent
from agents.cost_analyst import CostAnalystAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.history_agent import HistoryAgent
from agents.remediation_agent import RemediationAgent
from agents.resource_agent import ResourceAgent
from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.diagnosis import Diagnosis
from models.diagnosis import RootCauseHypothesis
from models.findings import CostFinding
from models.findings import InvestigationReport
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
    started_at = datetime(2026, 2, 11, 2, 0, tzinfo=timezone.utc)
    finished_at = datetime(2026, 2, 11, 2, 1, tzinfo=timezone.utc)
    return AgentResult[Any](
        agent=agent,
        status=AgentStatus.OK,
        started_at=started_at,
        finished_at=finished_at,
        data=data,
        errors=[],
    )


def test_coordinator_starts_agents_in_parallel(monkeypatch: pytest.MonkeyPatch) -> None:
    started = {
        AgentName.COST: threading.Event(),
        AgentName.RESOURCE: threading.Event(),
        AgentName.HISTORY: threading.Event(),
    }
    barrier = threading.Barrier(4)
    alert_id = "alert-parallel-1"
    resource_id = (
        "/subscriptions/sub-123/resourceGroups/rg/providers/"
        "Microsoft.Compute/virtualMachines/vm-cost"
    )

    def make_run(agent: AgentName, data: Any):
        def _run(
            self,
            alert_payload: dict[str, object],
            hints: dict[str, object] | None = None,
        ) -> AgentResult[Any]:
            del self, alert_payload, hints
            started[agent].set()
            barrier.wait(timeout=5)
            return _agent_result(agent, data)

        return _run

    monkeypatch.setattr(
        CostAnalystAgent,
        "run",
        make_run(
            AgentName.COST,
            InvestigationFindings(
                alert_id=alert_id,
                received_at=datetime(2026, 2, 11, 2, 0, tzinfo=timezone.utc),
                cost_findings=[
                    CostFinding(resource_id=resource_id, cost=125.5, currency="USD")
                ],
                notes="",
            ),
        ),
    )
    monkeypatch.setattr(
        ResourceAgent,
        "run",
        make_run(
            AgentName.RESOURCE,
            ResourceFindings(target_resource_id=resource_id, notes=""),
        ),
    )
    monkeypatch.setattr(
        HistoryAgent,
        "run",
        make_run(
            AgentName.HISTORY,
            HistoryFindings(query="cost anomaly", matches=[], notes=""),
        ),
    )
    monkeypatch.setattr(
        DiagnosisAgent,
        "run",
        lambda self, unified_findings: _agent_result(
            AgentName.DIAGNOSIS,
            Diagnosis(
                hypothesis=RootCauseHypothesis(
                    title="GPU VM left running",
                    explanation="Detected running VM with no shutdown schedule.",
                    evidence=["vm-cost has high spend"],
                ),
                confidence=80,
                alternatives=["Legitimate batch workload"],
                risks=["Stopping VM interrupts active jobs"],
            ),
        ),
    )
    monkeypatch.setattr(
        RemediationAgent,
        "run",
        lambda self, unified_findings, diagnosis: _agent_result(
            AgentName.REMEDIATION,
            RemediationPlan(
                summary="Stop VM after approval",
                actions=[
                    RemediationAction(
                        type=RemediationActionType.STOP_VM,
                        target_resource_id=resource_id,
                        parameters={"mode": "deallocate"},
                        risk_level=RemediationRiskLevel.MEDIUM,
                    )
                ],
                rollback_notes="Restart VM if jobs were interrupted.",
            ),
        ),
    )

    coordinator = CoordinatorAgent(per_agent_timeout_seconds=20.0)
    execution: dict[str, Any] = {}

    def invoke_coordinator() -> None:
        try:
            execution["result"] = coordinator.handle_alert(
                {
                    "alert_id": alert_id,
                    "summary": "GPU VM spend spike",
                    "resource_id": resource_id,
                }
            )
        except Exception as exc:  # pragma: no cover - defensive assertion capture
            execution["error"] = exc

    thread = threading.Thread(target=invoke_coordinator)
    thread.start()

    for name, event in started.items():
        assert event.wait(timeout=5), (
            f"{name.value} agent never reached execution barrier"
        )

    try:
        barrier.wait(timeout=5)
    except threading.BrokenBarrierError as exc:
        pytest.fail(
            "Barrier timed out while releasing agents; coordinator likely ran sequentially"
        )

    thread.join(timeout=5)
    assert not thread.is_alive(), (
        "Coordinator call did not complete after releasing barrier"
    )
    assert "error" not in execution, (
        f"Coordinator raised unexpected error: {execution['error']}"
    )

    report = execution["result"]
    assert isinstance(report, InvestigationReport)

    findings = report.unified_findings
    assert set(findings.results.keys()) == {
        AgentName.COST,
        AgentName.RESOURCE,
        AgentName.HISTORY,
    }
    assert findings.results[AgentName.COST].status == AgentStatus.OK
    assert findings.results[AgentName.RESOURCE].status == AgentStatus.OK
    assert findings.results[AgentName.HISTORY].status == AgentStatus.OK
    assert report.diagnosis_result.agent == AgentName.DIAGNOSIS
    assert report.remediation_result.agent == AgentName.REMEDIATION


def test_webhook_returns_unified_findings_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    merged = UnifiedFindings.merge(
        [
            _agent_result(
                AgentName.COST,
                InvestigationFindings(
                    alert_id="alert-123",
                    received_at=datetime(2026, 2, 11, 2, 0, tzinfo=timezone.utc),
                    cost_findings=[
                        CostFinding(
                            resource_id="/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                            cost=200.0,
                            currency="USD",
                        )
                    ],
                    notes="",
                ),
            ),
            _agent_result(
                AgentName.RESOURCE,
                ResourceFindings(
                    target_resource_id="/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                    notes="",
                ),
            ),
            _agent_result(
                AgentName.HISTORY,
                HistoryFindings(query="cost spike", matches=[], notes=""),
            ),
        ],
        alert_summary={"alert_id": "alert-123"},
    )

    report = InvestigationReport(
        unified_findings=merged,
        diagnosis_result=_agent_result(
            AgentName.DIAGNOSIS,
            Diagnosis(
                hypothesis=RootCauseHypothesis(
                    title="Recurring VM overrun",
                    explanation="Matches prior incident pattern.",
                    evidence=["high spend on vm1"],
                ),
                confidence=55,
                alternatives=["Legitimate peak workload"],
                risks=["Stopping service may affect users"],
            ),
        ),
        remediation_result=_agent_result(
            AgentName.REMEDIATION,
            RemediationPlan(
                summary="Notify owner for approval",
                actions=[
                    RemediationAction(
                        type=RemediationActionType.NOTIFY_OWNER,
                        target_resource_id="/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                        parameters={"channel": "incident-war-room"},
                        risk_level=RemediationRiskLevel.LOW,
                    )
                ],
                rollback_notes="No infrastructure rollback needed.",
            ),
        ),
    )

    async def fake_handle_alert_async(_: dict[str, object]) -> InvestigationReport:
        return report

    monkeypatch.setattr(
        web_app.coordinator_agent, "handle_alert_async", fake_handle_alert_async
    )

    client = TestClient(web_app.app)
    response = client.post("/webhooks/alert", json={"alert_id": "alert-123"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["unified_findings"]["alert_summary"]["alert_id"] == "alert-123"
    assert set(payload["unified_findings"]["results"].keys()) == {
        "cost",
        "resource",
        "history",
    }
    assert payload["unified_findings"]["results"]["cost"]["status"] == "ok"
    assert payload["unified_findings"]["results"]["resource"]["status"] == "ok"
    assert payload["unified_findings"]["results"]["history"]["status"] == "ok"
    assert payload["diagnosis_result"]["agent"] == "diagnosis"
    assert payload["remediation_result"]["agent"] == "remediation"
