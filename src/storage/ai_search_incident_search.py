from __future__ import annotations

import os
from typing import Any
from typing import Mapping

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from storage.incident_search import IncidentSearch


class AzureAISearchIncidentSearch(IncidentSearch):
    def __init__(
        self,
        *,
        endpoint: str | None = None,
        api_key: str | None = None,
        index_name: str | None = None,
        id_field: str = "id",
    ) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._index_name = index_name
        self._id_field = id_field

    def search_similar(self, query: str, k: int) -> list[dict[str, Any]]:
        if k <= 0:
            return []

        trimmed_query = query.strip()
        if not trimmed_query:
            return []

        endpoint, api_key, index_name = self._resolve_settings()
        client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key),
        )

        results = client.search(search_text=trimmed_query, top=k)

        hits: list[dict[str, Any]] = []
        for result in results:
            result_map = self._as_mapping(result)
            incident_id = result_map.get(self._id_field) or result_map.get(
                "incident_id"
            )
            if incident_id is None:
                continue

            hit: dict[str, Any] = {"id": str(incident_id)}
            score = self._coerce_score(result_map.get("@search.score"))
            if score is not None:
                hit["score"] = score
            hits.append(hit)

        return hits

    def _resolve_settings(self) -> tuple[str, str, str]:
        endpoint = self._endpoint or os.getenv("AZURE_SEARCH_ENDPOINT")
        api_key = self._api_key or os.getenv("AZURE_SEARCH_API_KEY")
        index_name = self._index_name or os.getenv("AZURE_SEARCH_INDEX")

        missing = [
            name
            for name, value in (
                ("AZURE_SEARCH_ENDPOINT", endpoint),
                ("AZURE_SEARCH_API_KEY", api_key),
                ("AZURE_SEARCH_INDEX", index_name),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing required Azure AI Search configuration: "
                f"{', '.join(missing)}. Set these environment variables before searching."
            )

        return str(endpoint), str(api_key), str(index_name)

    @staticmethod
    def _as_mapping(result: Any) -> Mapping[str, Any]:
        if isinstance(result, Mapping):
            return result
        return dict(result)

    @staticmethod
    def _coerce_score(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
