from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Mapping

from agents.cost_analyst import CostAnalystAgent
from models.findings import InvestigationFindings


class CoordinatorAgent:
    def __init__(self, cost_analyst: CostAnalystAgent | None = None) -> None:
        self.cost_analyst = cost_analyst or CostAnalystAgent()
        self.last_alert_id: str | None = None
        self.last_received_at: datetime | None = None
        self.alert_history: dict[str, datetime] = {}

    def handle_alert(self, alert_payload: Mapping[str, Any]) -> InvestigationFindings:
        findings = self.cost_analyst.run(alert_payload)

        self.last_alert_id = findings.alert_id
        self.last_received_at = findings.received_at
        self.alert_history[findings.alert_id] = findings.received_at

        return findings
