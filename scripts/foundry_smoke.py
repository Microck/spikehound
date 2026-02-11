from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from azure.ai.projects import AIProjectClient

from azure.foundry import get_project_client


def _list_single_agent(project_client: AIProjectClient) -> int:
    list_agents = getattr(project_client.agents, "list_agents", None)
    if not callable(list_agents):
        raise RuntimeError(
            "AIProjectClient.agents.list_agents is unavailable in this SDK version."
        )

    try:
        agents = list_agents(top=1)
    except TypeError:
        agents = list_agents()

    if not isinstance(agents, Iterable):
        raise RuntimeError("Foundry list_agents did not return an iterable result.")

    count = 0
    for _agent in agents:
        count += 1
        if count >= 1:
            break

    return count


def main() -> None:
    client = get_project_client()
    try:
        agent_count = _list_single_agent(client)
    finally:
        close_client = getattr(client, "close", None)
        if callable(close_client):
            close_client()

    print(f"Foundry read-only smoke check passed (listed_agents={agent_count}).")


if __name__ == "__main__":
    main()
