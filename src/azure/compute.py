from __future__ import annotations

from typing import Any

from azure.mgmt.compute import ComputeManagementClient


def stop_vm(
    credential: Any,
    subscription_id: str,
    resource_group: str,
    vm_name: str,
) -> None:
    client = ComputeManagementClient(credential, subscription_id)
    try:
        poller = client.virtual_machines.begin_power_off(resource_group, vm_name)
        poller.result()
    finally:
        client.close()


def add_auto_shutdown(
    credential: Any,
    subscription_id: str,
    resource_group: str,
    vm_name: str,
    *,
    schedule_utc: str,
    timezone_name: str = "UTC",
) -> str:
    del (
        credential,
        subscription_id,
        resource_group,
        vm_name,
        schedule_utc,
        timezone_name,
    )
    return "Auto-shutdown configuration is not implemented yet."
