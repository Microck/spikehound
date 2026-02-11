from __future__ import annotations

import os

from azure.identity import DefaultAzureCredential


def get_credential() -> DefaultAzureCredential:
    return DefaultAzureCredential(exclude_interactive_browser_credential=True)


def get_subscription_id() -> str:
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        raise RuntimeError(
            "Missing AZURE_SUBSCRIPTION_ID. Set this environment variable to your Azure subscription ID."
        )
    return subscription_id
