from __future__ import annotations

from enum import Enum
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class RemediationActionType(str, Enum):
    STOP_VM = "stop_vm"
    RESIZE_VM = "resize_vm"
    ADD_AUTO_SHUTDOWN = "add_auto_shutdown"
    NOTIFY_OWNER = "notify_owner"
    OPEN_TICKET = "open_ticket"


class RemediationRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RemediationAction(BaseModel):
    type: RemediationActionType
    target_resource_id: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk_level: RemediationRiskLevel
    human_approval_required: Literal[True] = True


class RemediationPlan(BaseModel):
    summary: str = Field(min_length=1)
    actions: list[RemediationAction] = Field(min_length=1)
    rollback_notes: str = ""
