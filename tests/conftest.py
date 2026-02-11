from __future__ import annotations

import pytest

import web.app as web_app


@pytest.fixture(autouse=True)
def reset_in_memory_web_state() -> None:
    web_app.approval_records.clear()
    web_app.latest_reports.clear()
    web_app.latest_remediation_plans.clear()
    web_app.processed_investigations.clear()
