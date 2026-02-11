from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class SimilarIncident(BaseModel):
    id: str = Field(min_length=1)
    title: str = ""
    summary: str = ""
    resolution: str = ""
    score: float | None = None


class HistoryFindings(BaseModel):
    query: str = Field(min_length=1)
    matches: list[SimilarIncident] = Field(default_factory=list)
    notes: str = ""
