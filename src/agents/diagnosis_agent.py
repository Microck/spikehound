from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Mapping
from typing import Sequence

from pydantic import BaseModel

from llm.foundry_client import FoundryClient
from llm.foundry_client import FoundryError
from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.diagnosis import Diagnosis
from models.diagnosis import RootCauseHypothesis
from models.findings import UnifiedFindings


class DiagnosisAgent:
    def __init__(self, *, foundry_client: FoundryClient | None = None) -> None:
        self._foundry_client = foundry_client or FoundryClient()

    def run(
        self, unified_findings: UnifiedFindings | Mapping[str, Any]
    ) -> AgentResult[Diagnosis]:
        started_at = datetime.now(timezone.utc)
        normalized_findings = self._to_plain_data(unified_findings)

        errors: list[str] = []
        status = AgentStatus.OK
        try:
            diagnosis_payload = self._foundry_client.complete_json(
                self._system_prompt(),
                self._user_prompt(normalized_findings),
                Diagnosis,
            )
            diagnosis = Diagnosis.model_validate(diagnosis_payload)
        except FoundryError as exc:
            status = AgentStatus.DEGRADED
            errors.append(str(exc))
            diagnosis = self._fallback_diagnosis(normalized_findings)
        except Exception as exc:  # pragma: no cover - defensive fallback
            status = AgentStatus.DEGRADED
            errors.append(f"Diagnosis generation failed: {exc}")
            diagnosis = self._fallback_diagnosis(normalized_findings)

        return AgentResult[Diagnosis](
            agent=AgentName.DIAGNOSIS,
            status=status,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            data=diagnosis,
            errors=errors,
        )

    def _system_prompt(self) -> str:
        return (
            "You are a diagnosis agent for Azure cost anomalies. "
            "Synthesize findings into a single actionable root-cause hypothesis. "
            "Return only valid JSON with this schema: "
            '{"hypothesis":{"title":"string","explanation":"string","evidence":["string"]},'
            '"confidence":0,"alternatives":["string"],"risks":["string"]}. '
            "Use confidence as an integer between 0 and 100. "
            "Provide 3-6 evidence items, at least 2 alternatives, and at least 1 risk."
        )

    def _user_prompt(self, findings: dict[str, Any]) -> str:
        top_cost_drivers = self._format_top_cost_drivers(findings)
        resource_changes = self._format_resource_changes(findings)
        history_matches = self._format_history_matches(findings)

        return "\n".join(
            [
                "Investigation findings:",
                "",
                "Top cost drivers:",
                *top_cost_drivers,
                "",
                "Key resource changes:",
                *resource_changes,
                "",
                "Similar incidents and resolutions:",
                *history_matches,
                "",
                "Return diagnosis JSON only.",
            ]
        )

    def _fallback_diagnosis(self, findings: dict[str, Any]) -> Diagnosis:
        cost_findings = self._extract_cost_findings(findings)
        resource_findings = self._extract_resource_findings(findings)
        history_findings = self._extract_history_findings(findings)

        top_driver = self._top_cost_driver(cost_findings)
        power_state = self._infer_power_state(resource_findings)
        looks_like_vm = self._looks_like_vm(
            top_driver=top_driver,
            resource_findings=resource_findings,
        )
        shutdown_indicator = self._missing_shutdown_indicator(resource_findings)
        has_intentional_change = self._has_intentional_change_window(resource_findings)
        historical_match = self._first_history_match(history_findings)

        if top_driver is None:
            title = "Unattributed cost increase"
            confidence = 40
            explanation = (
                "The findings do not include a reliable top cost-driving resource id, so cost attribution is incomplete. "
                "Resource and history signals were reviewed, but none can be tied to a confirmed primary cost source. "
                "This incident is treated as a general compute cost increase until richer attribution data is available."
            )
        elif looks_like_vm and power_state == "running" and shutdown_indicator:
            title = "GPU VM left running without auto-shutdown"
            confidence = 80
            explanation = (
                f"The top cost driver is {top_driver['resource_id']} and it appears to still be running. "
                f"A shutdown policy signal indicates missing or disabled automation ({shutdown_indicator}). "
                "This pattern strongly matches runaway spend caused by a GPU VM left on outside intended windows."
            )
        elif looks_like_vm and power_state == "running" and not has_intentional_change:
            title = "VM running longer than intended"
            confidence = 60
            explanation = (
                f"The top cost driver is {top_driver['resource_id']} and runtime indicators show it is running. "
                "Recent resource-change history does not show a clear deployment or maintenance window that explains prolonged uptime. "
                "The most likely cause is extended VM runtime beyond the intended schedule."
            )
        elif historical_match is not None:
            title = "Recurring cost anomaly similar to past incident"
            confidence = 55
            explanation = (
                f"A prior incident ({historical_match.get('title') or historical_match.get('id')}) closely resembles this anomaly. "
                "The current findings align with a previously seen pattern and include a known resolution reference. "
                "This suggests recurrence of an earlier operational issue rather than a novel failure mode."
            )
        else:
            title = "Compute usage increase"
            confidence = 40
            explanation = (
                "Cost findings show elevated compute spend, but no single deterministic misconfiguration is confirmed. "
                "Resource state and change history provide partial context without a definitive root-cause signature. "
                "Treating this as a broader compute usage increase is the most reliable interim diagnosis."
            )

        evidence = self._build_evidence(
            findings=findings,
            top_driver=top_driver,
            power_state=power_state,
            shutdown_indicator=shutdown_indicator,
            has_intentional_change=has_intentional_change,
            historical_match=historical_match,
        )
        alternatives = [
            "Legitimate workload spike",
            "Misconfigured schedule or automation policy",
            "Resource leak causing sustained compute usage",
        ]
        risks = ["Stopping VM may disrupt active jobs"]

        return Diagnosis(
            hypothesis=RootCauseHypothesis(
                title=title,
                explanation=explanation,
                evidence=evidence,
            ),
            confidence=confidence,
            alternatives=alternatives,
            risks=risks,
        )

    def _extract_cost_findings(self, findings: dict[str, Any]) -> list[dict[str, Any]]:
        top_level = findings.get("cost_findings")
        if isinstance(top_level, list):
            return [item for item in top_level if isinstance(item, Mapping)]

        cost_result_data = self._extract_result_data(findings, AgentName.COST.value)
        if isinstance(cost_result_data, Mapping):
            nested = cost_result_data.get("cost_findings")
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, Mapping)]

        return []

    def _extract_resource_findings(self, findings: dict[str, Any]) -> dict[str, Any]:
        resource_findings = findings.get("resource_findings")
        if isinstance(resource_findings, Mapping):
            return dict(resource_findings)

        resource_result_data = self._extract_result_data(
            findings, AgentName.RESOURCE.value
        )
        if isinstance(resource_result_data, Mapping):
            return dict(resource_result_data)

        return {}

    def _extract_history_findings(self, findings: dict[str, Any]) -> dict[str, Any]:
        history_findings = findings.get("history_findings")
        if isinstance(history_findings, Mapping):
            return dict(history_findings)

        history_result_data = self._extract_result_data(
            findings, AgentName.HISTORY.value
        )
        if isinstance(history_result_data, Mapping):
            return dict(history_result_data)

        return {}

    def _extract_result_data(
        self,
        findings: dict[str, Any],
        agent_name: str,
    ) -> dict[str, Any] | None:
        results = findings.get("results")
        if not isinstance(results, Mapping):
            return None

        for key, value in results.items():
            key_name = str(key)
            if key_name != agent_name:
                continue

            if isinstance(value, Mapping):
                data = value.get("data")
                if isinstance(data, Mapping):
                    return dict(data)
            return None

        return None

    def _top_cost_driver(
        self,
        cost_findings: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not cost_findings:
            return None

        best = max(
            cost_findings,
            key=lambda item: self._to_float(item.get("cost") or item.get("total_cost")),
        )
        resource_id = str(best.get("resource_id") or "").strip()
        if not resource_id:
            return None

        return {
            "resource_id": resource_id,
            "cost": self._to_float(best.get("cost") or best.get("total_cost")),
            "currency": str(best.get("currency") or "USD"),
        }

    def _looks_like_vm(
        self,
        *,
        top_driver: dict[str, Any] | None,
        resource_findings: dict[str, Any],
    ) -> bool:
        candidates: list[str] = []

        if top_driver is not None:
            candidates.append(str(top_driver.get("resource_id") or ""))

        config = resource_findings.get("config")
        if isinstance(config, Mapping):
            candidates.append(str(config.get("type") or ""))
            candidates.append(str(config.get("name") or ""))

        combined = " ".join(candidates).lower()
        return (
            "virtualmachines" in combined
            or "microsoft.compute/virtualmachines" in combined
            or " vm" in f" {combined}"
        )

    def _infer_power_state(self, resource_findings: dict[str, Any]) -> str:
        config = resource_findings.get("config")
        search_space: list[Any] = [resource_findings]
        if isinstance(config, Mapping):
            search_space.append(config.get("properties"))

        text = " ".join(self._collect_text_fragments(search_space)).lower()
        if "powerstate/running" in text or " running" in f" {text}":
            return "running"
        if (
            "deallocated" in text
            or "powerstate/stopped" in text
            or "stopped" in text
            or "deallocated" in text
        ):
            return "stopped"
        return "unknown"

    def _missing_shutdown_indicator(
        self,
        resource_findings: dict[str, Any],
    ) -> str | None:
        for key_path, value in self._walk_key_values(resource_findings):
            key_lower = key_path.lower()
            if not any(term in key_lower for term in ("shutdown", "schedule", "auto")):
                continue

            if isinstance(value, bool) and not value:
                return f"{key_path}=false"

            value_text = str(value).strip().lower()
            if not value_text:
                continue

            if any(
                term in value_text for term in ("missing", "disabled", "false", "none")
            ):
                return f"{key_path}={value_text}"

        notes = str(resource_findings.get("notes") or "")
        notes_lower = notes.lower()
        if any(
            term in notes_lower for term in ("auto-shutdown", "shutdown", "schedule")
        ) and any(term in notes_lower for term in ("missing", "disabled")):
            return notes.strip()

        return None

    def _has_intentional_change_window(self, resource_findings: dict[str, Any]) -> bool:
        changes = resource_findings.get("recent_changes")
        if not isinstance(changes, list):
            return False

        operation_keywords = (
            "deploy",
            "write",
            "create",
            "update",
            "start",
            "scale",
            "restart",
        )
        for change in changes:
            if not isinstance(change, Mapping):
                continue

            operation = str(change.get("operation") or "").lower()
            if any(keyword in operation for keyword in operation_keywords):
                return True

        return False

    def _first_history_match(
        self,
        history_findings: dict[str, Any],
    ) -> dict[str, Any] | None:
        matches = history_findings.get("matches")
        if not isinstance(matches, list):
            return None

        for match in matches:
            if isinstance(match, Mapping):
                return dict(match)
        return None

    def _build_evidence(
        self,
        *,
        findings: dict[str, Any],
        top_driver: dict[str, Any] | None,
        power_state: str,
        shutdown_indicator: str | None,
        has_intentional_change: bool,
        historical_match: dict[str, Any] | None,
    ) -> list[str]:
        evidence: list[str] = []

        if top_driver is None:
            evidence.append(
                "- Top cost driver was unavailable in UnifiedFindings cost section"
            )
        else:
            evidence.append(
                "- Top cost driver: "
                f"{top_driver['resource_id']} (~{top_driver['cost']:.2f} {top_driver['currency']})"
            )

        evidence.append(f"- Inferred resource power state: {power_state}")

        if shutdown_indicator:
            evidence.append(
                f"- Missing/disabled shutdown indicator: {shutdown_indicator}"
            )

        if power_state == "running" and not has_intentional_change:
            evidence.append(
                "- No recent deployment/change window indicates intentional extended runtime"
            )

        if historical_match is not None:
            title = (
                historical_match.get("title") or historical_match.get("id") or "unknown"
            )
            resolution = historical_match.get("resolution") or "no resolution captured"
            evidence.append(
                f"- Similar incident match: {title}; prior resolution: {resolution}"
            )

        alert_id = findings.get("alert_id")
        if alert_id is not None:
            evidence.append(f"- Alert id: {alert_id}")

        normalized = [item.strip() for item in evidence if item and item.strip()]
        deduped = list(dict.fromkeys(normalized))

        while len(deduped) < 3:
            deduped.append("- Additional telemetry required for stronger attribution")

        return deduped[:6]

    def _format_top_cost_drivers(self, findings: dict[str, Any]) -> list[str]:
        cost_findings = self._extract_cost_findings(findings)
        if not cost_findings:
            return ["- none"]

        sorted_findings = sorted(
            cost_findings,
            key=lambda item: self._to_float(item.get("cost") or item.get("total_cost")),
            reverse=True,
        )
        lines: list[str] = []
        for item in sorted_findings[:3]:
            resource_id = str(item.get("resource_id") or "unknown-resource")
            cost = self._to_float(item.get("cost") or item.get("total_cost"))
            currency = str(item.get("currency") or "USD")
            lines.append(f"- {resource_id}: {cost:.2f} {currency}")
        return lines

    def _format_resource_changes(self, findings: dict[str, Any]) -> list[str]:
        resource_findings = self._extract_resource_findings(findings)
        recent_changes = resource_findings.get("recent_changes")
        if not isinstance(recent_changes, list) or not recent_changes:
            notes = str(resource_findings.get("notes") or "").strip()
            if notes:
                return [f"- notes: {notes}"]
            return ["- none"]

        lines: list[str] = []
        for change in recent_changes[:3]:
            if not isinstance(change, Mapping):
                continue
            timestamp = str(change.get("timestamp") or "unknown-time")
            operation = str(change.get("operation") or "unknown-operation")
            status = str(change.get("status") or "unknown-status")
            caller = str(change.get("caller") or "unknown-caller")
            lines.append(f"- {timestamp}: {operation} ({status}) by {caller}")

        return lines or ["- none"]

    def _format_history_matches(self, findings: dict[str, Any]) -> list[str]:
        history_findings = self._extract_history_findings(findings)
        matches = history_findings.get("matches")
        if not isinstance(matches, list) or not matches:
            return ["- none"]

        lines: list[str] = []
        for match in matches[:3]:
            if not isinstance(match, Mapping):
                continue
            title = str(match.get("title") or match.get("id") or "unknown-incident")
            resolution = str(match.get("resolution") or "resolution not provided")
            score = match.get("score")
            if score is None:
                lines.append(f"- {title}: {resolution}")
            else:
                lines.append(f"- {title} (score={score}): {resolution}")
        return lines or ["- none"]

    def _to_plain_data(self, value: Any) -> dict[str, Any]:
        if isinstance(value, UnifiedFindings):
            return value.model_dump(mode="json")
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, Mapping):
            return {
                str(key): self._normalize_value(raw_value)
                for key, raw_value in value.items()
            }
        return {}

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, Mapping):
            return {
                str(key): self._normalize_value(raw_value)
                for key, raw_value in value.items()
            }
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            return [self._normalize_value(item) for item in value]
        return value

    def _collect_text_fragments(self, values: Sequence[Any]) -> list[str]:
        fragments: list[str] = []
        for value in values:
            if isinstance(value, Mapping):
                for key, child in value.items():
                    fragments.append(str(key))
                    fragments.extend(self._collect_text_fragments([child]))
            elif isinstance(value, Sequence) and not isinstance(
                value, (str, bytes, bytearray)
            ):
                fragments.extend(self._collect_text_fragments(list(value)))
            elif value is not None:
                fragments.append(str(value))
        return fragments

    def _walk_key_values(self, value: Any, prefix: str = "") -> list[tuple[str, Any]]:
        if isinstance(value, Mapping):
            rows: list[tuple[str, Any]] = []
            for key, child in value.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                rows.extend(self._walk_key_values(child, path))
            return rows
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            rows: list[tuple[str, Any]] = []
            for index, child in enumerate(value):
                path = f"{prefix}[{index}]" if prefix else f"[{index}]"
                rows.extend(self._walk_key_values(child, path))
            return rows
        return [(prefix or "value", value)]

    def _to_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
