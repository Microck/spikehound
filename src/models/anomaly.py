from __future__ import annotations

from enum import Enum

from pydantic import BaseModel
from pydantic import Field

from models.time_range import TimeRange


class AnomalyType(str, Enum):
    SPIKE = "spike"


class Anomaly(BaseModel):
    anomaly_type: AnomalyType
    scope: str = Field(min_length=1)
    resource_id: str | None = None
    cost_before: float = Field(ge=0)
    cost_after: float = Field(ge=0)
    currency: str = Field(min_length=1)
    time_range: TimeRange
    summary: str = Field(min_length=1)
