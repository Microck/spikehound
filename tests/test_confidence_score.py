from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.diagnosis import Diagnosis


def _payload(confidence: int) -> dict[str, object]:
    return {
        "hypothesis": {
            "title": "GPU VM left running without auto-shutdown",
            "explanation": "Cost and runtime findings indicate continuous VM uptime.",
            "evidence": [
                "Top cost driver is vm-gpu-prod",
                "Power state is running",
                "Auto-shutdown schedule is missing",
            ],
        },
        "confidence": confidence,
        "alternatives": [
            "Legitimate workload spike",
            "Resource leak from recurring jobs",
        ],
        "risks": ["Stopping VM may disrupt active jobs"],
    }


@pytest.mark.parametrize("confidence", [-1, 101])
def test_diagnosis_rejects_confidence_out_of_range(confidence: int) -> None:
    with pytest.raises(ValidationError):
        Diagnosis.model_validate(_payload(confidence))
