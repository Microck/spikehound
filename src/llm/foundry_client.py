from __future__ import annotations

import json
import os
from typing import Any

import httpx
from pydantic import BaseModel
from pydantic import ValidationError


class FoundryError(RuntimeError):
    pass


class FoundryNotConfiguredError(FoundryError):
    pass


class FoundryResponseError(FoundryError):
    pass


class FoundryClient:
    API_VERSION = "2024-06-01"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._endpoint = (
            (endpoint or os.getenv("FOUNDRY_ENDPOINT") or "").strip().rstrip("/")
        )
        self._model = (model or os.getenv("FOUNDRY_MODEL") or "").strip()
        self._api_key = (api_key or os.getenv("FOUNDRY_API_KEY") or "").strip()
        self._timeout = timeout
        self._http_client = http_client

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model_cls: type[BaseModel],
    ) -> dict[str, Any]:
        self._ensure_configured()

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "max_tokens": 800,
        }
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        try:
            response = self._post(payload, headers)
            response.raise_for_status()
            body = response.json()
            content = self._extract_content(body)
            parsed = json.loads(content)
            validated = model_cls.model_validate(parsed)
            return validated.model_dump(mode="json")
        except FoundryResponseError:
            raise
        except (
            httpx.HTTPError,
            json.JSONDecodeError,
            ValidationError,
            ValueError,
        ) as exc:
            raise FoundryResponseError(f"Invalid Foundry response: {exc}") from exc

    def _post(self, payload: dict[str, Any], headers: dict[str, str]) -> httpx.Response:
        url = (
            f"{self._endpoint}/openai/deployments/{self._model}/chat/completions"
            f"?api-version={self.API_VERSION}"
        )

        if self._http_client is not None:
            return self._http_client.post(url, headers=headers, json=payload)

        with httpx.Client(timeout=self._timeout) as client:
            return client.post(url, headers=headers, json=payload)

    def _ensure_configured(self) -> None:
        missing: list[str] = []
        if not self._endpoint:
            missing.append("FOUNDRY_ENDPOINT")
        if not self._model:
            missing.append("FOUNDRY_MODEL")
        if not self._api_key:
            missing.append("FOUNDRY_API_KEY")

        if missing:
            joined = ", ".join(missing)
            raise FoundryNotConfiguredError(
                f"Foundry client is not configured. Missing: {joined}"
            )

    @staticmethod
    def _extract_content(body: dict[str, Any]) -> str:
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise FoundryResponseError("Missing choices in Foundry response.")

        first = choices[0]
        if not isinstance(first, dict):
            raise FoundryResponseError("Malformed choices payload in Foundry response.")

        message = first.get("message")
        if not isinstance(message, dict):
            raise FoundryResponseError("Missing message in Foundry response.")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise FoundryResponseError("Missing message content in Foundry response.")

        return content
