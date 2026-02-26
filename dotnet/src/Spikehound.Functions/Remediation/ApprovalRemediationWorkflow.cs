using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Core.Execution;
using Spikehound.Core.Models;
using Microsoft.Extensions.Logging;

namespace Spikehound.Functions.Remediation;

public enum QueueExecutionResult
{
    Queued,
    Disabled,
    AlreadyQueued,
    NoPlan,
    Ignored,
    QueueFailed,
}

public sealed class ApprovalRemediationWorkflow
{
    private const string PendingInstanceMarker = "__pending__";

    private readonly InMemoryState _state;
    private readonly IRemediationActionExecutor _executor;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<ApprovalRemediationWorkflow> _logger;

    public ApprovalRemediationWorkflow(
        InMemoryState state,
        IRemediationActionExecutor executor,
        IHttpClientFactory httpClientFactory,
        ILogger<ApprovalRemediationWorkflow> logger)
    {
        _state = state;
        _executor = executor;
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    public async Task<QueueExecutionResult> QueueApprovedExecutionAsync(
        string investigationId,
        ApprovalRecord approvalRecord,
        string source,
        Func<RemediationExecutionRequest, CancellationToken, Task<string>> scheduleOrchestration,
        CancellationToken cancellationToken = default)
    {
        if (approvalRecord.Decision != ApprovalDecision.Approve)
        {
            _logger.LogInformation(
                "remediation_execution_skipped: {investigationId} decision={decision}",
                investigationId,
                approvalRecord.Decision);
            return QueueExecutionResult.Ignored;
        }

        if (!_state.LatestRemediationPlans.TryGetValue(investigationId, out var plan) || plan.Actions.Count == 0)
        {
            _logger.LogWarning(
                "remediation_execution_skipped: {investigationId} no remediation plan available",
                investigationId);
            return QueueExecutionResult.NoPlan;
        }

        var executionEnabled = IsExecutionEnabled();
        var request = new RemediationExecutionRequest(
            InvestigationId: investigationId,
            Plan: plan,
            ApprovalRecord: approvalRecord,
            Source: source,
            ExecutionEnabled: executionEnabled);

        if (!_state.RemediationExecutionInstances.TryAdd(investigationId, PendingInstanceMarker))
        {
            var existingInstanceId = _state.RemediationExecutionInstances.TryGetValue(investigationId, out var existing)
                ? existing
                : "unknown";

            _logger.LogInformation(
                "remediation_execution_already_queued: {investigationId} source={source} existingInstanceId={instanceId}",
                investigationId,
                source,
                existingInstanceId);

            return QueueExecutionResult.AlreadyQueued;
        }

        try
        {
            var instanceId = await scheduleOrchestration(request, cancellationToken);
            _state.RemediationExecutionInstances[investigationId] = instanceId;

            _logger.LogInformation(
                "remediation_execution_queued: {investigationId} source={source} actions={actionCount} enabled={enabled} instanceId={instanceId}",
                investigationId,
                source,
                plan.Actions.Count,
                executionEnabled,
                instanceId);

            return executionEnabled ? QueueExecutionResult.Queued : QueueExecutionResult.Disabled;
        }
        catch (Exception ex)
        {
            _state.RemediationExecutionInstances.TryRemove(investigationId, out _);
            _logger.LogError(ex, "remediation_execution_queue_failed: {investigationId} source={source}", investigationId, source);
            return QueueExecutionResult.QueueFailed;
        }
    }

    public async Task<RemediationExecutionSummary> ExecuteQueuedRequestAsync(
        RemediationExecutionRequest request,
        CancellationToken cancellationToken)
    {
        var investigationId = request.InvestigationId;
        try
        {
            _logger.LogInformation("remediation_execution_started: {investigationId}", investigationId);

            IReadOnlyList<RemediationExecutionOutcome> outcomes;
            if (!request.ExecutionEnabled)
            {
                outcomes = BuildDisabledOutcomes(request.Plan);
                _logger.LogWarning(
                    "remediation_execution_disabled: {investigationId} set SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION=true to enable",
                    investigationId);
            }
            else
            {
                outcomes = await RemediationExecutionEngine.ExecuteAsync(request.Plan, request.ApprovalRecord, _executor, cancellationToken);
            }

            _state.LatestRemediationOutcomes[investigationId] = outcomes;

            var followupMessage = BuildFollowupMessage(investigationId, request.Source, request.ApprovalRecord, outcomes);
            await SendFollowupNotificationsAsync(
                followupMessage,
                cancellationToken);

            var summary = new RemediationExecutionSummary(
                InvestigationId: investigationId,
                OkCount: outcomes.Count(x => x.Status == RemediationExecutionStatus.Ok),
                SkippedCount: outcomes.Count(x => x.Status == RemediationExecutionStatus.Skipped),
                DegradedCount: outcomes.Count(x => x.Status == RemediationExecutionStatus.Degraded),
                ErrorCount: outcomes.Count(x => x.Status == RemediationExecutionStatus.Error));

            _logger.LogInformation(
                "remediation_execution_completed: {investigationId} ok={ok} skipped={skipped} degraded={degraded} error={error}",
                investigationId,
                summary.OkCount,
                summary.SkippedCount,
                summary.DegradedCount,
                summary.ErrorCount);

            return summary;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "remediation_execution_failed: {investigationId}", investigationId);
            throw;
        }
    }

