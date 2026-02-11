from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class IncidentRecord(BaseModel):
    id: str = Field(min_length=1)
    created_at: datetime
    title: str = Field(min_length=1)
    summary: str = ""
    root_cause: str = ""
    resolution: str = ""
    tags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class IncidentStore(ABC):
    @abstractmethod
    def put(self, record: IncidentRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, incident_id: str) -> IncidentRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[IncidentRecord]:
        raise NotImplementedError


class MemoryIncidentStore(IncidentStore):
    def __init__(self) -> None:
        self._records: dict[str, IncidentRecord] = {}

    def put(self, record: IncidentRecord) -> None:
        self._records[record.id] = record.model_copy(deep=True)

    def get(self, incident_id: str) -> IncidentRecord | None:
        record = self._records.get(incident_id)
        if record is None:
            return None
        return record.model_copy(deep=True)

    def list_recent(self, limit: int = 50) -> list[IncidentRecord]:
        if limit <= 0:
            return []

        sorted_records = sorted(
            self._records.values(),
            key=lambda record: (record.created_at, record.id),
            reverse=True,
        )
        return [record.model_copy(deep=True) for record in sorted_records[:limit]]
