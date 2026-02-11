from __future__ import annotations

from typing import Any
from typing import Iterable

from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from azure.mgmt.resourcegraph.models import QueryRequestOptions


def query_resources(
    credential: Any,
    subscription_ids: Iterable[str],
    kql: str,
) -> list[dict[str, Any]]:
    subscriptions = [
        subscription_id for subscription_id in subscription_ids if subscription_id
    ]
    if not subscriptions:
        return []

    client = ResourceGraphClient(credential)
    query_request = QueryRequest(
        subscriptions=subscriptions,
        query=kql,
        options=QueryRequestOptions(result_format="objectArray"),
    )

    try:
        query_response = client.resources(query_request)
    finally:
        client.close()

    data = getattr(query_response, "data", None)
    if not isinstance(data, list):
        return []

    return [row for row in data if isinstance(row, dict)]
