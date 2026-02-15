using System;
using System.Collections.Concurrent;
using IncidentWarRoom.Core.Models;

namespace IncidentWarRoom.Functions;

public sealed class InMemoryState
{
    private readonly ConcurrentDictionary<string, (DateTimeOffset CachedAt, InvestigationReport Report)> _processed = new();

    public ConcurrentDictionary<string, ApprovalRecord> ApprovalRecords { get; } = new();
    public ConcurrentDictionary<string, InvestigationReport> LatestReports { get; } = new();
    public ConcurrentDictionary<string, RemediationPlan> LatestRemediationPlans { get; } = new();

    public bool TryGetCachedReport(string investigationId, DateTimeOffset now, TimeSpan ttl, out InvestigationReport report)
    {
        if (_processed.TryGetValue(investigationId, out var entry))
        {
            if (now - entry.CachedAt <= ttl)
            {
                report = entry.Report;
                return true;
            }

            _processed.TryRemove(investigationId, out _);
        }

        report = default!;
        return false;
    }

    public void StoreReport(string investigationId, DateTimeOffset now, InvestigationReport report)
    {
        LatestReports[investigationId] = report;
        if (report.RemediationResult.Data is not null)
        {
            LatestRemediationPlans[investigationId] = report.RemediationResult.Data;
        }
        else
        {
            LatestRemediationPlans.TryRemove(investigationId, out _);
        }

        _processed[investigationId] = (now, report);
    }

    public void PruneExpired(DateTimeOffset now, TimeSpan ttl)
    {
        foreach (var pair in _processed)
        {
            if (now - pair.Value.CachedAt > ttl)
            {
                _processed.TryRemove(pair.Key, out _);
            }
        }
    }
}