    private async Task SendFollowupNotificationsAsync(string message, CancellationToken cancellationToken)
    {
        var slackUrl = Environment.GetEnvironmentVariable("SLACK_WEBHOOK_URL") ?? string.Empty;
        if (!string.IsNullOrWhiteSpace(slackUrl))
        {
            await PostSlackAsync(slackUrl, message, cancellationToken);
        }

        var discordBotToken = Environment.GetEnvironmentVariable("DISCORD_BOT_TOKEN") ?? string.Empty;
        var discordChannelId = Environment.GetEnvironmentVariable("DISCORD_CHANNEL_ID") ?? string.Empty;
        if (!string.IsNullOrWhiteSpace(discordBotToken) && !string.IsNullOrWhiteSpace(discordChannelId))
        {
            await PostDiscordBotAsync(discordChannelId, discordBotToken, message, cancellationToken);
            return;
        }

        var discordWebhookUrl = Environment.GetEnvironmentVariable("DISCORD_WEBHOOK_URL") ?? string.Empty;
        if (!string.IsNullOrWhiteSpace(discordWebhookUrl))
        {
            await PostDiscordWebhookAsync(discordWebhookUrl, message, cancellationToken);
        }
    }

    private async Task PostSlackAsync(string url, string message, CancellationToken cancellationToken)
    {
        try
        {
            var client = _httpClientFactory.CreateClient();
            using var resp = await client.PostAsJsonAsync(url, new { text = message }, cancellationToken);
            resp.EnsureSuccessStatusCode();
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "slack_remediation_followup_failed");
        }
    }

    private async Task PostDiscordWebhookAsync(string url, string message, CancellationToken cancellationToken)
    {
        try
        {
            var client = _httpClientFactory.CreateClient();
            using var resp = await client.PostAsJsonAsync(url, new
            {
                content = message,
                allowed_mentions = new { parse = Array.Empty<string>() },
            }, cancellationToken);
            resp.EnsureSuccessStatusCode();
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "discord_remediation_followup_failed");
        }
    }

    private async Task PostDiscordBotAsync(string channelId, string botToken, string message, CancellationToken cancellationToken)
    {
        try
        {
            var client = _httpClientFactory.CreateClient();
            using var request = new HttpRequestMessage(HttpMethod.Post, $"https://discord.com/api/v10/channels/{channelId}/messages")
            {
                Content = JsonContent.Create(new
                {
                    content = message,
                    allowed_mentions = new { parse = Array.Empty<string>() },
                }),
            };
            request.Headers.Authorization = new AuthenticationHeaderValue("Bot", botToken);

            using var resp = await client.SendAsync(request, cancellationToken);
            resp.EnsureSuccessStatusCode();
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "discord_remediation_followup_failed");
        }
    }

    private static IReadOnlyList<RemediationExecutionOutcome> BuildDisabledOutcomes(RemediationPlan plan)
    {
        var outcomes = new List<RemediationExecutionOutcome>(plan.Actions.Count);
        foreach (var action in plan.Actions)
        {
            var now = DateTimeOffset.UtcNow;
            outcomes.Add(new RemediationExecutionOutcome(
                ActionType: action.Type,
                TargetResourceId: action.TargetResourceId,
                Status: RemediationExecutionStatus.Skipped,
                Message: "Execution disabled. Set SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION=true to execute approved actions.",
                StartedAt: now,
                FinishedAt: now));
        }

        return outcomes;
    }

    private static string BuildFollowupMessage(
        string investigationId,
        string source,
        ApprovalRecord approvalRecord,
        IReadOnlyList<RemediationExecutionOutcome> outcomes)
    {
        var lines = new List<string>
        {
            $"Remediation follow-up for `{investigationId}` ({source} approval by `{approvalRecord.DecidedBy}`):"
        };

        foreach (var outcome in outcomes)
        {
            var action = outcome.ActionType.ToString().ToLowerInvariant();
            var status = outcome.Status.ToString().ToLowerInvariant();
            lines.Add($"- {action}: {status} ({outcome.Message})");
        }

        return string.Join("\n", lines);
    }

    private static bool IsExecutionEnabled() =>
        string.Equals(
            Environment.GetEnvironmentVariable("SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION"),
            "true",
            StringComparison.OrdinalIgnoreCase);
}
