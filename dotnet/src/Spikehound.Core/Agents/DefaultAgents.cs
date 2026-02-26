using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Core.Models;
using Spikehound.Core.Orchestration;
using Spikehound.Core.Parsing;

namespace Spikehound.Core.Agents;

public static class CloudGate
{
    public static bool IsEnabled() =>
        string.Equals(Environment.GetEnvironmentVariable("SPIKEHOUND_CLOUD_ENABLED"), "true", StringComparison.OrdinalIgnoreCase);
}

public sealed class FallbackCostAgent : IAgentRunner<JsonElement, InvestigationFindings>
{
    public Task<AgentResult<InvestigationFindings>> RunAsync(JsonElement input, CancellationToken cancellationToken)
    {
        var normalized = AlertNormalizer.Normalize(input);
        var now = DateTimeOffset.UtcNow;
        var resourceId = normalized.ResourceId ?? "unknown-resource";

        var findings = new InvestigationFindings(
            AlertId: normalized.AlertId,
            ReceivedAt: now,
            CostFindings: new[]
            {
                new CostFinding(resourceId, 450.00, "USD/day"),
            },
            ResourceFindings: null,
            HistoryFindings: null,
            Notes: "Baseline spend: $12.50/day. Current spend: $450.00/day (36x anomaly factor). Spike began 72 hours ago."
        );

        return Task.FromResult(
            new AgentResult<InvestigationFindings>(
                Agent: AgentName.Cost,
                Status: AgentStatus.Ok,
                StartedAt: now,
                FinishedAt: now.AddMilliseconds(180),
                Data: findings,
                Errors: Array.Empty<string>()));
    }
}

public sealed class FallbackResourceAgent : IAgentRunner<JsonElement, IReadOnlyDictionary<string, object?>>
{
    public Task<AgentResult<IReadOnlyDictionary<string, object?>>> RunAsync(JsonElement input, CancellationToken cancellationToken)
    {
        var normalized = AlertNormalizer.Normalize(input);
        var now = DateTimeOffset.UtcNow;
        var payload = new Dictionary<string, object?>
        {
            ["resource_id"] = normalized.ResourceId,
            ["resource_type"] = "Microsoft.Compute/virtualMachines",
            ["vm_size"] = "Standard_D2s_v3",
            ["location"] = "polandcentral",
            ["power_state"] = "VM running",
            ["uptime_hours"] = 72,
            ["tags"] = "environment=dev, owner=ml-team, project=training-pipeline",
            ["notes"] = "VM has been running for 72 hours with no active compute jobs. Last SSH session ended 71 hours ago.",
        };

        return Task.FromResult(
            new AgentResult<IReadOnlyDictionary<string, object?>>(
                Agent: AgentName.Resource,
                Status: AgentStatus.Ok,
                StartedAt: now,
                FinishedAt: now.AddMilliseconds(210),
                Data: payload,
                Errors: Array.Empty<string>()));
    }
}

public sealed class FallbackHistoryAgent : IAgentRunner<(JsonElement Raw, IReadOnlyDictionary<string, object?> AlertSummary), IReadOnlyDictionary<string, object?>>
{
    public Task<AgentResult<IReadOnlyDictionary<string, object?>>> RunAsync(
        (JsonElement Raw, IReadOnlyDictionary<string, object?> AlertSummary) input,
        CancellationToken cancellationToken)
    {
        var now = DateTimeOffset.UtcNow;
        var payload = new Dictionary<string, object?>
        {
            ["alert_id"] = input.AlertSummary.TryGetValue("alert_id", out var value) ? value?.ToString() : null,
            ["prior_incidents"] = 0,
            ["resource_history"] = "VM created 5 days ago for ML training batch. Training job completed 72 hours ago. No scheduled deallocate policy found.",
            ["notes"] = "No prior cost anomaly alerts for this resource. First occurrence.",
        };

        return Task.FromResult(
            new AgentResult<IReadOnlyDictionary<string, object?>>(
                Agent: AgentName.History,
                Status: AgentStatus.Ok,
                StartedAt: now,
                FinishedAt: now.AddMilliseconds(150),
                Data: payload,
                Errors: Array.Empty<string>()));
    }
}

