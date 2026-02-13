from __future__ import annotations

import httpx

from integrations import discord as discord_integration


def test_discord_webhook_skips_when_url_missing(monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    calls: list[dict[str, object]] = []

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return httpx.Response(204)

    monkeypatch.setattr(discord_integration.httpx, "post", fake_post)

    discord_integration.send_discord_webhook({"content": "hello"})

    assert calls == []


def test_discord_webhook_retries_on_429_then_succeeds(monkeypatch) -> None:
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")
    monkeypatch.setenv("DISCORD_WEBHOOK_MAX_RETRIES", "2")
    monkeypatch.setenv("DISCORD_WEBHOOK_BACKOFF_SECONDS", "0.01")

    responses = [
        httpx.Response(
            429, headers={"Retry-After": "0.01"}, json={"retry_after": 0.01}
        ),
        httpx.Response(204),
    ]
    call_count = {"count": 0}
    slept: list[float] = []

    def fake_post(*args, **kwargs):
        call_count["count"] += 1
        return responses.pop(0)

    monkeypatch.setattr(discord_integration.httpx, "post", fake_post)
    monkeypatch.setattr(
        discord_integration.time, "sleep", lambda seconds: slept.append(seconds)
    )

    discord_integration.send_discord_webhook({"content": "hello"})

    assert call_count["count"] == 2
    assert len(slept) == 1


def test_discord_webhook_retries_on_transient_request_error(monkeypatch) -> None:
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")
    monkeypatch.setenv("DISCORD_WEBHOOK_MAX_RETRIES", "2")
    monkeypatch.setenv("DISCORD_WEBHOOK_BACKOFF_SECONDS", "0.01")

    request = httpx.Request("POST", "https://discord.example/webhook")
    call_count = {"count": 0}
    slept: list[float] = []

    def fake_post(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise httpx.ConnectError("network issue", request=request)
        return httpx.Response(204)

    monkeypatch.setattr(discord_integration.httpx, "post", fake_post)
    monkeypatch.setattr(
        discord_integration.time, "sleep", lambda seconds: slept.append(seconds)
    )

    discord_integration.send_discord_webhook({"content": "hello"})

    assert call_count["count"] == 2
    assert len(slept) == 1


def test_discord_webhook_does_not_retry_on_permanent_4xx(monkeypatch) -> None:
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")
    monkeypatch.setenv("DISCORD_WEBHOOK_MAX_RETRIES", "3")

    call_count = {"count": 0}

    def fake_post(*args, **kwargs):
        call_count["count"] += 1
        return httpx.Response(400)

    monkeypatch.setattr(discord_integration.httpx, "post", fake_post)

    discord_integration.send_discord_webhook({"content": "hello"})

    assert call_count["count"] == 1


def test_discord_webhook_exhausted_retries_does_not_raise(monkeypatch) -> None:
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")
    monkeypatch.setenv("DISCORD_WEBHOOK_MAX_RETRIES", "1")
    monkeypatch.setenv("DISCORD_WEBHOOK_BACKOFF_SECONDS", "0.01")

    request = httpx.Request("POST", "https://discord.example/webhook")
    call_count = {"count": 0}

    def fake_post(*args, **kwargs):
        call_count["count"] += 1
        raise httpx.ConnectError("still failing", request=request)

    monkeypatch.setattr(discord_integration.httpx, "post", fake_post)
    monkeypatch.setattr(discord_integration.time, "sleep", lambda seconds: None)

    # Should not raise despite repeated failures.
    discord_integration.send_discord_webhook({"content": "hello"})

    assert call_count["count"] == 2
