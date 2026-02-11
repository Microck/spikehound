from __future__ import annotations

from datetime import datetime
from datetime import timedelta

from pydantic import BaseModel
from pydantic import field_validator
from pydantic import model_validator


class TimeRange(BaseModel):
    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def validate_utc_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("Time values must be UTC ISO8601 datetimes")
        return value

    @model_validator(mode="after")
    def validate_order(self) -> "TimeRange":
        if self.start >= self.end:
            raise ValueError("start must be before end")
        return self
