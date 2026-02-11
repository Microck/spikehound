from __future__ import annotations

from datetime import datetime
from datetime import timezone
import json
from typing import Any
from typing import Mapping

from pydantic import BaseModel
from pydantic import Field

from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.diagnosis import Diagnosis
from models.remediation import RemediationPlan


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
    alert_id: str = Field(default="unknown-alert")
    received_at: datetime = Field(
        default_factory=lambda: datetime.fromtimestamp(0, tz=timezone.utc)
    )
    cost_findings: list[CostFinding] = Field(default_factory=list)
    resource_findings: dict[str, Any] | None = None
    history_findings: dict[str, Any] | None = None
    notes: str = ""

    @classmethod
    def merge(
        cls,
        results: list[AgentResult[Any]],
        alert_summary: Mapping[str, Any] | None = None,
    ) -> "UnifiedFindings":
        merged_results: dict[AgentName, AgentResult[Any]] = {}
        for result in sorted(results, key=cls._result_sort_key):
            merged_results[result.agent] = result

        summary = dict(alert_summary or {})
        alert_id = str(summary.get("alert_id") or "unknown-alert")
        received_at = cls._coerce_datetime(summary.get("received_at"))
        cost_findings: list[CostFinding] = []
        resource_findings: dict[str, Any] | None = None
        history_findings: dict[str, Any] | None = None
        notes = ""

        cost_result = merged_results.get(AgentName.COST)
        if cost_result and isinstance(cost_result.data, InvestigationFindings):
            alert_id = cost_result.data.alert_id
            received_at = cost_result.data.received_at
            cost_findings = list(cost_result.data.cost_findings)
            notes = cost_result.data.notes

        resource_result = merged_results.get(AgentName.RESOURCE)
        if resource_result and resource_result.data is not None:
            resource_findings = cls._dump_model(resource_result.data)

        history_result = merged_results.get(AgentName.HISTORY)
        if history_result and history_result.data is not None:
            history_findings = cls._dump_model(history_result.data)

        return cls(
            alert_summary=summary,
            results=merged_results,
            alert_id=alert_id,
            received_at=received_at,
            cost_findings=cost_findings,
            resource_findings=resource_findings,
            history_findings=history_findings,
            notes=notes,
        )

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        if isinstance(value, str):
            normalized = value.strip()
            if normalized.endswith("Z"):
                normalized = f"{normalized[:-1]}+00:00"
            try:
                parsed = datetime.fromisoformat(normalized)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                pass

        return datetime.fromtimestamp(0, tz=timezone.utc)

    @staticmethod
    def _dump_model(data: Any) -> dict[str, Any]:
        if isinstance(data, BaseModel):
            return data.model_dump(mode="json")
        if isinstance(data, Mapping):
            return dict(data)
        return {"value": data}

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


class InvestigationReport(BaseModel):
    unified_findings: UnifiedFindings
    diagnosis_result: AgentResult[Diagnosis]
    remediation_result: AgentResult[RemediationPlan]
