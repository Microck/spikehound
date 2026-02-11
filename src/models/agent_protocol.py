from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Field


TData = TypeVar("TData")


class AgentName(str, Enum):
    COST = "cost"
    RESOURCE = "resource"
    HISTORY = "history"
    DIAGNOSIS = "diagnosis"
    REMEDIATION = "remediation"


class AgentStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class AgentResult(BaseModel, Generic[TData]):
    agent: AgentName
    status: AgentStatus
    started_at: datetime
    finished_at: datetime
    data: TData | None = None
    errors: list[str] = Field(default_factory=list)
