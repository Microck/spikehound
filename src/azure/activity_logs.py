from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from azure.mgmt.monitor import MonitorManagementClient


def _to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        normalized = value.replace(tzinfo=timezone.utc)
    else:
        normalized = value.astimezone(timezone.utc)
    return normalized.strftime("%Y-%m-%dT%H:%M:%SZ")


def _escape_filter_value(value: str) -> str:
    return value.replace("'", "''")


def _extract_operation_name(event: Any) -> str:
    operation_name = getattr(event, "operation_name", None)
    localized_value = getattr(operation_name, "localized_value", None)
    if localized_value:
        return str(localized_value)

    value = getattr(operation_name, "value", None)
    if value:
        return str(value)

    return "unknown"


def _extract_status_name(event: Any) -> str:
    status = getattr(event, "status", None)
    localized_value = getattr(status, "localized_value", None)
    if localized_value:
        return str(localized_value)

    value = getattr(status, "value", None)
    if value:
        return str(value)

    return "unknown"


def _to_activity_log_row(event: Any) -> dict[str, Any]:
    timestamp = getattr(event, "event_timestamp", None)
    if isinstance(timestamp, datetime):
        timestamp_value = _to_utc_iso(timestamp)
    elif timestamp is None:
        timestamp_value = ""
    else:
        timestamp_value = str(timestamp)

    return {
        "timestamp": timestamp_value,
        "caller": str(getattr(event, "caller", "") or ""),
        "operation": _extract_operation_name(event),
        "status": _extract_status_name(event),
        "resource_id": str(getattr(event, "resource_id", "") or ""),
    }


def list_activity_logs(
    credential: Any,
    subscription_id: str,
    start_utc: datetime,
    end_utc: datetime,
    resource_id: str | None = None,
    resource_group: str | None = None,
) -> list[dict[str, Any]]:
    filters = [
        f"eventTimestamp ge '{_to_utc_iso(start_utc)}'",
        f"eventTimestamp le '{_to_utc_iso(end_utc)}'",
    ]

    if resource_id:
        filters.append(f"resourceUri eq '{_escape_filter_value(resource_id)}'")

    if resource_group:
        filters.append(f"resourceGroupName eq '{_escape_filter_value(resource_group)}'")

    filter_expression = " and ".join(filters)
    client = MonitorManagementClient(credential, subscription_id)
    try:
        return [
            _to_activity_log_row(event)
            for event in client.activity_logs.list(filter=filter_expression)
        ]
    finally:
        client.close()
