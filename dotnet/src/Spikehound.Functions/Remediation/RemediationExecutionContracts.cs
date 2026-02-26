using Spikehound.Core.Models;

namespace Spikehound.Functions.Remediation;

public sealed record RemediationExecutionRequest(
    string InvestigationId,
    RemediationPlan Plan,
    ApprovalRecord ApprovalRecord,
    string Source,
    bool ExecutionEnabled
);

public sealed record RemediationExecutionSummary(
    string InvestigationId,
    int OkCount,
    int SkippedCount,
    int DegradedCount,
    int ErrorCount
);
