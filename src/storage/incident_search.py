from __future__ import annotations

from abc import ABC
from abc import abstractmethod
import re
from typing import Any

from storage.incident_store import IncidentRecord
from storage.incident_store import IncidentStore


class IncidentSearch(ABC):
    @abstractmethod
    def search_similar(self, query: str, k: int) -> list[dict[str, Any]]:
        raise NotImplementedError


class LocalIncidentSearch(IncidentSearch):
    def __init__(self, store: IncidentStore, *, candidate_limit: int = 200) -> None:
        self._store = store
        self._candidate_limit = candidate_limit

    def search_similar(self, query: str, k: int) -> list[dict[str, Any]]:
        if k <= 0:
            return []

        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        candidate_count = max(self._candidate_limit, k)
        candidates = self._store.list_recent(limit=candidate_count)

        hits: list[dict[str, Any]] = []
        for record in candidates:
            score = self._score(query_terms, record)
            if score <= 0:
                continue
            hits.append({"id": record.id, "score": score})

        hits.sort(key=lambda hit: (-float(hit.get("score", 0.0)), str(hit["id"])))
        return hits[:k]

    @staticmethod
    def _score(query_terms: set[str], record: IncidentRecord) -> float:
        candidate_terms = LocalIncidentSearch._tokenize(
            " ".join(
                [
                    record.title,
                    record.summary,
                    record.root_cause,
                    record.resolution,
                    " ".join(record.tags),
                ]
            )
        )
        if not candidate_terms:
            return 0.0

        overlap = len(query_terms & candidate_terms)
        if overlap == 0:
            return 0.0
        return round(overlap / len(query_terms), 6)

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token}
