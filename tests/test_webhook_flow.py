from __future__ import annotations

from datetime import datetime
from datetime import timezone

from fastapi.testclient import TestClient

import web.app as web_app
from models.findings import CostFinding
from models.findings import InvestigationFindings


def test_webhook_alert_returns_structured_findings(monkeypatch) -> None:
    expected_findings = InvestigationFindings(
        alert_id="alert-123",
        received_at=datetime(2026, 2, 11, 0, 0, tzinfo=timezone.utc),
        cost_findings=[
            CostFinding(
                resource_id="/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                cost=125.5,
                currency="USD",
            )
        ],
        notes="stubbed",
    )

    def fake_run(_: dict[str, object]) -> InvestigationFindings:
        return expected_findings

    monkeypatch.setattr(web_app.coordinator_agent.cost_analyst, "run", fake_run)

    client = TestClient(web_app.app)
    response = client.post("/webhooks/alert", json={"alert_id": "alert-123"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["alert_id"] == "alert-123"
    assert "received_at" in payload
    assert payload["notes"] == "stubbed"
    assert payload["cost_findings"][0]["resource_id"].endswith("/vm1")
    assert payload["cost_findings"][0]["cost"] == 125.5
    assert payload["cost_findings"][0]["currency"] == "USD"
