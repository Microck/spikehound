from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Mapping

from azure.auth import get_credential
from azure.auth import get_subscription_id
from azure.cost_management import query_last_7_days_costs_by_resource
from azure.cost_management import rows_to_cost_items
from models.findings import CostFinding
from models.findings import InvestigationFindings


class CostAnalystAgent:
    def __init__(self, *, top_n: int = 5) -> None:
        self.top_n = top_n

    def run(self, alert_payload: Mapping[str, Any]) -> InvestigationFindings:
        alert_id = self._extract_alert_id(alert_payload)
        received_at = datetime.now(timezone.utc)

        try:
            subscription_id = get_subscription_id()
        except RuntimeError as exc:
            return InvestigationFindings(
                alert_id=alert_id,
                received_at=received_at,
                cost_findings=[],
                notes=str(exc),
            )

        try:
            result = query_last_7_days_costs_by_resource(
                get_credential(), subscription_id
            )
            cost_items = rows_to_cost_items(result)
        except Exception as exc:
            return InvestigationFindings(
                alert_id=alert_id,
                received_at=received_at,
                cost_findings=[],
                notes=f"Unable to query Azure Cost Management: {exc}",
            )

        findings = self._to_findings(cost_items)
        return InvestigationFindings(
            alert_id=alert_id,
            received_at=received_at,
            cost_findings=findings,
            notes="",
        )

    def _extract_alert_id(self, payload: Mapping[str, Any]) -> str:
        alert_id = payload.get("alert_id") or payload.get("id")
        if alert_id is None:
            return "unknown-alert"
        return str(alert_id)

    def _to_findings(self, cost_items: list[dict[str, Any]]) -> list[CostFinding]:
        sorted_items = sorted(
            cost_items,
            key=lambda item: self._coerce_cost(item.get("total_cost")),
            reverse=True,
        )

        findings: list[CostFinding] = []
        for item in sorted_items[: self.top_n]:
            resource_id = str(item.get("resource_id") or "unknown-resource")
            currency = str(item.get("currency") or "unknown")
            findings.append(
                CostFinding(
                    resource_id=resource_id,
                    cost=self._coerce_cost(item.get("total_cost")),
                    currency=currency,
                )
            )
        return findings

    def _coerce_cost(self, value: Any) -> float:
        try:
            cost = float(value)
        except (TypeError, ValueError):
            return 0.0
        if cost < 0:
            return 0.0
        return cost
