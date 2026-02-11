from __future__ import annotations

from datetime import datetime
from datetime import timezone

from execution.remediation import ExecutionStatus
from execution.remediation import execute_remediation
from models.approval import ApprovalDecision
from models.approval import ApprovalRecord
from models.remediation import RemediationAction
from models.remediation import RemediationActionType
from models.remediation import RemediationPlan
from models.remediation import RemediationRiskLevel


def _approval_record(decision: ApprovalDecision) -> ApprovalRecord:
    return ApprovalRecord(
        investigation_id="alert-123",
        decision=decision,
        decided_by="tester",
        decided_at=datetime(2026, 2, 11, 18, 0, tzinfo=timezone.utc),
    )


def _plan() -> RemediationPlan:
    return RemediationPlan(
        summary="Stop running VM",
        actions=[
            RemediationAction(
                type=RemediationActionType.STOP_VM,
                target_resource_id=(
                    "/subscriptions/sub-123/resourceGroups/rg-demo/providers/"
                    "Microsoft.Compute/virtualMachines/vm-demo"
                ),
                parameters={"mode": "deallocate"},
                risk_level=RemediationRiskLevel.MEDIUM,
            )
        ],
        rollback_notes="Restart VM if stop was unintended.",
    )


def test_execute_remediation_reject_skips_without_running(monkeypatch) -> None:
    plan = _plan()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("stop_vm should not run for non-approved decisions")

    monkeypatch.setattr("execution.remediation.stop_vm", fail_if_called)

    outcomes = execute_remediation(
        plan,
        _approval_record(ApprovalDecision.REJECT),
    )

    assert len(outcomes) == 1
    assert outcomes[0].action == "stop_vm"
    assert outcomes[0].status is ExecutionStatus.SKIPPED
    assert "reject" in outcomes[0].message


def test_execute_remediation_approve_runs_stop_vm(monkeypatch) -> None:
    plan = _plan()
    called: dict[str, str] = {}

    monkeypatch.setattr("execution.remediation.get_credential", lambda: object())
    monkeypatch.setattr("execution.remediation.get_subscription_id", lambda: "sub-123")

    def fake_stop_vm(
        credential,
        subscription_id: str,
        resource_group: str,
        vm_name: str,
    ) -> None:
        assert credential is not None
        called["subscription_id"] = subscription_id
        called["resource_group"] = resource_group
        called["vm_name"] = vm_name

    monkeypatch.setattr("execution.remediation.stop_vm", fake_stop_vm)

    outcomes = execute_remediation(
        plan,
        _approval_record(ApprovalDecision.APPROVE),
    )

    assert len(outcomes) == 1
    assert outcomes[0].status is ExecutionStatus.OK
    assert called == {
        "subscription_id": "sub-123",
        "resource_group": "rg-demo",
        "vm_name": "vm-demo",
    }
