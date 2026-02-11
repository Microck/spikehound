from __future__ import annotations

from datetime import datetime
import json
from typing import Any
from typing import Mapping

from pydantic import BaseModel
from pydantic import Field

from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult


class CostFinding(BaseModel):
    resource_id: str = Field(min_length=1)
    cost: float = Field(ge=0)
    currency: str = Field(min_length=1)


class InvestigationFindings(BaseModel):
    alert_id: str = Field(min_length=1)
    received_at: datetime
    cost_findings: list[CostFinding] = Field(default_factory=list)
    resource_findings: dict[str, Any] | None = None
    history_findings: dict[str, Any] | None = None
    notes: str = ""


class UnifiedFindings(BaseModel):
    alert_summary: dict[str, Any] = Field(default_factory=dict)
    results: dict[AgentName, AgentResult[Any]] = Field(default_factory=dict)

    @classmethod
    def merge(
        cls,
        results: list[AgentResult[Any]],
        alert_summary: Mapping[str, Any] | None = None,
    ) -> "UnifiedFindings":
        merged_results: dict[AgentName, AgentResult[Any]] = {}
        for result in sorted(results, key=cls._result_sort_key):
            merged_results[result.agent] = result

        return cls(
            alert_summary=dict(alert_summary or {}),
            results=merged_results,
        )

    @staticmethod
    def _result_sort_key(
        result: AgentResult[Any],
    ) -> tuple[str, str, str, str, str, str]:
        return (
            result.agent.value,
            result.finished_at.isoformat(),
            result.started_at.isoformat(),
            result.status.value,
            json.dumps(result.data, sort_keys=True, default=str),
            json.dumps(result.errors, sort_keys=True),
        )
