from __future__ import annotations

from agents.remediation_agent import RemediationAgent
from models.agent_protocol import AgentName
from models.agent_protocol import AgentStatus
from models.remediation import RemediationActionType
from models.remediation import RemediationPlan


def test_remediation_agent_returns_safe_actions_for_gpu_vm_without_shutdown() -> None:
    agent = RemediationAgent()

    result = agent.run(
        {
            "cost_findings": [
                {
                    "resource_id": "/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-gpu"
                }
            ]
        },
        {
            "hypothesis": {
                "title": "GPU VM left running without auto-shutdown",
                "explanation": "The VM was running unexpectedly and no shutdown schedule exists.",
                "evidence": [
                    "GPU VM was top cost driver",
                    "auto-shutdown is missing",
                    "vm left running",
                ],
            },
            "alternatives": ["legitimate workload spike"],
            "risks": ["stopping VM may impact active workloads"],
        },
    )

    assert result.agent == AgentName.REMEDIATION
    assert result.status == AgentStatus.OK
    assert isinstance(result.data, RemediationPlan)
    assert result.data is not None
    assert len(result.data.actions) >= 1
    assert all(action.human_approval_required for action in result.data.actions)

    action_types = {action.type for action in result.data.actions}
    assert RemediationActionType.ADD_AUTO_SHUTDOWN in action_types
    assert RemediationActionType.STOP_VM in action_types


def test_remediation_agent_fallback_action_still_requires_human_approval() -> None:
    agent = RemediationAgent()

    result = agent.run(
        {"alert_summary": {"resource_id": "vm-unknown"}},
        {
            "hypothesis": {
                "title": "Compute usage increase",
                "explanation": "No clear source was identified.",
                "evidence": ["incomplete telemetry"],
            }
        },
    )

    assert result.data is not None
    assert len(result.data.actions) >= 1
    assert result.data.actions[0].type == RemediationActionType.NOTIFY_OWNER
    assert all(action.human_approval_required for action in result.data.actions)
