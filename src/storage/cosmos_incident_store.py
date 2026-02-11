from __future__ import annotations

import os
from typing import Any

from azure.cosmos import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos import exceptions as cosmos_exceptions

from storage.incident_store import IncidentRecord
from storage.incident_store import IncidentStore


class CosmosIncidentStore(IncidentStore):
    def __init__(
        self,
        *,
        endpoint: str | None = None,
        key: str | None = None,
        database: str | None = None,
        container: str | None = None,
        allow_create: bool | None = None,
    ) -> None:
        resolved_endpoint = endpoint or os.getenv("COSMOS_ENDPOINT")
        resolved_key = key or os.getenv("COSMOS_KEY")
        resolved_database = database or os.getenv("COSMOS_DATABASE")
        resolved_container = container or os.getenv("COSMOS_CONTAINER")

        missing = [
            name
            for name, value in (
                ("COSMOS_ENDPOINT", resolved_endpoint),
                ("COSMOS_KEY", resolved_key),
                ("COSMOS_DATABASE", resolved_database),
                ("COSMOS_CONTAINER", resolved_container),
            )
            if not value
        ]
        if missing:
            missing_list = ", ".join(missing)
            raise RuntimeError(
                f"Missing required Cosmos configuration: {missing_list}. "
                "Set these environment variables before using CosmosIncidentStore."
            )

        app_env = (os.getenv("APP_ENV") or "dev").lower()
        self._allow_create = (
            allow_create
            if allow_create is not None
            else app_env in {"dev", "local", "test"}
        )

        self._database_name = str(resolved_database)
        self._container_name = str(resolved_container)
        self._client = CosmosClient(
            url=str(resolved_endpoint), credential=str(resolved_key)
        )
        self._container = self._resolve_container()

    def put(self, record: IncidentRecord) -> None:
        payload = record.model_dump(mode="json")
        payload["id"] = record.id
        self._container.upsert_item(payload)

    def get(self, incident_id: str) -> IncidentRecord | None:
        try:
            item = self._container.read_item(
                item=incident_id, partition_key=incident_id
            )
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return None

        return IncidentRecord.model_validate(item)

    def list_recent(self, limit: int = 50) -> list[IncidentRecord]:
        if limit <= 0:
            return []

        query = f"SELECT TOP {int(limit)} * FROM c ORDER BY c.created_at DESC"
        items = self._container.query_items(
            query=query,
            enable_cross_partition_query=True,
        )
        records = [IncidentRecord.model_validate(item) for item in items]
        records.sort(key=lambda record: (record.created_at, record.id), reverse=True)
        return records[:limit]

    def _resolve_container(self) -> Any:
        if self._allow_create:
            database_client = self._client.create_database_if_not_exists(
                id=self._database_name
            )
            return database_client.create_container_if_not_exists(
                id=self._container_name,
                partition_key=PartitionKey(path="/id"),
            )

        try:
            database_client = self._client.get_database_client(self._database_name)
            database_client.read()
            container_client = database_client.get_container_client(
                self._container_name
            )
            container_client.read()
            return container_client
        except cosmos_exceptions.CosmosResourceNotFoundError as exc:
            raise RuntimeError(
                "Cosmos database/container not found. In non-dev environments, create "
                "resources ahead of time or run with APP_ENV=dev/local/test for safe auto-create."
            ) from exc
