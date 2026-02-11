from __future__ import annotations

from fastapi.testclient import TestClient

from web.app import app


def test_fastapi_app_loads() -> None:
    assert app.title == "Incident War Room"


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
