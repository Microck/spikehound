from __future__ import annotations

from datetime import datetime
from datetime import timezone
import os
from typing import Any
from typing import Mapping

from models.agent_protocol import AgentName
from models.agent_protocol import AgentResult
from models.agent_protocol import AgentStatus
from models.history_findings import HistoryFindings
from models.history_findings import SimilarIncident
from storage.ai_search_incident_search import AzureAISearchIncidentSearch
from storage.cosmos_incident_store import CosmosIncidentStore
from storage.incident_search import IncidentSearch
from storage.incident_search import LocalIncidentSearch
from storage.incident_store import IncidentRecord
from storage.incident_store import IncidentStore
from storage.incident_store import MemoryIncidentStore


class HistoryAgent:
    def __init__(
        self,
        *,
        store: IncidentStore | None = None,
        search: IncidentSearch | None = None,
        top_k: int = 5,
    ) -> None:
        self._store = store
        self._search = search
        self._top_k = top_k

    def run(
        self,
        alert_payload: Mapping[str, Any],
        unified_findings_hint: Mapping[str, Any] | None = None,
    ) -> AgentResult[HistoryFindings]:
        started_at = datetime.now(timezone.utc)
        query = self._build_query(alert_payload, unified_findings_hint)

        status = AgentStatus.OK
        errors: list[str] = []

        store, search, setup_issues, should_return_empty = self._resolve_dependencies()
        if setup_issues:
            status = AgentStatus.DEGRADED
            errors.extend(setup_issues)

        record = self._build_record(alert_payload, query, started_at)
        try:
            store.put(record)
        except Exception as exc:
            status = AgentStatus.DEGRADED
            errors.append(f"Incident persistence unavailable: {exc}")

        matches: list[SimilarIncident] = []
        if not should_return_empty:
            try:
                hits = search.search_similar(query, self._top_k)
                matches = self._to_similar_incidents(hits, store)
            except Exception as exc:
                status = AgentStatus.DEGRADED
                errors.append(f"Incident search unavailable: {exc}")

        findings = HistoryFindings(
            query=query,
            matches=matches,
            notes="; ".join(self._unique(errors)),
        )

        return AgentResult[HistoryFindings](
            agent=AgentName.HISTORY,
            status=status,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            data=findings,
            errors=self._unique(errors),
        )

    def _resolve_dependencies(
        self,
    ) -> tuple[IncidentStore, IncidentSearch, list[str], bool]:
        if self._store is not None and self._search is not None:
            return self._store, self._search, [], False

        if self._store is not None:
            return (
                self._store,
                self._search or LocalIncidentSearch(self._store),
                [],
                False,
            )

        if self._search is not None:
            store = MemoryIncidentStore()
            return store, self._search, [], False

        missing_backend_vars = self._missing_backend_env_vars()
        if missing_backend_vars:
            issue = (
                "Azure history backends not configured: "
                f"{', '.join(missing_backend_vars)}"
            )
            fallback_store = MemoryIncidentStore()
            return fallback_store, LocalIncidentSearch(fallback_store), [issue], True

        try:
            store = CosmosIncidentStore()
            search = AzureAISearchIncidentSearch()
            return store, search, [], False
        except RuntimeError as exc:
            fallback_store = MemoryIncidentStore()
            return fallback_store, LocalIncidentSearch(fallback_store), [str(exc)], True

    @staticmethod
    def _missing_backend_env_vars() -> list[str]:
        required = (
            "COSMOS_ENDPOINT",
            "COSMOS_KEY",
            "COSMOS_DATABASE",
            "COSMOS_CONTAINER",
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SEARCH_API_KEY",
            "AZURE_SEARCH_INDEX",
        )
        return [name for name in required if not os.getenv(name)]

    def _build_query(
        self,
        alert_payload: Mapping[str, Any],
        unified_findings_hint: Mapping[str, Any] | None,
    ) -> str:
        query_parts: list[str] = []

        for key in (
            "summary",
            "resource_id",
            "resource_name",
            "resource_type",
            "anomaly_type",
            "title",
        ):
            value = alert_payload.get(key)
            if value:
                query_parts.append(str(value))

        if unified_findings_hint:
            query_parts.extend(self._extract_hint_terms(unified_findings_hint))

        normalized = [
            part.strip() for part in query_parts if part and str(part).strip()
        ]
        if not normalized:
            return "cost anomaly incident"

        return " ".join(self._unique(normalized))

    @staticmethod
    def _extract_hint_terms(unified_findings_hint: Mapping[str, Any]) -> list[str]:
        terms: list[str] = []
        cost_findings = unified_findings_hint.get("cost_findings")
        if isinstance(cost_findings, list):
            for finding in cost_findings:
                if not isinstance(finding, Mapping):
                    continue
                resource_id = finding.get("resource_id")
                if resource_id:
                    terms.append(str(resource_id))
                total_cost = finding.get("cost") or finding.get("total_cost")
                if total_cost:
                    terms.append(str(total_cost))

        alert_summary = unified_findings_hint.get("alert_summary")
        if isinstance(alert_summary, Mapping):
            summary_text = alert_summary.get("summary")
            if summary_text:
                terms.append(str(summary_text))

        return terms

    @staticmethod
    def _build_record(
        alert_payload: Mapping[str, Any],
        query: str,
        timestamp: datetime,
    ) -> IncidentRecord:
        alert_id = alert_payload.get("alert_id") or alert_payload.get("id")
        incident_id = str(alert_id or f"incident-{int(timestamp.timestamp())}")
        title = str(
            alert_payload.get("title") or alert_payload.get("summary") or incident_id
        )
        summary = str(alert_payload.get("summary") or query)
        resolution = str(alert_payload.get("resolution") or "")

        tags: list[str] = []
        for key in ("anomaly_type", "resource_type"):
            value = alert_payload.get(key)
            if value:
                tags.append(str(value))

        return IncidentRecord(
            id=incident_id,
            created_at=timestamp,
            title=title,
            summary=summary,
            resolution=resolution,
            tags=HistoryAgent._unique(tags),
            raw=dict(alert_payload),
        )

    @staticmethod
    def _to_similar_incidents(
        hits: list[dict[str, Any]],
        store: IncidentStore,
    ) -> list[SimilarIncident]:
        matches: list[SimilarIncident] = []
        for hit in hits:
            incident_id = hit.get("id")
            if not incident_id:
                continue

            incident_id_str = str(incident_id)
            score = HistoryAgent._to_float_or_none(hit.get("score"))
            record = store.get(incident_id_str)
            if record is None:
                matches.append(
                    SimilarIncident(
                        id=incident_id_str,
                        title=str(hit.get("title") or incident_id_str),
                        summary=str(hit.get("summary") or ""),
                        resolution=str(hit.get("resolution") or ""),
                        score=score,
                    )
                )
                continue

            matches.append(
                SimilarIncident(
                    id=record.id,
                    title=record.title,
                    summary=record.summary,
                    resolution=record.resolution,
                    score=score,
                )
            )

        return matches

    @staticmethod
    def _to_float_or_none(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))
