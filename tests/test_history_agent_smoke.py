from __future__ import annotations

from agents.history_agent import HistoryAgent
from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.history_findings import HistoryFindings
from storage.incident_search import LocalIncidentSearch
from storage.incident_store import MemoryIncidentStore


def _alert_payload() -> dict[str, object]:
    return {
        "alert_id": "alert-history-1",
        "summary": "GPU VM cost spike in production",
        "resource_id": "/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-gpu",
        "resource_type": "Microsoft.Compute/virtualMachines",
    }


def test_history_agent_returns_agent_result_with_history_name() -> None:
    store = MemoryIncidentStore()
    agent = HistoryAgent(store=store, search=LocalIncidentSearch(store))

    result = agent.run(_alert_payload())

    assert isinstance(result, AgentResult)
    assert result.agent == AgentName.HISTORY
    assert isinstance(result.data, HistoryFindings)


def test_history_agent_degrades_when_azure_backends_not_configured(monkeypatch) -> None:
    for env_var in (
        "COSMOS_ENDPOINT",
        "COSMOS_KEY",
        "COSMOS_DATABASE",
        "COSMOS_CONTAINER",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX",
    ):
        monkeypatch.delenv(env_var, raising=False)

    agent = HistoryAgent()
    result = agent.run(_alert_payload())

    assert result.status == AgentStatus.DEGRADED
    assert result.data is not None
    assert result.data.matches == []
    assert "Azure history backends not configured" in result.data.notes
