from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class CostFinding(BaseModel):
    resource_id: str = Field(min_length=1)
    cost: float = Field(ge=0)
    currency: str = Field(min_length=1)


class InvestigationFindings(BaseModel):
    alert_id: str = Field(min_length=1)
    received_at: datetime
    cost_findings: list[CostFinding] = Field(default_factory=list)
    notes: str = ""
