from __future__ import annotations

import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def get_ai_project_endpoint() -> str:
    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "").strip()
    if not endpoint:
        raise RuntimeError(
            "Missing AZURE_AI_PROJECT_ENDPOINT. Set it to your Azure AI Foundry project endpoint."
        )
    return endpoint


def get_project_client(endpoint: str | None = None) -> AIProjectClient:
    resolved_endpoint = endpoint or get_ai_project_endpoint()
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    return AIProjectClient(endpoint=resolved_endpoint, credential=credential)
