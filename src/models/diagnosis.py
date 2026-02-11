from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class RootCauseHypothesis(BaseModel):
    title: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class Diagnosis(BaseModel):
    hypothesis: RootCauseHypothesis
    confidence: int = Field(ge=0, le=100)
    alternatives: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
