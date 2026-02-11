from __future__ import annotations

from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel

from azure.auth import get_credential
from azure.auth import get_subscription_id
from azure.compute import add_auto_shutdown
from azure.compute import stop_vm
from models.approval import ApprovalDecision
from models.approval import ApprovalRecord
from models.remediation import RemediationAction
from models.remediation import RemediationActionType
from models.remediation import RemediationPlan


class ExecutionStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"
    SKIPPED = "skipped"


class ExecutionOutcome(BaseModel):
    action: str
    status: ExecutionStatus
    message: str
    started_at: datetime
    finished_at: datetime


def execute_remediation(
    plan: RemediationPlan,
    approval_record: ApprovalRecord | None,
) -> list[ExecutionOutcome]:
    decision = approval_record.decision if approval_record is not None else None
    if decision is not ApprovalDecision.APPROVE:
        decision_label = decision.value if decision is not None else "missing"
        return [
            _outcome(
                action=action,
                status=ExecutionStatus.SKIPPED,
                message=(
                    "Remediation execution skipped because approval decision is "
                    f"'{decision_label}'."
                ),
            )
            for action in plan.actions
        ]

    outcomes: list[ExecutionOutcome] = []
    credential: Any | None = None
    subscription_id: str | None = None

    for action in plan.actions:
        started_at = datetime.now(timezone.utc)
        try:
            if action.type is RemediationActionType.STOP_VM:
                credential, subscription_id = _resolve_azure_context(
                    credential,
                    subscription_id,
                )
                resource_group, vm_name = _extract_vm_identifiers(
                    action.target_resource_id
                )
                stop_vm(
                    credential,
                    subscription_id,
                    resource_group,
                    vm_name,
                )
                outcomes.append(
                    ExecutionOutcome(
                        action=action.type.value,
                        status=ExecutionStatus.OK,
                        message=(
                            f"Stopped VM '{vm_name}' in resource group "
                            f"'{resource_group}'."
                        ),
                        started_at=started_at,
                        finished_at=datetime.now(timezone.utc),
                    )
                )
                continue

            if action.type is RemediationActionType.ADD_AUTO_SHUTDOWN:
                credential, subscription_id = _resolve_azure_context(
                    credential,
                    subscription_id,
                )
                resource_group, vm_name = _extract_vm_identifiers(
                    action.target_resource_id
                )
                schedule_utc = str(action.parameters.get("schedule_utc") or "22:00")
                timezone_name = str(action.parameters.get("timezone") or "UTC")
                message = add_auto_shutdown(
                    credential,
                    subscription_id,
                    resource_group,
                    vm_name,
                    schedule_utc=schedule_utc,
                    timezone_name=timezone_name,
                )
                outcomes.append(
                    ExecutionOutcome(
                        action=action.type.value,
                        status=ExecutionStatus.DEGRADED,
                        message=message,
                        started_at=started_at,
                        finished_at=datetime.now(timezone.utc),
                    )
                )
                continue

            outcomes.append(
                ExecutionOutcome(
                    action=action.type.value,
                    status=ExecutionStatus.SKIPPED,
                    message=(
                        f"Remediation action '{action.type.value}' is not "
                        "implemented for execution."
                    ),
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                )
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            outcomes.append(
                ExecutionOutcome(
                    action=action.type.value,
                    status=ExecutionStatus.ERROR,
                    message=f"Execution failed: {exc}",
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                )
            )

    return outcomes


def _resolve_azure_context(
    credential: Any | None,
    subscription_id: str | None,
) -> tuple[Any, str]:
    resolved_credential = credential or get_credential()
    resolved_subscription_id = subscription_id or get_subscription_id()
    return resolved_credential, resolved_subscription_id


def _extract_vm_identifiers(resource_id: str) -> tuple[str, str]:
    parts = [segment for segment in resource_id.split("/") if segment]
    normalized = [segment.lower() for segment in parts]

    try:
        resource_group = parts[normalized.index("resourcegroups") + 1]
        vm_name = parts[normalized.index("virtualmachines") + 1]
    except (ValueError, IndexError) as exc:
        raise ValueError(
            "Expected VM resource ID with resourceGroups and virtualMachines segments."
        ) from exc

    if not resource_group or not vm_name:
        raise ValueError("VM resource ID is missing resource group or VM name.")

    return resource_group, vm_name


def _outcome(
    *,
    action: RemediationAction,
    status: ExecutionStatus,
    message: str,
) -> ExecutionOutcome:
    now = datetime.now(timezone.utc)
    return ExecutionOutcome(
        action=action.type.value,
        status=status,
        message=message,
        started_at=now,
        finished_at=now,
    )
