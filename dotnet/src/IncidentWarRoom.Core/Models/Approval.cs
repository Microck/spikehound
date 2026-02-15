using System;

namespace IncidentWarRoom.Core.Models;

public enum ApprovalDecision
{
    Approve,
    Reject,
    Investigate,
}

public sealed record ApprovalRecord(
    string InvestigationId,
    ApprovalDecision Decision,
    string DecidedBy,
    DateTimeOffset DecidedAt,
    string? Reason
);
