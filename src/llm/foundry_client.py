from __future__ import annotations

import copy
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
    # Azure OpenAI chat completions API version.
    # Note: `response_format.type=json_schema` requires 2024-08-01-preview or later.
    DEFAULT_API_VERSION = "2024-08-01-preview"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._endpoint = (
            (endpoint or os.getenv("FOUNDRY_ENDPOINT") or "").strip().rstrip("/")
        )
        model_raw = (model or os.getenv("FOUNDRY_MODEL") or "").strip()
        # Allow comma-separated deployment candidates so renames can be rolled out
        # without breaking existing environments.
        self._models = [
            candidate.strip() for candidate in model_raw.split(",") if candidate.strip()
        ]
        self._api_key = (api_key or os.getenv("FOUNDRY_API_KEY") or "").strip()
        self._api_version = (
            (
                api_version
                or os.getenv("FOUNDRY_API_VERSION")
                or self.DEFAULT_API_VERSION
            )
            .strip()
            .rstrip("/")
        )
        self._timeout = timeout
        self._http_client = http_client

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model_cls: type[BaseModel],
    ) -> dict[str, Any]:
        self._ensure_configured()

        payload: dict[str, Any] = {
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

        response_formats = self._response_format_attempts(model_cls)

        try:
            last_error: Exception | None = None
            for model in self._models:
                for response_format in response_formats:
                    attempt_payload = dict(payload)
                    if response_format is not None:
                        attempt_payload["response_format"] = response_format

                    try:
                        response = self._post(attempt_payload, headers, model=model)
                        response.raise_for_status()
                        body = response.json()
                        content = self._extract_content(body)
                        parsed = json.loads(content)
                        validated = model_cls.model_validate(parsed)
                        return validated.model_dump(mode="json")
                    except httpx.HTTPStatusError as exc:
                        last_error = exc
                        status_code = exc.response.status_code
                        # If `json_schema` is unsupported or schema validation fails server-side,
                        # retry with a weaker but broadly supported response format.
                        if status_code == 400:
                            continue
                        # If a deployment name is invalid/missing, fall back to the next
                        # configured deployment candidate.
                        if status_code == 404:
                            break
                        raise

            if last_error is not None:
                raise last_error
            raise FoundryResponseError("Foundry response format attempts exhausted")
        except FoundryResponseError:
            raise
        except (
            httpx.HTTPError,
            json.JSONDecodeError,
            ValidationError,
            ValueError,
        ) as exc:
            raise FoundryResponseError(f"Invalid Foundry response: {exc}") from exc

    def _post(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
        *,
        api_version: str | None = None,
        model: str | None = None,
    ) -> httpx.Response:
        deployment = (model or "").strip() or self._models[0]
        url = (
            f"{self._endpoint}/openai/deployments/{deployment}/chat/completions"
            f"?api-version={api_version or self._api_version}"
        )

        if self._http_client is not None:
            return self._http_client.post(url, headers=headers, json=payload)

        with httpx.Client(timeout=self._timeout) as client:
            return client.post(url, headers=headers, json=payload)

    def _ensure_configured(self) -> None:
        missing: list[str] = []
        if not self._endpoint:
            missing.append("FOUNDRY_ENDPOINT")
        if not self._models:
            missing.append("FOUNDRY_MODEL")
        if not self._api_key:
            missing.append("FOUNDRY_API_KEY")

        if missing:
            joined = ", ".join(missing)
            raise FoundryNotConfiguredError(
                f"Foundry client is not configured. Missing: {joined}"
            )

    def _response_format_attempts(
        self, model_cls: type[BaseModel]
    ) -> list[dict[str, Any] | None]:
        """Return response_format strategies in preferred order.

        We prefer JSON schema structured outputs when the model schema can be made strict.
        If not, we fallback to JSON mode (valid JSON, not schema-constrained).
        As a last resort, we rely on prompting only.
        """

        attempts: list[dict[str, Any] | None] = []

        json_schema_format = self._build_json_schema_response_format(model_cls)
        if json_schema_format is not None:
            attempts.append(json_schema_format)

        # JSON mode is widely supported across Azure OpenAI chat models.
        attempts.append({"type": "json_object"})

        # Prompt-only fallback.
        attempts.append(None)
        return attempts

    def _build_json_schema_response_format(
        self, model_cls: type[BaseModel]
    ) -> dict[str, Any] | None:
        schema = self._build_strict_json_schema(model_cls)
        if schema is None:
            return None

        return {
            "type": "json_schema",
            "json_schema": {
                "name": model_cls.__name__,
                "schema": schema,
                "strict": True,
            },
        }

    def _build_strict_json_schema(
        self, model_cls: type[BaseModel]
    ) -> dict[str, Any] | None:
        """Build a strict JSON schema suitable for Azure Structured Outputs.

        Azure Structured Outputs has stricter requirements than Pydantic defaults:
        - `additionalProperties` must be false on objects
        - `required` must include every key in `properties`

        Some models (e.g., those containing free-form dict fields) cannot be made strict
        without losing semantics. In those cases, return None and rely on JSON mode.
        """

        raw_schema = model_cls.model_json_schema()
        if not self._schema_is_strictable(raw_schema):
            return None

        patched = copy.deepcopy(raw_schema)

        def patch(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "object" and isinstance(
                    node.get("properties"), dict
                ):
                    props = node["properties"]
                    node["additionalProperties"] = False
                    node["required"] = list(props.keys())

                for value in node.values():
                    patch(value)
            elif isinstance(node, list):
                for item in node:
                    patch(item)

        patch(patched)
        return patched

    @staticmethod
    def _schema_is_strictable(schema: dict[str, Any]) -> bool:
        """Return True if schema can be used with strict Structured Outputs.

        We reject schemas that contain free-form objects/dicts (additionalProperties true
        or schema-valued additionalProperties), since forcing additionalProperties=false
        would silently drop legitimate keys.
        """

        stack: list[Any] = [schema]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                additional = node.get("additionalProperties")
                if additional is True or isinstance(additional, dict):
                    return False

                node_type = node.get("type")
                if node_type == "object" and "properties" not in node:
                    # Likely a dict-like schema; not safe to make strict.
                    if additional is not False:
                        return False

                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

        return True

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
