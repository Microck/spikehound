using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using IncidentWarRoom.Core.Models;
using IncidentWarRoom.Core.Parsing;

namespace IncidentWarRoom.Core.Orchestration;

public interface INotificationSink
{
    Task NotifyAsync(InvestigationReport report, CancellationToken cancellationToken);
}

public sealed class NoopNotificationSink : INotificationSink
{
    public static readonly NoopNotificationSink Instance = new();

    private NoopNotificationSink() { }

    public Task NotifyAsync(InvestigationReport report, CancellationToken cancellationToken) => Task.CompletedTask;
}

public interface IAgentRunner<TInput, TOutput>
{
    Task<AgentResult<TOutput>> RunAsync(TInput input, CancellationToken cancellationToken);
}

public sealed class CoordinatorPipeline
{
    private readonly IAgentRunner<JsonElement, InvestigationFindings> _costAgent;
    private readonly IAgentRunner<JsonElement, IReadOnlyDictionary<string, object?>> _resourceAgent;
    private readonly IAgentRunner<(JsonElement Raw, IReadOnlyDictionary<string, object?> AlertSummary), IReadOnlyDictionary<string, object?>> _historyAgent;
    private readonly IAgentRunner<UnifiedFindings, Diagnosis> _diagnosisAgent;
    private readonly IAgentRunner<(UnifiedFindings Findings, Diagnosis? Diagnosis), RemediationPlan> _remediationAgent;
    private readonly INotificationSink _notificationSink;
    private readonly TimeSpan _perAgentTimeout;
    private readonly Func<DateTimeOffset> _now;

    public CoordinatorPipeline(
        IAgentRunner<JsonElement, InvestigationFindings> costAgent,
        IAgentRunner<JsonElement, IReadOnlyDictionary<string, object?>> resourceAgent,
        IAgentRunner<(JsonElement Raw, IReadOnlyDictionary<string, object?> AlertSummary), IReadOnlyDictionary<string, object?>> historyAgent,
        IAgentRunner<UnifiedFindings, Diagnosis> diagnosisAgent,
        IAgentRunner<(UnifiedFindings Findings, Diagnosis? Diagnosis), RemediationPlan> remediationAgent,
        INotificationSink? notificationSink = null,
        TimeSpan? perAgentTimeout = null,
        Func<DateTimeOffset>? now = null)
    {
        _costAgent = costAgent;
        _resourceAgent = resourceAgent;
        _historyAgent = historyAgent;
        _diagnosisAgent = diagnosisAgent;
        _remediationAgent = remediationAgent;
        _notificationSink = notificationSink ?? NoopNotificationSink.Instance;
        _perAgentTimeout = perAgentTimeout ?? TimeSpan.FromSeconds(20);
        _now = now ?? (() => DateTimeOffset.UtcNow);
    }

    public async Task<InvestigationReport> HandleAlertAsync(JsonElement alertPayload, CancellationToken cancellationToken = default)
    {
        var receivedAt = _now();
        var normalized = AlertNormalizer.Normalize(alertPayload);

        var alertSummary = BuildAlertSummary(alertPayload, normalized, receivedAt);

        var costTask = RunWithTimeout(
            agent: AgentName.Cost,
            startedAt: _now(),
            runner: ct => _costAgent.RunAsync(alertPayload, ct),
            cancellationToken: cancellationToken);
        var resourceTask = RunWithTimeout(
            agent: AgentName.Resource,
            startedAt: _now(),
            runner: ct => _resourceAgent.RunAsync(alertPayload, ct),
            cancellationToken: cancellationToken);
        var historyTask = RunWithTimeout(
            agent: AgentName.History,
            startedAt: _now(),
            runner: ct => _historyAgent.RunAsync((alertPayload, alertSummary), ct),
            cancellationToken: cancellationToken);

        await Task.WhenAll(costTask, resourceTask, historyTask);
        var investigatorResults = new[]
        {
            Box(await costTask),
            Box(await resourceTask),
            Box(await historyTask),
        };

        var unified = UnifiedFindings.Merge(investigatorResults, alertSummary);

        var diagnosis = await RunWithTimeout(
            agent: AgentName.Diagnosis,
            startedAt: _now(),
            runner: ct => _diagnosisAgent.RunAsync(unified, ct),
            cancellationToken: cancellationToken);

        var diagnosisData = diagnosis.Data;
        var remediation = await RunWithTimeout(
            agent: AgentName.Remediation,
            startedAt: _now(),
            runner: ct => _remediationAgent.RunAsync((unified, diagnosisData), ct),
            cancellationToken: cancellationToken);

        var report = new InvestigationReport(
            UnifiedFindings: unified,
            DiagnosisResult: diagnosis,
            RemediationResult: remediation
        );

        try
        {
            await _notificationSink.NotifyAsync(report, cancellationToken);
        }
        catch
        {
            // Best-effort notifications. Surface failures in logs at the edge.
        }

        return report;
    }

    private static AgentResult<object?> Box<T>(AgentResult<T> result) =>
        new(
            Agent: result.Agent,
            Status: result.Status,
            StartedAt: result.StartedAt,
            FinishedAt: result.FinishedAt,
            Data: result.Data,
            Errors: result.Errors
        );

    private async Task<AgentResult<T>> RunWithTimeout<T>(
        AgentName agent,
        DateTimeOffset startedAt,
        Func<CancellationToken, Task<AgentResult<T>>> runner,
        CancellationToken cancellationToken)
    {
        using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeoutCts.CancelAfter(_perAgentTimeout);

        try
        {
            var result = await runner(timeoutCts.Token);
            if (result.Agent != agent)
            {
                return AgentResult<T>.Error(agent, startedAt, _now(), $"{agent.ToString().ToLowerInvariant()} agent returned unexpected agent id {result.Agent.ToString().ToLowerInvariant()}");
            }

            return new AgentResult<T>(
                Agent: agent,
                Status: result.Status,
                StartedAt: startedAt,
                FinishedAt: _now(),
                Data: result.Data,
                Errors: result.Errors
            );
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            return AgentResult<T>.Error(agent, startedAt, _now(), $"{agent.ToString().ToLowerInvariant()} agent timed out after {(int)_perAgentTimeout.TotalSeconds}s");
        }
        catch (Exception ex)
        {
            return AgentResult<T>.Error(agent, startedAt, _now(), $"{agent.ToString().ToLowerInvariant()} agent failed: {ex.Message}");
        }
    }

    private static IReadOnlyDictionary<string, object?> BuildAlertSummary(
        JsonElement raw,
        NormalizedAlert normalized,
        DateTimeOffset receivedAt)
    {
        var summary = new Dictionary<string, object?>
        {
            ["alert_id"] = normalized.AlertId,
            ["received_at"] = receivedAt,
            ["rule_name"] = normalized.RuleName,
            ["severity"] = normalized.Severity,
            ["fired_date_time"] = normalized.FiredDateTime,
            ["summary"] = normalized.Summary,
        };

        if (!string.IsNullOrWhiteSpace(normalized.ResourceId))
        {
            summary["resource_id"] = normalized.ResourceId;
        }

        // Preserve a small subset of top-level fields when present.
        foreach (var key in new[] { "title", "anomaly_type", "resource_name", "resource_type" })
        {
            if (raw.ValueKind == JsonValueKind.Object && raw.TryGetProperty(key, out var child) && child.ValueKind != JsonValueKind.Undefined)
            {
                summary[key] = child.ValueKind == JsonValueKind.String ? child.GetString() : child.ToString();
            }
        }

        return summary;
    }
}
