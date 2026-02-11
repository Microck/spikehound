from __future__ import annotations

import agents.resource_agent as resource_agent_module
from agents.resource_agent import ResourceAgent
from models.agent_protocol import AgentName
from models.agent_protocol import AgentStatus
from models.resource_findings import ResourceFindings


def test_resource_agent_returns_resource_result_without_azure_creds(
    monkeypatch,
) -> None:
    fake_resource_id = (
        "/subscriptions/sub-123/resourceGroups/rg-cost/providers/"
        "Microsoft.Compute/virtualMachines/vm-cost"
    )

    def fake_get_subscription_id() -> str:
        raise RuntimeError("Missing AZURE_SUBSCRIPTION_ID")

    monkeypatch.setattr(
        resource_agent_module,
        "get_subscription_id",
        fake_get_subscription_id,
    )

    result = ResourceAgent().run(
        {"alert_id": "alert-1", "resource_id": fake_resource_id}
    )

    assert result.agent == AgentName.RESOURCE
    assert result.status == AgentStatus.DEGRADED
    assert isinstance(result.data, ResourceFindings)
    assert result.data is not None
    assert result.data.target_resource_id == fake_resource_id
    assert result.data.notes
    assert result.errors
