from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from azure.mgmt.costmanagement.models import QueryColumn
from azure.mgmt.costmanagement.models import QueryResult

import azure.cost_management as cost_management


def test_build_last_7_days_query_definition_shape() -> None:
    now = datetime(2026, 2, 11, 0, 0, 0, tzinfo=timezone.utc)

    definition = cost_management.build_last_7_days_query_definition(now=now)

    assert definition.type == "Usage"
    assert definition.timeframe == "Custom"
    assert definition.time_period is not None
    assert definition.time_period.from_property == now - timedelta(days=7)
    assert definition.time_period.to == now
    assert definition.dataset.granularity == "Daily"
    assert "totalCost" in definition.dataset.aggregation
    assert definition.dataset.aggregation["totalCost"].name == "PreTaxCost"
    assert definition.dataset.aggregation["totalCost"].function == "Sum"


def test_query_last_7_days_uses_subscription_scope_and_query_usage(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeQuery:
        def usage(self, scope: str, parameters: object) -> dict[str, bool]:
            captured["scope"] = scope
            captured["parameters"] = parameters
            return {"ok": True}

    class FakeClient:
        def __init__(self, credential: object) -> None:
            captured["credential"] = credential
            self.query = FakeQuery()

        def close(self) -> None:
            captured["closed"] = True

    monkeypatch.setattr(cost_management, "CostManagementClient", FakeClient)

    fake_credential = object()
    result = cost_management.query_last_7_days_costs_by_resource(
        fake_credential, "sub-123"
    )

    assert result == {"ok": True}
    assert captured["credential"] is fake_credential
    assert captured["scope"] == "/subscriptions/sub-123"
    assert getattr(captured["parameters"], "dataset", None) is not None
    assert captured["closed"] is True


def test_rows_to_cost_items_maps_expected_keys() -> None:
    result = QueryResult(
        columns=[
            QueryColumn(name="ResourceId", type="String"),
            QueryColumn(name="totalCost", type="Number"),
            QueryColumn(name="Currency", type="String"),
            QueryColumn(name="UsageDate", type="Number"),
        ],
        rows=[["resource-1", 42.5, "USD", 20260210]],
    )

    assert cost_management.rows_to_cost_items(result) == [
        {
            "resource_id": "resource-1",
            "total_cost": 42.5,
            "currency": "USD",
            "date": 20260210,
        }
    ]
