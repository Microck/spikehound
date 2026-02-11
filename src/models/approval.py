from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    INVESTIGATE = "investigate"


class ApprovalRecord(BaseModel):
    investigation_id: str = Field(min_length=1)
    decision: ApprovalDecision
    decided_by: str = Field(min_length=1)
    decided_at: datetime
    reason: str | None = None


ApprovalStore = dict[str, ApprovalRecord]
