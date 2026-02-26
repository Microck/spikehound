using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Core.Models;

namespace Spikehound.Core.Execution;

public enum RemediationExecutionStatus
{
    Ok,
    Skipped,
    Degraded,
    Error,
}

public sealed record RemediationExecutionOutcome(
    RemediationActionType ActionType,
    string TargetResourceId,
    RemediationExecutionStatus Status,
    string Message,
    DateTimeOffset StartedAt,
    DateTimeOffset FinishedAt
);

public interface IRemediationActionExecutor
{
    Task<RemediationExecutionOutcome> ExecuteAsync(RemediationAction action, CancellationToken cancellationToken);
}

public static class RemediationExecutionEngine
{
    public static async Task<IReadOnlyList<RemediationExecutionOutcome>> ExecuteAsync(
        RemediationPlan plan,
        ApprovalRecord approvalRecord,
        IRemediationActionExecutor executor,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(approvalRecord);
        ArgumentNullException.ThrowIfNull(executor);

        if (approvalRecord.Decision != ApprovalDecision.Approve)
        {
            return BuildSkippedOutcomes(plan, approvalRecord.Decision);
        }

        var outcomes = new List<RemediationExecutionOutcome>(plan.Actions.Count);
        foreach (var action in plan.Actions)
        {
            var startedAt = DateTimeOffset.UtcNow;
            try
            {
                var outcome = await executor.ExecuteAsync(action, cancellationToken);
                outcomes.Add(outcome with
                {
                    ActionType = action.Type,
                    TargetResourceId = action.TargetResourceId,
                    StartedAt = outcome.StartedAt == default ? startedAt : outcome.StartedAt,
                    FinishedAt = outcome.FinishedAt == default ? DateTimeOffset.UtcNow : outcome.FinishedAt,
                });
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex)
            {
                outcomes.Add(new RemediationExecutionOutcome(
                    ActionType: action.Type,
                    TargetResourceId: action.TargetResourceId,
                    Status: RemediationExecutionStatus.Error,
                    Message: ex.Message,
                    StartedAt: startedAt,
                    FinishedAt: DateTimeOffset.UtcNow));
            }
        }

        return outcomes;
    }

    private static IReadOnlyList<RemediationExecutionOutcome> BuildSkippedOutcomes(
        RemediationPlan plan,
        ApprovalDecision decision)
    {
        var outcomes = new List<RemediationExecutionOutcome>(plan.Actions.Count);
        var reason = $"Execution skipped because approval decision was {decision.ToString().ToLowerInvariant()}.";

        foreach (var action in plan.Actions)
        {
            var now = DateTimeOffset.UtcNow;
            outcomes.Add(new RemediationExecutionOutcome(
                ActionType: action.Type,
                TargetResourceId: action.TargetResourceId,
                Status: RemediationExecutionStatus.Skipped,
                Message: reason,
                StartedAt: now,
                FinishedAt: now));
        }

        return outcomes;
    }
}
