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
        var receivedAt = DateTimeOffset.UtcNow;

        var findings = new InvestigationFindings(
            AlertId: normalized.AlertId,
            ReceivedAt: receivedAt,
            CostFindings: Array.Empty<CostFinding>(),
            ResourceFindings: null,
            HistoryFindings: null,
            Notes: CloudGate.IsEnabled()
                ? "Cloud enabled but Cost agent is running in demo fallback mode."
                : "Cloud calls disabled (set SPIKEHOUND_CLOUD_ENABLED=true to enable)."
        );

        return Task.FromResult(
            AgentResult<InvestigationFindings>.Degraded(
                AgentName.Cost,
                DateTimeOffset.FromUnixTimeSeconds(0),
                DateTimeOffset.FromUnixTimeSeconds(0),
                findings,
                findings.Notes));
    }
}

public sealed class FallbackResourceAgent : IAgentRunner<JsonElement, IReadOnlyDictionary<string, object?>>
{
    public Task<AgentResult<IReadOnlyDictionary<string, object?>>> RunAsync(JsonElement input, CancellationToken cancellationToken)
    {
        var normalized = AlertNormalizer.Normalize(input);
        var payload = new Dictionary<string, object?>
        {
            ["resource_id"] = normalized.ResourceId,
            ["notes"] = CloudGate.IsEnabled()
                ? "Cloud enabled but Resource agent is running in demo fallback mode."
                : "Cloud calls disabled (set SPIKEHOUND_CLOUD_ENABLED=true to enable).",
        };

        return Task.FromResult(
            AgentResult<IReadOnlyDictionary<string, object?>>.Degraded(
                AgentName.Resource,
                DateTimeOffset.FromUnixTimeSeconds(0),
                DateTimeOffset.FromUnixTimeSeconds(0),
                payload,
                (string)payload["notes"]!));
    }
}

public sealed class FallbackHistoryAgent : IAgentRunner<(JsonElement Raw, IReadOnlyDictionary<string, object?> AlertSummary), IReadOnlyDictionary<string, object?>>
{
    public Task<AgentResult<IReadOnlyDictionary<string, object?>>> RunAsync(
        (JsonElement Raw, IReadOnlyDictionary<string, object?> AlertSummary) input,
        CancellationToken cancellationToken)
    {
        var payload = new Dictionary<string, object?>
        {
            ["alert_id"] = input.AlertSummary.TryGetValue("alert_id", out var value) ? value?.ToString() : null,
            ["notes"] = CloudGate.IsEnabled()
                ? "Cloud enabled but History agent is running in demo fallback mode."
                : "Cloud calls disabled (set SPIKEHOUND_CLOUD_ENABLED=true to enable).",
        };

        return Task.FromResult(
            AgentResult<IReadOnlyDictionary<string, object?>>.Degraded(
                AgentName.History,
                DateTimeOffset.FromUnixTimeSeconds(0),
                DateTimeOffset.FromUnixTimeSeconds(0),
                payload,
                (string)payload["notes"]!));
    }
}

public sealed class FallbackDiagnosisAgent : IAgentRunner<UnifiedFindings, Diagnosis>
{
    public Task<AgentResult<Diagnosis>> RunAsync(UnifiedFindings input, CancellationToken cancellationToken)
    {
        var hypothesis = new RootCauseHypothesis(
            Title: "Diagnosis unavailable (demo fallback)",
            Explanation: "This run used deterministic fallback logic because cloud/LLM services are not configured.",
            Evidence: new[] { $"AlertId={input.AlertId}", $"Severity={input.AlertSummary.GetValueOrDefault("severity")}" }
        );

        var diagnosis = new Diagnosis(
            Hypothesis: hypothesis,
            Confidence: 55,
            Alternatives: Array.Empty<string>(),
            Risks: new[] { "Fallback diagnosis may be incomplete." }
        );

        var status = CloudGate.IsEnabled() ? AgentStatus.Degraded : AgentStatus.Degraded;
        return Task.FromResult(
            new AgentResult<Diagnosis>(
                Agent: AgentName.Diagnosis,
                Status: status,
                StartedAt: DateTimeOffset.FromUnixTimeSeconds(0),
                FinishedAt: DateTimeOffset.FromUnixTimeSeconds(0),
                Data: diagnosis,
                Errors: new[] { "Using fallback diagnosis" }));
    }
}

public sealed class FallbackRemediationAgent : IAgentRunner<(UnifiedFindings Findings, Diagnosis? Diagnosis), RemediationPlan>
{
    public Task<AgentResult<RemediationPlan>> RunAsync(
        (UnifiedFindings Findings, Diagnosis? Diagnosis) input,
        CancellationToken cancellationToken)
    {
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
            Summary: "Safe-by-default remediation plan (requires human approval)",
            Actions: actions,
            RollbackNotes: "Review changes and reverse any resource actions if executed."
        );

        return Task.FromResult(
            AgentResult<RemediationPlan>.Degraded(
                AgentName.Remediation,
                DateTimeOffset.FromUnixTimeSeconds(0),
                DateTimeOffset.FromUnixTimeSeconds(0),
                plan,
                "Using fallback remediation"));
    }
}

internal static class DictionaryExtensions
{
    public static object? GetValueOrDefault(this IReadOnlyDictionary<string, object?> dictionary, string key) =>
        dictionary.TryGetValue(key, out var value) ? value : null;
}
