import json

import httpx
import pytest
from pydantic import BaseModel
from pydantic import Field

from llm.foundry_client import FoundryClient


def _make_response(*, content: str) -> httpx.Response:
    body = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                }
            }
        ]
    }
    return httpx.Response(200, json=body)


def test_foundry_client_prefers_json_schema_for_strictable_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Ping(BaseModel):
        ok: bool
        model: str = Field(min_length=1)
        tags: list[str] = Field(default_factory=list)

    monkeypatch.setenv("FOUNDRY_ENDPOINT", "https://example.test")
    monkeypatch.setenv("FOUNDRY_MODEL", "deployment")
    monkeypatch.setenv("FOUNDRY_API_KEY", "test-key")
    monkeypatch.setenv("FOUNDRY_API_VERSION", "2024-08-01-preview")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        response_format = payload.get("response_format")
        assert isinstance(response_format, dict)
        assert response_format.get("type") == "json_schema"

        schema = response_format.get("json_schema", {}).get("schema")
        assert isinstance(schema, dict)
        assert schema.get("type") == "object"
        assert schema.get("additionalProperties") is False

        # Azure structured outputs expects required to include every property key.
        properties = schema.get("properties")
        required = schema.get("required")
        assert isinstance(properties, dict)
        assert isinstance(required, list)
        assert set(required) == set(properties.keys())

        return _make_response(content='{"ok": true, "model": "spikehound", "tags": []}')

    client = httpx.Client(transport=httpx.MockTransport(handler))
    foundry = FoundryClient(http_client=client)
    result = foundry.complete_json(
        system_prompt="Return JSON only",
        user_prompt="Ping",
        model_cls=Ping,
    )

    assert result["ok"] is True
    assert result["model"] == "spikehound"
    assert result["tags"] == []


def test_foundry_client_uses_json_object_for_non_strictable_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Loose(BaseModel):
        ok: bool
        params: dict[str, object] = Field(default_factory=dict)

    monkeypatch.setenv("FOUNDRY_ENDPOINT", "https://example.test")
    monkeypatch.setenv("FOUNDRY_MODEL", "deployment")
    monkeypatch.setenv("FOUNDRY_API_KEY", "test-key")
    monkeypatch.setenv("FOUNDRY_API_VERSION", "2024-08-01-preview")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        response_format = payload.get("response_format")
        assert response_format == {"type": "json_object"}
        return _make_response(content='{"ok": true, "params": {"a": 1}}')

    client = httpx.Client(transport=httpx.MockTransport(handler))
    foundry = FoundryClient(http_client=client)
    result = foundry.complete_json(
        system_prompt="Return JSON only",
        user_prompt="Ping",
        model_cls=Loose,
    )

    assert result["ok"] is True
    assert result["params"] == {"a": 1}


def test_foundry_client_falls_back_from_json_schema_to_json_object_on_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Ping(BaseModel):
        ok: bool
        model: str

    monkeypatch.setenv("FOUNDRY_ENDPOINT", "https://example.test")
    monkeypatch.setenv("FOUNDRY_MODEL", "deployment")
    monkeypatch.setenv("FOUNDRY_API_KEY", "test-key")
    monkeypatch.setenv("FOUNDRY_API_VERSION", "2024-08-01-preview")

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        response_format = payload.get("response_format")
        calls.append(str(response_format.get("type")))

        if response_format.get("type") == "json_schema":
            return httpx.Response(
                400, json={"error": {"message": "schema not supported"}}
            )
        assert response_format == {"type": "json_object"}
        return _make_response(content='{"ok": true, "model": "fallback"}')

    client = httpx.Client(transport=httpx.MockTransport(handler))
    foundry = FoundryClient(http_client=client)
    result = foundry.complete_json(
        system_prompt="Return JSON only",
        user_prompt="Ping",
        model_cls=Ping,
    )

    assert calls == ["json_schema", "json_object"]
    assert result["ok"] is True
    assert result["model"] == "fallback"


def test_foundry_client_falls_back_to_next_deployment_on_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Ping(BaseModel):
        ok: bool
        model: str

    monkeypatch.setenv("FOUNDRY_ENDPOINT", "https://example.test")
    monkeypatch.setenv("FOUNDRY_MODEL", "spikehound-gpt4o,legacy-deployment")
    monkeypatch.setenv("FOUNDRY_API_KEY", "test-key")
    monkeypatch.setenv("FOUNDRY_API_VERSION", "2024-08-01-preview")

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/deployments/spikehound-gpt4o/" in url:
            return httpx.Response(404, json={"error": {"message": "not found"}})
        if "/deployments/legacy-deployment/" in url:
            return _make_response(content='{"ok": true, "model": "spikehound"}')
        return httpx.Response(500, json={"error": {"message": "unexpected"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    foundry = FoundryClient(http_client=client)
    result = foundry.complete_json(
        system_prompt="Return JSON only",
        user_prompt="Ping",
        model_cls=Ping,
    )

    assert result["ok"] is True
    assert result["model"] == "spikehound"
