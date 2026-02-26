using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Core.Agents;
using Spikehound.Core.Models;
using Spikehound.Core.Orchestration;
using Xunit;

namespace Spikehound.Core.Tests;

public sealed class CoordinatorPipelineTests
{
    private sealed class RecordingNotificationSink : INotificationSink
    {
        public int Calls { get; private set; }

        public Task NotifyAsync(InvestigationReport report, CancellationToken cancellationToken)
        {
            Calls++;
            return Task.CompletedTask;
        }
    }

    [Fact]
    public async Task HandleAlertAsync_ComposesInvestigationDiagnosisRemediation_AndNotifies()
    {
        using var doc = JsonDocument.Parse(
            "{\"alert_id\":\"alert-1\",\"rule_name\":\"cost-spike\",\"severity\":\"Sev3\",\"resource_id\":\"/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1\"}"
        );

        var sink = new RecordingNotificationSink();
        var pipeline = new CoordinatorPipeline(
            costAgent: new FallbackCostAgent(),
            resourceAgent: new FallbackResourceAgent(),
            historyAgent: new FallbackHistoryAgent(),
            diagnosisAgent: new FallbackDiagnosisAgent(),
            remediationAgent: new FallbackRemediationAgent(),
            notificationSink: sink);

        var report = await pipeline.HandleAlertAsync(doc.RootElement);

        Assert.Equal("alert-1", report.UnifiedFindings.AlertId);
        Assert.NotNull(report.UnifiedFindings.Results[AgentName.Cost]);
        Assert.NotNull(report.UnifiedFindings.Results[AgentName.Resource]);
        Assert.NotNull(report.UnifiedFindings.Results[AgentName.History]);

        Assert.Equal(AgentName.Diagnosis, report.DiagnosisResult.Agent);
        Assert.NotNull(report.DiagnosisResult.Data);

        Assert.Equal(AgentName.Remediation, report.RemediationResult.Agent);
        Assert.NotNull(report.RemediationResult.Data);
        Assert.NotEmpty(report.RemediationResult.Data!.Actions);
        foreach (var action in report.RemediationResult.Data!.Actions)
        {
            Assert.True(action.HumanApprovalRequired);
        }

        Assert.Equal(1, sink.Calls);
    }
}
