from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class ResourceConfig(BaseModel):
    resource_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    location: str = Field(min_length=1)
    tags: dict[str, str] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)


class ResourceChange(BaseModel):
    timestamp: datetime
    caller: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    status: str = Field(min_length=1)
    correlation_id: str | None = None


class ResourceFindings(BaseModel):
    target_resource_id: str = Field(min_length=1)
    config: ResourceConfig | None = None
    recent_changes: list[ResourceChange] = Field(default_factory=list)
    notes: str = ""
