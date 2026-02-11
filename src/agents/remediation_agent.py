from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Mapping

from pydantic import BaseModel

from llm import FoundryClient
from llm import FoundryError
from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.remediation import RemediationAction
from models.remediation import RemediationActionType
from models.remediation import RemediationPlan
from models.remediation import RemediationRiskLevel


class RemediationAgent:
    def __init__(self, *, foundry_client: FoundryClient | None = None) -> None:
        self._foundry_client = foundry_client

    def run(
        self,
        unified_findings: Mapping[str, Any] | BaseModel,
        diagnosis: Mapping[str, Any] | BaseModel | Any,
    ) -> AgentResult[RemediationPlan]:
        started_at = datetime.now(timezone.utc)

        findings_payload = self._to_mapping(unified_findings)
        diagnosis_payload = self._to_mapping(diagnosis)
        target_resource_id = self._resolve_target_resource_id(findings_payload)

        llm_errors: list[str] = []
        llm_plan = self._build_llm_plan_if_configured(
            findings_payload=findings_payload,
            diagnosis_payload=diagnosis_payload,
            target_resource_id=target_resource_id,
        )
        if llm_plan is not None:
            return AgentResult[RemediationPlan](
                agent=AgentName.REMEDIATION,
                status=AgentStatus.OK,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                data=llm_plan,
                errors=[],
            )

        if self._should_report_llm_error():
            llm_errors = [
                "Foundry remediation generation unavailable; used rules fallback."
            ]

        fallback_plan = self._build_rules_plan(
            diagnosis_payload=diagnosis_payload,
            target_resource_id=target_resource_id,
        )

        status = AgentStatus.DEGRADED if llm_errors else AgentStatus.OK
        return AgentResult[RemediationPlan](
            agent=AgentName.REMEDIATION,
            status=status,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            data=fallback_plan,
            errors=llm_errors,
        )

    def _build_llm_plan_if_configured(
        self,
        *,
        findings_payload: Mapping[str, Any],
        diagnosis_payload: Mapping[str, Any],
        target_resource_id: str,
    ) -> RemediationPlan | None:
        client = self._foundry_client
        if client is None:
            return None

        system_prompt = (
            "You generate safe remediation plans for cloud cost anomalies. "
            "Return JSON only matching the RemediationPlan schema. "
            "Always keep human_approval_required=true for every action."
        )
        user_prompt = (
            "Create remediation actions for the following diagnosis and findings.\n"
            f"Diagnosis: {diagnosis_payload}\n"
            f"Unified findings: {findings_payload}\n"
            f"Primary target resource: {target_resource_id}\n"
            "Prefer low-risk actions first."
        )

        try:
            payload = client.complete_json(system_prompt, user_prompt, RemediationPlan)
        except FoundryError:
            return None

        return RemediationPlan.model_validate(payload)

    def _build_rules_plan(
        self,
        *,
        diagnosis_payload: Mapping[str, Any],
        target_resource_id: str,
    ) -> RemediationPlan:
        diagnosis_text = self._diagnosis_text(diagnosis_payload).lower()
        actions: list[RemediationAction] = []
        action_reasons: list[str] = []

        mentions_gpu_vm = "gpu vm" in diagnosis_text or (
            "gpu" in diagnosis_text and "vm" in diagnosis_text
        )
        mentions_no_shutdown = any(
            phrase in diagnosis_text
            for phrase in (
                "no shutdown",
                "without auto-shutdown",
                "missing auto-shutdown",
                "shutdown missing",
                "shutdown disabled",
            )
        )
        vm_running_unexpectedly = any(
            phrase in diagnosis_text
            for phrase in (
                "running unexpectedly",
                "left running",
                "running longer than intended",
            )
        )

        if mentions_gpu_vm and mentions_no_shutdown:
            actions.append(
                RemediationAction(
                    type=RemediationActionType.ADD_AUTO_SHUTDOWN,
                    target_resource_id=target_resource_id,
                    parameters={
                        "schedule_utc": "22:00",
                        "timezone": "UTC",
                        "reason": "Prevent overnight idle GPU spend",
                    },
                    risk_level=RemediationRiskLevel.LOW,
                )
            )
            action_reasons.append("Detected GPU VM without shutdown automation")

        if vm_running_unexpectedly:
            actions.append(
                RemediationAction(
                    type=RemediationActionType.STOP_VM,
                    target_resource_id=target_resource_id,
                    parameters={
                        "mode": "deallocate",
                        "reason": "Unexpected runtime outside planned usage",
                    },
                    risk_level=RemediationRiskLevel.MEDIUM,
                )
            )
            action_reasons.append("VM appears to be running unexpectedly")

        if not actions:
            actions.append(
                RemediationAction(
                    type=RemediationActionType.NOTIFY_OWNER,
                    target_resource_id=target_resource_id,
                    parameters={
                        "channel": "incident-war-room",
                        "message": "Review diagnosis and approve a remediation action.",
                    },
                    risk_level=RemediationRiskLevel.LOW,
                )
            )
            action_reasons.append("No deterministic infrastructure action matched")

        summary = "; ".join(action_reasons)
        return RemediationPlan(
            summary=summary,
            actions=actions,
            rollback_notes=(
                "If an approved action causes disruption, restore prior VM state "
                "or schedule and notify stakeholders in the incident channel."
            ),
        )

    def _resolve_target_resource_id(self, findings_payload: Mapping[str, Any]) -> str:
        cost_findings = findings_payload.get("cost_findings")
        if isinstance(cost_findings, list):
            for finding in cost_findings:
                if not isinstance(finding, Mapping):
                    continue
                resource_id = finding.get("resource_id")
                if resource_id:
                    return str(resource_id)

        alert_summary = findings_payload.get("alert_summary")
        if isinstance(alert_summary, Mapping):
            summary_resource_id = alert_summary.get("resource_id")
            if summary_resource_id:
                return str(summary_resource_id)

        return "unknown-resource"

    def _diagnosis_text(self, diagnosis_payload: Mapping[str, Any]) -> str:
        parts: list[str] = []
        hypothesis = diagnosis_payload.get("hypothesis")
        if isinstance(hypothesis, Mapping):
            for key in ("title", "explanation"):
                value = hypothesis.get(key)
                if value:
                    parts.append(str(value))
            evidence = hypothesis.get("evidence")
            if isinstance(evidence, list):
                parts.extend(str(item) for item in evidence if item)

        for key in ("alternatives", "risks"):
            value = diagnosis_payload.get(key)
            if isinstance(value, list):
                parts.extend(str(item) for item in value if item)

        title = diagnosis_payload.get("title")
        if title:
            parts.append(str(title))

        explanation = diagnosis_payload.get("explanation")
        if explanation:
            parts.append(str(explanation))

        return " ".join(parts)

    def _to_mapping(self, value: Any) -> dict[str, Any]:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, Mapping):
            return dict(value)

        if hasattr(value, "__dict__"):
            raw_dict = getattr(value, "__dict__")
            if isinstance(raw_dict, Mapping):
                return {str(key): raw_dict[key] for key in raw_dict}

        return {}

    def _should_report_llm_error(self) -> bool:
        return self._foundry_client is not None
