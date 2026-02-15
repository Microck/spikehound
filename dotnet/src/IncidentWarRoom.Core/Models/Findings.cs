using System;
using System.Collections.Generic;
using System.Linq;

namespace IncidentWarRoom.Core.Models;

public sealed record CostFinding(string ResourceId, double Cost, string Currency);

public sealed record InvestigationFindings(
    string AlertId,
    DateTimeOffset ReceivedAt,
    IReadOnlyList<CostFinding> CostFindings,
    IReadOnlyDictionary<string, object?>? ResourceFindings,
    IReadOnlyDictionary<string, object?>? HistoryFindings,
    string Notes
);

public sealed record UnifiedFindings(
    IReadOnlyDictionary<string, object?> AlertSummary,
    IReadOnlyDictionary<AgentName, AgentResult<object?>> Results,
    string AlertId,
    DateTimeOffset ReceivedAt,
    IReadOnlyList<CostFinding> CostFindings,
    IReadOnlyDictionary<string, object?>? ResourceFindings,
    IReadOnlyDictionary<string, object?>? HistoryFindings,
    string Notes
)
{
    public static UnifiedFindings Merge(
        IEnumerable<AgentResult<object?>> results,
        IReadOnlyDictionary<string, object?>? alertSummary = null)
    {
        var merged = results
            .OrderBy(r => r.Agent.ToString(), StringComparer.Ordinal)
            .ThenBy(r => r.FinishedAt)
            .ThenBy(r => r.StartedAt)
            .ToDictionary(r => r.Agent, r => r);

        var summary = new Dictionary<string, object?>(alertSummary ?? new Dictionary<string, object?>());
        var alertId = (summary.TryGetValue("alert_id", out var rawAlertId) ? rawAlertId?.ToString() : null) ?? "unknown-alert";
        var receivedAt = summary.TryGetValue("received_at", out var rawReceivedAt) && rawReceivedAt is DateTimeOffset dto
            ? dto
            : DateTimeOffset.FromUnixTimeSeconds(0);

        List<CostFinding> costFindings = [];
        IReadOnlyDictionary<string, object?>? resourceFindings = null;
        IReadOnlyDictionary<string, object?>? historyFindings = null;
        var notes = "";

        if (merged.TryGetValue(AgentName.Cost, out var costResult) && costResult.Data is InvestigationFindings costData)
        {
            alertId = costData.AlertId;
            receivedAt = costData.ReceivedAt;
            costFindings = costData.CostFindings?.ToList() ?? [];
            notes = costData.Notes ?? "";
        }

        if (merged.TryGetValue(AgentName.Resource, out var resourceResult) && resourceResult.Data is IReadOnlyDictionary<string, object?> resourceData)
        {
            resourceFindings = resourceData;
        }

        if (merged.TryGetValue(AgentName.History, out var historyResult) && historyResult.Data is IReadOnlyDictionary<string, object?> historyData)
        {
            historyFindings = historyData;
        }

        return new UnifiedFindings(
            AlertSummary: summary,
            Results: merged,
            AlertId: alertId,
            ReceivedAt: receivedAt,
            CostFindings: costFindings,
            ResourceFindings: resourceFindings,
            HistoryFindings: historyFindings,
            Notes: notes
        );
    }
}

public sealed record InvestigationReport(
    UnifiedFindings UnifiedFindings,
    AgentResult<Diagnosis> DiagnosisResult,
    AgentResult<RemediationPlan> RemediationResult
);
