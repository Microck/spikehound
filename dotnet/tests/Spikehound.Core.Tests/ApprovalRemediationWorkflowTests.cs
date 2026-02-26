using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Core.Execution;
using Spikehound.Core.Models;
using Spikehound.Functions;
using Spikehound.Functions.Remediation;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace Spikehound.Core.Tests;

public sealed class ApprovalRemediationWorkflowTests
{
    private sealed class RecordingExecutor : IRemediationActionExecutor
    {
        public int Calls { get; private set; }

        public Task<RemediationExecutionOutcome> ExecuteAsync(RemediationAction action, CancellationToken cancellationToken)
        {
            Calls++;
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

    private sealed class StaticHttpClientFactory : IHttpClientFactory
    {
        private readonly HttpClient _client = new();

        public HttpClient CreateClient(string name) => _client;
    }

    private sealed class RecordingScheduler
    {
        public List<RemediationExecutionRequest> Requests { get; } = [];

        public bool ThrowOnSchedule { get; set; }

        public Task<string> ScheduleAsync(RemediationExecutionRequest request, CancellationToken cancellationToken)
        {
            if (ThrowOnSchedule)
            {
                throw new InvalidOperationException("scheduler unavailable");
            }

            Requests.Add(request);
            return Task.FromResult($"instance-{Requests.Count}");
        }
    }

    [Fact]
    public async Task QueueApprovedExecutionAsync_ReturnsIgnored_WhenDecisionNotApprove()
    {
        const string investigationId = "inv-reject";
        var state = CreateStateWithPlan(investigationId);
        var executor = new RecordingExecutor();
        var scheduler = new RecordingScheduler();
        var workflow = CreateWorkflow(state, executor);
        var approval = CreateApproval(investigationId, ApprovalDecision.Reject);

        var queueResult = await workflow.QueueApprovedExecutionAsync(
            investigationId,
            approval,
            source: "test",
            scheduleOrchestration: scheduler.ScheduleAsync);

        Assert.Equal(QueueExecutionResult.Ignored, queueResult);
        Assert.Empty(scheduler.Requests);
        Assert.Equal(0, executor.Calls);
    }

    [Fact]
    public async Task QueueApprovedExecutionAsync_ReturnsNoPlan_WhenNoPlanExists()
    {
        const string investigationId = "inv-no-plan";
        var state = new InMemoryState();
        var executor = new RecordingExecutor();
        var scheduler = new RecordingScheduler();
        var workflow = CreateWorkflow(state, executor);
        var approval = CreateApproval(investigationId, ApprovalDecision.Approve);

        var queueResult = await workflow.QueueApprovedExecutionAsync(
            investigationId,
            approval,
            source: "test",
            scheduleOrchestration: scheduler.ScheduleAsync);

        Assert.Equal(QueueExecutionResult.NoPlan, queueResult);
        Assert.Empty(scheduler.Requests);
        Assert.Equal(0, executor.Calls);
    }

    [Fact]
    public async Task QueueApprovedExecutionAsync_ReturnsDisabled_WhenExecutionToggleOff()
    {
        const string investigationId = "inv-disabled";
        var state = CreateStateWithPlan(investigationId);
        var executor = new RecordingExecutor();
        var scheduler = new RecordingScheduler();
        var workflow = CreateWorkflow(state, executor);
        var approval = CreateApproval(investigationId, ApprovalDecision.Approve);

        var previousValue = Environment.GetEnvironmentVariable("SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION");
        Environment.SetEnvironmentVariable("SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION", "false");

        try
        {
            var queueResult = await workflow.QueueApprovedExecutionAsync(
                investigationId,
                approval,
                source: "test",
                scheduleOrchestration: scheduler.ScheduleAsync);

            Assert.Equal(QueueExecutionResult.Disabled, queueResult);
            var request = Assert.Single(scheduler.Requests);
            Assert.False(request.ExecutionEnabled);
            Assert.True(state.RemediationExecutionInstances.TryGetValue(investigationId, out var instanceId));
            Assert.Equal("instance-1", instanceId);
            Assert.Equal(0, executor.Calls);
        }
        finally
        {
            Environment.SetEnvironmentVariable("SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION", previousValue);
        }
    }

    [Fact]
    public async Task QueueApprovedExecutionAsync_ReturnsQueued_WhenExecutionToggleOn()
    {
        const string investigationId = "inv-enabled";
        var state = CreateStateWithPlan(investigationId);
        var executor = new RecordingExecutor();
        var scheduler = new RecordingScheduler();
        var workflow = CreateWorkflow(state, executor);
        var approval = CreateApproval(investigationId, ApprovalDecision.Approve);

        var previousValue = Environment.GetEnvironmentVariable("SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION");
        Environment.SetEnvironmentVariable("SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION", "true");

        try
        {
            var queueResult = await workflow.QueueApprovedExecutionAsync(
                investigationId,
                approval,
                source: "test",
                scheduleOrchestration: scheduler.ScheduleAsync);

            Assert.Equal(QueueExecutionResult.Queued, queueResult);
            var request = Assert.Single(scheduler.Requests);
            Assert.True(request.ExecutionEnabled);
            Assert.True(state.RemediationExecutionInstances.TryGetValue(investigationId, out var instanceId));
            Assert.Equal("instance-1", instanceId);
            Assert.Equal(0, executor.Calls);
        }
        finally
        {
            Environment.SetEnvironmentVariable("SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION", previousValue);
        }
    }

    [Fact]
    public async Task QueueApprovedExecutionAsync_ReturnsAlreadyQueued_WhenInvestigationAlreadyQueued()
    {
        const string investigationId = "inv-queued";
        var state = CreateStateWithPlan(investigationId);
        state.RemediationExecutionInstances[investigationId] = "existing-instance";
        var executor = new RecordingExecutor();
        var scheduler = new RecordingScheduler();
        var workflow = CreateWorkflow(state, executor);
        var approval = CreateApproval(investigationId, ApprovalDecision.Approve);

        var queueResult = await workflow.QueueApprovedExecutionAsync(
            investigationId,
            approval,
            source: "test",
            scheduleOrchestration: scheduler.ScheduleAsync);

        Assert.Equal(QueueExecutionResult.AlreadyQueued, queueResult);
        Assert.Empty(scheduler.Requests);
        Assert.True(state.RemediationExecutionInstances.TryGetValue(investigationId, out var instanceId));
        Assert.Equal("existing-instance", instanceId);
        Assert.Equal(0, executor.Calls);
    }

    [Fact]
    public async Task QueueApprovedExecutionAsync_ReturnsQueueFailed_WhenSchedulerThrows()
    {
        const string investigationId = "inv-queue-failed";
        var state = CreateStateWithPlan(investigationId);
        var executor = new RecordingExecutor();
        var scheduler = new RecordingScheduler { ThrowOnSchedule = true };
        var workflow = CreateWorkflow(state, executor);
        var approval = CreateApproval(investigationId, ApprovalDecision.Approve);

        var queueResult = await workflow.QueueApprovedExecutionAsync(
            investigationId,
            approval,
            source: "test",
            scheduleOrchestration: scheduler.ScheduleAsync);

        Assert.Equal(QueueExecutionResult.QueueFailed, queueResult);
        Assert.False(state.RemediationExecutionInstances.ContainsKey(investigationId));
        Assert.Equal(0, executor.Calls);
    }

    [Fact]
    public async Task ExecuteQueuedRequestAsync_StoresSkippedOutcomes_WhenExecutionDisabled()
    {
        const string investigationId = "inv-exec-disabled";
        var plan = CreateStateWithPlan(investigationId).LatestRemediationPlans[investigationId];
        var approval = CreateApproval(investigationId, ApprovalDecision.Approve);
        var request = new RemediationExecutionRequest(
            InvestigationId: investigationId,
            Plan: plan,
            ApprovalRecord: approval,
            Source: "test",
            ExecutionEnabled: false);

        var state = new InMemoryState();
        var executor = new RecordingExecutor();
        var workflow = CreateWorkflow(state, executor);

        var summary = await workflow.ExecuteQueuedRequestAsync(request, CancellationToken.None);

        Assert.Equal(0, summary.OkCount);
        Assert.Equal(1, summary.SkippedCount);
        Assert.Equal(0, summary.DegradedCount);
        Assert.Equal(0, summary.ErrorCount);
        var outcomes = Assert.Single(state.LatestRemediationOutcomes[investigationId]);
        Assert.Equal(RemediationExecutionStatus.Skipped, outcomes.Status);
        Assert.Equal(0, executor.Calls);
    }

    [Fact]
    public async Task ExecuteQueuedRequestAsync_StoresOkOutcomes_WhenExecutionEnabled()
    {
        const string investigationId = "inv-exec-enabled";
        var plan = CreateStateWithPlan(investigationId).LatestRemediationPlans[investigationId];
        var approval = CreateApproval(investigationId, ApprovalDecision.Approve);
        var request = new RemediationExecutionRequest(
            InvestigationId: investigationId,
            Plan: plan,
            ApprovalRecord: approval,
            Source: "test",
            ExecutionEnabled: true);

        var state = new InMemoryState();
        var executor = new RecordingExecutor();
        var workflow = CreateWorkflow(state, executor);

        var summary = await workflow.ExecuteQueuedRequestAsync(request, CancellationToken.None);

        Assert.Equal(1, summary.OkCount);
        Assert.Equal(0, summary.SkippedCount);
        Assert.Equal(0, summary.DegradedCount);
        Assert.Equal(0, summary.ErrorCount);
        var outcomes = Assert.Single(state.LatestRemediationOutcomes[investigationId]);
        Assert.Equal(RemediationExecutionStatus.Ok, outcomes.Status);
        Assert.Equal(1, executor.Calls);
    }

    private static ApprovalRemediationWorkflow CreateWorkflow(InMemoryState state, IRemediationActionExecutor executor)
    {
        return new ApprovalRemediationWorkflow(
            state,
            executor,
            new StaticHttpClientFactory(),
            NullLogger<ApprovalRemediationWorkflow>.Instance);
    }

    private static InMemoryState CreateStateWithPlan(string investigationId)
    {
        var state = new InMemoryState();
        state.LatestRemediationPlans[investigationId] = new RemediationPlan(
            Summary: "plan",
            Actions:
            [
                new RemediationAction(
                    Type: RemediationActionType.StopVm,
                    TargetResourceId: "/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
                    Parameters: new Dictionary<string, object?>(),
                    RiskLevel: RemediationRiskLevel.High),
            ],
            RollbackNotes: "none");
        return state;
    }

    private static ApprovalRecord CreateApproval(string investigationId, ApprovalDecision decision)
    {
        return new ApprovalRecord(
            InvestigationId: investigationId,
            Decision: decision,
            DecidedBy: "tester",
            DecidedAt: DateTimeOffset.UtcNow,
            Reason: null);
    }
}
