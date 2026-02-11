from __future__ import annotations

from datetime import datetime
from datetime import timezone

import pytest
from pydantic import ValidationError

from models.anomaly import Anomaly


def _valid_payload() -> dict[str, object]:
    return {
        "anomaly_type": "spike",
        "scope": "/subscriptions/sub-123",
        "resource_id": "/subscriptions/sub-123/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
        "cost_before": 50.0,
        "cost_after": 175.25,
        "currency": "USD",
        "time_range": {
            "start": datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2026, 2, 8, 0, 0, tzinfo=timezone.utc),
        },
        "summary": "Daily spend increased significantly on vm1",
    }


def test_anomaly_model_valid_instance_and_json_serialization() -> None:
    anomaly = Anomaly.model_validate(_valid_payload())

    assert anomaly.anomaly_type.value == "spike"
    assert anomaly.cost_after == 175.25
    assert '"anomaly_type":"spike"' in anomaly.model_dump_json()


def test_anomaly_model_rejects_invalid_time_range() -> None:
    payload = _valid_payload()
    payload["time_range"] = {
        "start": datetime(2026, 2, 8, 0, 0, tzinfo=timezone.utc),
        "end": datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc),
    }

    with pytest.raises(ValidationError):
        Anomaly.model_validate(payload)


def test_anomaly_model_rejects_negative_cost() -> None:
    payload = _valid_payload()
    payload["cost_before"] = -1.0

    with pytest.raises(ValidationError):
        Anomaly.model_validate(payload)