public sealed class FallbackDiagnosisAgent : IAgentRunner<UnifiedFindings, Diagnosis>
{
    public Task<AgentResult<Diagnosis>> RunAsync(UnifiedFindings input, CancellationToken cancellationToken)
    {
        var now = DateTimeOffset.UtcNow;

        var hypothesis = new RootCauseHypothesis(
            Title: "Orphaned GPU VM after training job completion",
            Explanation: "GPU VM left running after ML training job completed 72 hours ago. No auto-shutdown policy configured. Estimated waste: $450/day ($13,500/month projected).",
            Evidence: new[]
            {
                "VM uptime: 72 hours with no active compute jobs",
                "Last SSH session ended 71 hours ago",
                "No auto-shutdown policy or deallocate schedule found",
                "Cost anomaly factor: 36x baseline ($12.50/day → $450/day)",
            }
        );

        var diagnosis = new Diagnosis(
            Hypothesis: hypothesis,
            Confidence: 85,
            Alternatives: new[]
            {
                "Intentional long-running job not yet reflected in scheduler (unlikely — no active processes found)",
            },
            Risks: new[]
            {
                "If VM is deallocated, any unsaved state on ephemeral disks will be lost.",
            }
        );

        return Task.FromResult(
            new AgentResult<Diagnosis>(
                Agent: AgentName.Diagnosis,
                Status: AgentStatus.Ok,
                StartedAt: now,
                FinishedAt: now.AddMilliseconds(320),
                Data: diagnosis,
                Errors: Array.Empty<string>()));
    }
}

public sealed class FallbackRemediationAgent : IAgentRunner<(UnifiedFindings Findings, Diagnosis? Diagnosis), RemediationPlan>
{
    public Task<AgentResult<RemediationPlan>> RunAsync(
        (UnifiedFindings Findings, Diagnosis? Diagnosis) input,
        CancellationToken cancellationToken)
    {
        var now = DateTimeOffset.UtcNow;

        var resourceId = input.Findings.ResourceFindings != null && input.Findings.ResourceFindings.TryGetValue("resource_id", out var rid)
            ? rid?.ToString()
            : input.Findings.AlertSummary.GetValueOrDefault("resource_id")?.ToString();

        var actions = new List<RemediationAction>();
        if (!string.IsNullOrWhiteSpace(resourceId) && resourceId.Contains("/virtualMachines/", StringComparison.OrdinalIgnoreCase))
        {
            actions.Add(
                new RemediationAction(
                    Type: RemediationActionType.StopVm,
                    TargetResourceId: resourceId,
                    Parameters: new Dictionary<string, object?>(),
                    RiskLevel: RemediationRiskLevel.High));
        }

        actions.Add(
            new RemediationAction(
                Type: RemediationActionType.NotifyOwner,
                TargetResourceId: resourceId ?? "unknown-resource",
                Parameters: new Dictionary<string, object?>(),
                RiskLevel: RemediationRiskLevel.Low));

        var plan = new RemediationPlan(
            Summary: "Deallocate orphaned VM and notify resource owner. Estimated savings: $450/day.",
            Actions: actions,
            RollbackNotes: "To restore: az vm start --name spikehound-gpu-vm --resource-group spikehound-demo-rg"
        );

        return Task.FromResult(
            new AgentResult<RemediationPlan>(
                Agent: AgentName.Remediation,
                Status: AgentStatus.Ok,
                StartedAt: now,
                FinishedAt: now.AddMilliseconds(90),
                Data: plan,
                Errors: Array.Empty<string>()));
    }
}

internal static class DictionaryExtensions
{
    public static object? GetValueOrDefault(this IReadOnlyDictionary<string, object?> dictionary, string key) =>
        dictionary.TryGetValue(key, out var value) ? value : null;
}
