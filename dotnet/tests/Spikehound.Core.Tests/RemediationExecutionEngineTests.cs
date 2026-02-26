using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Core.Execution;
using Spikehound.Core.Models;
using Xunit;

namespace Spikehound.Core.Tests;

public sealed class RemediationExecutionEngineTests
{
    private sealed class RecordingExecutor : IRemediationActionExecutor
    {
        public List<RemediationAction> Calls { get; } = [];

        public bool ThrowOnExecute { get; set; }

        public Task<RemediationExecutionOutcome> ExecuteAsync(RemediationAction action, CancellationToken cancellationToken)
        {
            Calls.Add(action);
            if (ThrowOnExecute)
            {
                throw new InvalidOperationException("simulated executor failure");
            }

            var now = DateTimeOffset.UtcNow;
            return Task.FromResult(new RemediationExecutionOutcome(
                ActionType: action.Type,
                TargetResourceId: action.TargetResourceId,
                Status: RemediationExecutionStatus.Ok,
                Message: "executed",
                StartedAt: now,
                FinishedAt: now));
        }
    }

    [Fact]
    public async Task ExecuteAsync_SkipsAllActions_WhenDecisionIsNotApprove()
    {
        var plan = CreatePlan();
        var approval = new ApprovalRecord(
            InvestigationId: "inv-1",
            Decision: ApprovalDecision.Reject,
            DecidedBy: "operator",
            DecidedAt: DateTimeOffset.UtcNow,
            Reason: "Unsafe");

        var executor = new RecordingExecutor();

        var outcomes = await RemediationExecutionEngine.ExecuteAsync(plan, approval, executor);

        Assert.Empty(executor.Calls);
        Assert.Equal(plan.Actions.Count, outcomes.Count);
        Assert.All(outcomes, outcome => Assert.Equal(RemediationExecutionStatus.Skipped, outcome.Status));
    }

    [Fact]
    public async Task ExecuteAsync_ExecutesAllActions_WhenApproved()
    {
        var plan = CreatePlan();
        var approval = new ApprovalRecord(
            InvestigationId: "inv-1",
            Decision: ApprovalDecision.Approve,
            DecidedBy: "operator",
            DecidedAt: DateTimeOffset.UtcNow,
            Reason: null);

        var executor = new RecordingExecutor();

        var outcomes = await RemediationExecutionEngine.ExecuteAsync(plan, approval, executor);

        Assert.Equal(plan.Actions.Count, executor.Calls.Count);
        Assert.Equal(plan.Actions.Select(a => a.Type), outcomes.Select(o => o.ActionType));
        Assert.All(outcomes, outcome => Assert.Equal(RemediationExecutionStatus.Ok, outcome.Status));
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsErrorOutcome_WhenExecutorThrows()
    {
        var plan = CreatePlan(actions: [
            new RemediationAction(
                Type: RemediationActionType.StopVm,
                TargetResourceId: "/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                Parameters: new Dictionary<string, object?>(),
                RiskLevel: RemediationRiskLevel.High),
        ]);
        var approval = new ApprovalRecord(
            InvestigationId: "inv-1",
            Decision: ApprovalDecision.Approve,
            DecidedBy: "operator",
            DecidedAt: DateTimeOffset.UtcNow,
            Reason: null);

        var executor = new RecordingExecutor { ThrowOnExecute = true };

        var outcomes = await RemediationExecutionEngine.ExecuteAsync(plan, approval, executor);

        Assert.Single(executor.Calls);
        var outcome = Assert.Single(outcomes);
        Assert.Equal(RemediationExecutionStatus.Error, outcome.Status);
        Assert.Contains("simulated executor failure", outcome.Message, StringComparison.Ordinal);
    }

    private static RemediationPlan CreatePlan(IReadOnlyList<RemediationAction>? actions = null)
    {
        return new RemediationPlan(
            Summary: "plan",
            Actions: actions ??
            [
                new RemediationAction(
                    Type: RemediationActionType.StopVm,
                    TargetResourceId: "/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                    Parameters: new Dictionary<string, object?>(),
                    RiskLevel: RemediationRiskLevel.High),
                new RemediationAction(
                    Type: RemediationActionType.NotifyOwner,
                    TargetResourceId: "owner://ops-team",
                    Parameters: new Dictionary<string, object?>(),
                    RiskLevel: RemediationRiskLevel.Low),
            ],
            RollbackNotes: "rollback");
    }
}
