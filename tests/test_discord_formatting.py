from __future__ import annotations

from datetime import datetime
from datetime import timezone
import json
from typing import Any

from integrations.message_format import format_investigation_report_for_discord
from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.diagnosis import Diagnosis
from models.diagnosis import RootCauseHypothesis
from models.findings import CostFinding
from models.findings import InvestigationFindings
from models.findings import InvestigationReport
from models.findings import UnifiedFindings
from models.remediation import RemediationAction
from models.remediation import RemediationActionType
from models.remediation import RemediationPlan
from models.remediation import RemediationRiskLevel


def _agent_result(agent: AgentName, data: Any) -> AgentResult[Any]:
    started_at = datetime(2026, 2, 11, 5, 0, tzinfo=timezone.utc)
    finished_at = datetime(2026, 2, 11, 5, 1, tzinfo=timezone.utc)
    return AgentResult[Any](
        agent=agent,
        status=AgentStatus.OK,
        started_at=started_at,
        finished_at=finished_at,
        data=data,
        errors=[],
    )


def _sample_report() -> InvestigationReport:
    resource_id = (
        "/subscriptions/sub-123/resourceGroups/rg/providers/"
        "Microsoft.Compute/virtualMachines/vm-test-1"
    )
    cost_result = _agent_result(
        AgentName.COST,
        InvestigationFindings(
            alert_id="alert-discord-001",
            received_at=datetime(2026, 2, 11, 5, 0, tzinfo=timezone.utc),
            cost_findings=[
                CostFinding(resource_id=resource_id, cost=210.75, currency="USD")
            ],
            notes="",
        ),
    )

    findings = UnifiedFindings.merge(
        [cost_result],
        alert_summary={"alert_id": "alert-discord-001"},
    )

    diagnosis_result = _agent_result(
        AgentName.DIAGNOSIS,
        Diagnosis(
            hypothesis=RootCauseHypothesis(
                title="GPU VM left running",
                explanation="Cost spike maps to an always-on VM with no shutdown schedule.",
                evidence=["vm-test-1 is top cost driver"],
            ),
            confidence=85,
            alternatives=["Legitimate workload"],
            risks=["Stopping can interrupt active jobs"],
        ),
    )

    remediation_result = _agent_result(
        AgentName.REMEDIATION,
        RemediationPlan(
            summary="Add shutdown automation",
            actions=[
                RemediationAction(
                    type=RemediationActionType.ADD_AUTO_SHUTDOWN,
                    target_resource_id=resource_id,
                    parameters={"schedule_utc": "22:00"},
                    risk_level=RemediationRiskLevel.LOW,
                )
            ],
            rollback_notes="Remove schedule if the anomaly is a false positive.",
        ),
    )

    return InvestigationReport(
        unified_findings=findings,
        diagnosis_result=diagnosis_result,
        remediation_result=remediation_result,
    )


def test_discord_formatting_returns_non_empty_content_with_key_details() -> None:
    report = _sample_report()

    formatted = format_investigation_report_for_discord(report)

    content = formatted["content"]
    assert isinstance(content, str)
    assert content.strip()
    assert "vm-test-1" in content
    assert "85%" in content

    embeds = formatted["embeds"]
    assert isinstance(embeds, list)
    assert len(embeds) == 1

    embed = embeds[0]
    assert embed["title"] == "Incident Investigation Complete"

    field_values = [field["value"] for field in embed["fields"]]
    assert any("GPU VM left running" in value for value in field_values)
    assert any("add_auto_shutdown" in value for value in field_values)

    components = formatted["components"]
    assert isinstance(components, list)
    assert len(components) == 1

    action_row = components[0]
    assert action_row["type"] == 1
    buttons = action_row["components"]
    assert len(buttons) == 3

    custom_ids = [button["custom_id"] for button in buttons]
    assert set(custom_ids) == {
        "approve_remediation:alert-discord-001",
        "reject_remediation:alert-discord-001",
        "investigate_more:alert-discord-001",
    }

    allowed_mentions = formatted["allowed_mentions"]
    assert allowed_mentions == {"parse": []}


def test_discord_formatting_payload_is_json_serializable() -> None:
    report = _sample_report()

    formatted = format_investigation_report_for_discord(report)

    serialized = json.dumps(formatted)
    assert isinstance(serialized, str)
    assert serialized
