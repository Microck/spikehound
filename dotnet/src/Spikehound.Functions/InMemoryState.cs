using System;
using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;
using Spikehound.Core.Execution;
using Spikehound.Core.Models;

namespace Spikehound.Functions;

public sealed class InMemoryState
{
    private const string DiscordTokenPrefix = "inv_";

    private readonly ConcurrentDictionary<string, (DateTimeOffset CachedAt, InvestigationReport Report)> _processed = new();

    public ConcurrentDictionary<string, ApprovalRecord> ApprovalRecords { get; } = new();
    public ConcurrentDictionary<string, InvestigationReport> LatestReports { get; } = new();
    public ConcurrentDictionary<string, RemediationPlan> LatestRemediationPlans { get; } = new();
    public ConcurrentDictionary<string, IReadOnlyList<RemediationExecutionOutcome>> LatestRemediationOutcomes { get; } = new();
    public ConcurrentDictionary<string, string> RemediationExecutionInstances { get; } = new();
    public ConcurrentDictionary<string, string> DiscordInvestigationTokens { get; } = new();

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

    public string RememberDiscordInvestigationToken(string investigationId)
    {
        var token = CreateDiscordInvestigationToken(investigationId);
        DiscordInvestigationTokens[token] = investigationId;
        return token;
    }

    public bool TryResolveDiscordInvestigationToken(string token, out string investigationId) =>
        DiscordInvestigationTokens.TryGetValue(token, out investigationId!);

    private static string CreateDiscordInvestigationToken(string investigationId)
    {
        var bytes = Encoding.UTF8.GetBytes(investigationId);
        var hash = SHA256.HashData(bytes);
        var token = Convert.ToBase64String(hash)
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');
        return $"{DiscordTokenPrefix}{token}";
    }
}
