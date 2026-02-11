from __future__ import annotations

from datetime import datetime
from datetime import timezone

from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.findings import UnifiedFindings


def _agent_result(
    *,
    agent: AgentName,
    status: AgentStatus,
    data: dict[str, object],
    errors: list[str],
) -> AgentResult[dict[str, object]]:
    started = datetime(2026, 2, 11, 1, 0, tzinfo=timezone.utc)
    finished = datetime(2026, 2, 11, 1, 5, tzinfo=timezone.utc)
    return AgentResult[dict[str, object]](
        agent=agent,
        status=status,
        started_at=started,
        finished_at=finished,
        data=data,
        errors=errors,
    )


def test_merge_is_deterministic_across_input_order() -> None:
    cost = _agent_result(
        agent=AgentName.COST,
        status=AgentStatus.OK,
        data={"top_spend": "vm-1"},
        errors=[],
    )
    history = _agent_result(
        agent=AgentName.HISTORY,
        status=AgentStatus.DEGRADED,
        data={"incident_matches": 2},
        errors=["partial-history"],
    )

    merged_a = UnifiedFindings.merge([cost, history])
    merged_b = UnifiedFindings.merge([history, cost])

    assert merged_a.model_dump(mode="json") == merged_b.model_dump(mode="json")


def test_merge_preserves_status_and_errors_by_agent() -> None:
    resource = _agent_result(
        agent=AgentName.RESOURCE,
        status=AgentStatus.ERROR,
        data={"resource_id": "vm-2"},
        errors=["graph-query-timeout"],
    )
    diagnosis = _agent_result(
        agent=AgentName.DIAGNOSIS,
        status=AgentStatus.DEGRADED,
        data={"hypothesis": "burst usage"},
        errors=["insufficient-history"],
    )

    merged = UnifiedFindings.merge([resource, diagnosis])

    assert merged.results[AgentName.RESOURCE].status == AgentStatus.ERROR
    assert merged.results[AgentName.RESOURCE].errors == ["graph-query-timeout"]
    assert merged.results[AgentName.DIAGNOSIS].status == AgentStatus.DEGRADED
    assert merged.results[AgentName.DIAGNOSIS].errors == ["insufficient-history"]
