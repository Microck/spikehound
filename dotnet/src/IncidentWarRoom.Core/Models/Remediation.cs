using System.Collections.Generic;

namespace IncidentWarRoom.Core.Models;

public enum RemediationActionType
{
    StopVm,
    ResizeVm,
    AddAutoShutdown,
    NotifyOwner,
    OpenTicket,
}

public enum RemediationRiskLevel
{
    Low,
    Medium,
    High,
}

public sealed record RemediationAction(
    RemediationActionType Type,
    string TargetResourceId,
    IReadOnlyDictionary<string, object?> Parameters,
    RemediationRiskLevel RiskLevel
)
{
    // Safety invariant: remediation actions are always human-approved.
    public bool HumanApprovalRequired => true;
}

public sealed record RemediationPlan(
    string Summary,
    IReadOnlyList<RemediationAction> Actions,
    string RollbackNotes
);
