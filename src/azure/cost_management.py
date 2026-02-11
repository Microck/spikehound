from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryAggregation
from azure.mgmt.costmanagement.models import QueryDataset
from azure.mgmt.costmanagement.models import QueryDefinition
from azure.mgmt.costmanagement.models import QueryGrouping
from azure.mgmt.costmanagement.models import QueryTimePeriod


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_last_7_days_query_definition(now: datetime | None = None) -> QueryDefinition:
    end = _to_utc(now or datetime.now(timezone.utc))
    start = end - timedelta(days=7)

    return QueryDefinition(
        type="Usage",
        timeframe="Custom",
        time_period=QueryTimePeriod(from_property=start, to=end),
        dataset=QueryDataset(
            granularity="Daily",
            aggregation={
                "totalCost": QueryAggregation(name="PreTaxCost", function="Sum"),
            },
            grouping=[
                QueryGrouping(type="Dimension", name="ResourceId"),
                QueryGrouping(type="Dimension", name="Currency"),
                QueryGrouping(type="Dimension", name="UsageDate"),
            ],
        ),
    )


def query_last_7_days_costs_by_resource(credential: Any, subscription_id: str) -> Any:
    scope = f"/subscriptions/{subscription_id}"
    definition = build_last_7_days_query_definition()
    client = CostManagementClient(credential)
    try:
        return client.query.usage(scope, definition)
    finally:
        client.close()


def rows_to_cost_items(result: Any) -> list[dict[str, Any]]:
    columns = getattr(result, "columns", None) or []
    rows = getattr(result, "rows", None) or []
    if not columns or not rows:
        return []

    normalized_index: dict[str, int] = {}
    for idx, column in enumerate(columns):
        name = getattr(column, "name", None)
        if name:
            normalized_index[name.lower()] = idx

    required = ("resourceid", "totalcost", "usagedate")
    if not all(key in normalized_index for key in required):
        return []

    mapped_rows: list[dict[str, Any]] = []
    currency_idx = normalized_index.get("currency")

    for row in rows:
        if not isinstance(row, list):
            continue

        resource_idx = normalized_index["resourceid"]
        cost_idx = normalized_index["totalcost"]
        date_idx = normalized_index["usagedate"]
        if max(resource_idx, cost_idx, date_idx) >= len(row):
            continue

        currency_value = None
        if currency_idx is not None and currency_idx < len(row):
            currency_value = row[currency_idx]

        mapped_rows.append(
            {
                "resource_id": row[resource_idx],
                "total_cost": row[cost_idx],
                "currency": currency_value,
                "date": row[date_idx],
            }
        )

    return mapped_rows
