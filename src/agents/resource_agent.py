from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Mapping
from typing import Sequence

from azure.activity_logs import list_activity_logs
from azure.auth import get_credential
from azure.auth import get_subscription_id
from azure.resource_graph import query_resources
from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.resource_findings import ResourceChange
from models.resource_findings import ResourceConfig
from models.resource_findings import ResourceFindings


class ResourceAgent:
    def __init__(self, *, lookback_days: int = 7) -> None:
        self.lookback_days = lookback_days

    def run(
        self,
        alert_payload: Mapping[str, Any],
        hints: Mapping[str, Any] | None = None,
    ) -> AgentResult[ResourceFindings]:
        started_at = datetime.now(timezone.utc)

        hinted_resource_id: str | None = None
        if hints:
            hinted_resource_id_value = hints.get("resource_id")
            if hinted_resource_id_value is not None:
                hinted_resource_id = str(hinted_resource_id_value)

        target_resource_id = self._resolve_target_resource_id(
            alert_payload, hinted_resource_id
        )

        if target_resource_id is None:
            note = "Unable to determine target resource_id from alert payload."
            findings = ResourceFindings(
                target_resource_id="unknown-resource",
                notes=note,
            )
            return self._build_result(
                status=AgentStatus.DEGRADED,
                started_at=started_at,
                findings=findings,
                errors=[note],
            )

        try:
            subscription_id = get_subscription_id()
            credential = get_credential()
        except RuntimeError as exc:
            note = str(exc)
            findings = ResourceFindings(
                target_resource_id=target_resource_id,
                notes=note,
            )
            return self._build_result(
                status=AgentStatus.DEGRADED,
                started_at=started_at,
                findings=findings,
                errors=[note],
            )

        notes: list[str] = []
        status = AgentStatus.OK

        try:
            config = self._query_resource_config(
                credential=credential,
                subscription_id=subscription_id,
                resource_id=target_resource_id,
            )
            if config is None:
                status = AgentStatus.DEGRADED
                notes.append(
                    "Resource Graph returned no matching resource configuration."
                )

            recent_changes = self._query_recent_changes(
                credential=credential,
                subscription_id=subscription_id,
                resource_id=target_resource_id,
            )
        except Exception as exc:  # pragma: no cover - Azure SDK errors vary
            note = f"Resource investigation failed: {exc}"
            findings = ResourceFindings(
                target_resource_id=target_resource_id,
                config=None,
                recent_changes=[],
                notes=note,
            )
            return self._build_result(
                status=AgentStatus.ERROR,
                started_at=started_at,
                findings=findings,
                errors=[note],
            )

        findings = ResourceFindings(
            target_resource_id=target_resource_id,
            config=config,
            recent_changes=recent_changes,
            notes=" ".join(notes),
        )
        return self._build_result(
            status=status,
            started_at=started_at,
            findings=findings,
            errors=notes,
        )

    def _resolve_target_resource_id(
        self,
        alert_payload: Mapping[str, Any],
        explicit_resource_id: str | None,
    ) -> str | None:
        if explicit_resource_id:
            return explicit_resource_id

        candidates: list[str] = []
        self._collect_resource_id_candidates(alert_payload, candidates)

        for candidate in candidates:
            cleaned = candidate.strip()
            if cleaned:
                return cleaned

        return None

    def _collect_resource_id_candidates(
        self,
        value: Any,
        candidates: list[str],
    ) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                key_name = str(key).lower()
                if key_name in {"resource_id", "resourceid", "resourceuri"}:
                    if isinstance(child, str):
                        candidates.append(child)
                elif key_name == "id" and isinstance(child, str):
                    if child.lower().startswith("/subscriptions/"):
                        candidates.append(child)

                if isinstance(child, Mapping) or isinstance(child, Sequence):
                    self._collect_resource_id_candidates(child, candidates)
            return

        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            for item in value:
                self._collect_resource_id_candidates(item, candidates)

    def _query_resource_config(
        self,
        *,
        credential: Any,
        subscription_id: str,
        resource_id: str,
    ) -> ResourceConfig | None:
        escaped_resource_id = resource_id.replace("'", "''")
        kql = "\n".join(
            [
                "Resources",
                f"| where id =~ '{escaped_resource_id}'",
                "| project id, name, type, location, tags, properties",
            ]
        )

        rows = query_resources(
            credential=credential,
            subscription_ids=[subscription_id],
            kql=kql,
        )

        if not rows:
            return None

        first_row = rows[0]
        tags = first_row.get("tags")
        properties = first_row.get("properties")

        normalized_tags: dict[str, str] = {}
        if isinstance(tags, dict):
            normalized_tags = {
                str(tag_key): str(tag_value) for tag_key, tag_value in tags.items()
            }

        normalized_properties: dict[str, Any] = {}
        if isinstance(properties, dict):
            normalized_properties = dict(properties)

        return ResourceConfig(
            resource_id=str(first_row.get("id") or resource_id),
            name=str(first_row.get("name") or "unknown-resource"),
            type=str(first_row.get("type") or "unknown-type"),
            location=str(first_row.get("location") or "unknown-location"),
            tags=normalized_tags,
            properties=normalized_properties,
        )

    def _query_recent_changes(
        self,
        *,
        credential: Any,
        subscription_id: str,
        resource_id: str,
    ) -> list[ResourceChange]:
        end_utc = datetime.now(timezone.utc)
        start_utc = end_utc - timedelta(days=self.lookback_days)

        activity_rows = list_activity_logs(
            credential=credential,
            subscription_id=subscription_id,
            start_utc=start_utc,
            end_utc=end_utc,
            resource_id=resource_id,
        )

        return [
            ResourceChange(
                timestamp=self._parse_timestamp(row.get("timestamp")),
                caller=str(row.get("caller") or "unknown"),
                operation=str(row.get("operation") or "unknown"),
                status=str(row.get("status") or "unknown"),
            )
            for row in activity_rows
        ]

    def _parse_timestamp(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        if isinstance(value, str):
            parsed_value = value.strip()
            if parsed_value.endswith("Z"):
                parsed_value = f"{parsed_value[:-1]}+00:00"

            try:
                parsed = datetime.fromisoformat(parsed_value)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                pass

        return datetime.fromtimestamp(0, tz=timezone.utc)

    def _build_result(
        self,
        *,
        status: AgentStatus,
        started_at: datetime,
        findings: ResourceFindings,
        errors: list[str],
    ) -> AgentResult[ResourceFindings]:
        return AgentResult[ResourceFindings](
            agent=AgentName.RESOURCE,
            status=status,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            data=findings,
            errors=errors,
        )
