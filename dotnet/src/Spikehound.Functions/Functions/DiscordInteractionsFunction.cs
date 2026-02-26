using System;
using System.Collections.Generic;
using System.Net;
using System.Text.Json;
using System.Threading.Tasks;
using Spikehound.Core.Models;
using Spikehound.Core.Security;
using Spikehound.Functions.Http;
using Spikehound.Functions.Remediation;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.Functions.Worker.Extensions.DurableTask;
using Microsoft.DurableTask.Client;
using Microsoft.Extensions.Logging;

namespace Spikehound.Functions.Functions;

public sealed class DiscordInteractionsFunction
{
    private static readonly IReadOnlyDictionary<string, ApprovalDecision> ActionDecisionMap = new Dictionary<string, ApprovalDecision>(StringComparer.Ordinal)
    {
        ["approve_remediation"] = ApprovalDecision.Approve,
        ["reject_remediation"] = ApprovalDecision.Reject,
        ["investigate_more"] = ApprovalDecision.Investigate,
    };

    private readonly InMemoryState _state;
    private readonly ApprovalRemediationWorkflow _approvalWorkflow;
    private readonly ILogger<DiscordInteractionsFunction> _logger;

    public DiscordInteractionsFunction(
        InMemoryState state,
        ApprovalRemediationWorkflow approvalWorkflow,
        ILogger<DiscordInteractionsFunction> logger)
    {
        _state = state;
        _approvalWorkflow = approvalWorkflow;
        _logger = logger;
    }

    [Function("webhooks_discord_interactions")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/discord/interactions")] HttpRequestData req,
        [DurableClient] DurableTaskClient durableClient)
    {
        var bodyBytes = await HttpUtils.ReadBodyBytesAsync(req);
        var headers = HttpUtils.HeadersToDictionary(req.Headers);
        var publicKeyHex = Environment.GetEnvironmentVariable("DISCORD_INTERACTIONS_PUBLIC_KEY") ?? string.Empty;

        if (!DiscordSignatureVerifier.Verify(bodyBytes, headers, publicKeyHex, HttpUtils.NowEpochSeconds()))
        {
            return req.CreateResponse(HttpStatusCode.Unauthorized);
        }

        JsonDocument payloadDoc;
        try
        {
            payloadDoc = JsonDocument.Parse(bodyBytes);
        }
        catch (JsonException)
        {
            var bad = req.CreateResponse(HttpStatusCode.BadRequest);
            await HttpUtils.WritePlainTextAsync(bad, "invalid discord payload");
            return bad;
        }

        using (payloadDoc)
        {
            var root = payloadDoc.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "invalid discord payload");
                return bad;
            }

            var interactionType = root.TryGetProperty("type", out var typeEl) && typeEl.ValueKind == JsonValueKind.Number
                ? typeEl.GetInt32()
                : -1;

            if (interactionType == 1)
            {
                var pong = req.CreateResponse(HttpStatusCode.OK);
                await pong.WriteAsJsonAsync(new { type = 1 });
                return pong;
            }

            if (interactionType != 3)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "unsupported discord interaction type");
                return bad;
            }

            var customId = root.TryGetProperty("data", out var dataEl) && dataEl.ValueKind == JsonValueKind.Object &&
                           dataEl.TryGetProperty("custom_id", out var customEl) && customEl.ValueKind == JsonValueKind.String
                ? (customEl.GetString() ?? "")
                : "";

            var parsed = ParseCustomId(customId);
            if (parsed is null)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "invalid discord action");
                return bad;
            }

            var (actionId, investigationReference) = parsed.Value;
            if (!ActionDecisionMap.TryGetValue(actionId, out var decision))
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "unsupported discord action");
                return bad;
            }

            var investigationId = ResolveInvestigationId(investigationReference);
            if (string.IsNullOrWhiteSpace(investigationId))
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "unknown discord investigation id");
                return bad;
            }

            var decidedBy = ExtractDiscordUserIdentifier(root);
            var record = new ApprovalRecord(
                InvestigationId: investigationId,
                Decision: decision,
                DecidedBy: decidedBy,
                DecidedAt: DateTimeOffset.UtcNow,
                Reason: decision == ApprovalDecision.Investigate ? "Requested additional investigation" : null);

            _state.ApprovalRecords[investigationId] = record;
            _logger.LogInformation("discord_approval_recorded: {investigationId} {decision} {decidedBy}", investigationId, decision, decidedBy);

            var responseText = $"Recorded **{decision.ToString().ToLowerInvariant()}** decision for investigation `{investigationId}`.";
            if (decision == ApprovalDecision.Approve)
            {
                var queueResult = await _approvalWorkflow.QueueApprovedExecutionAsync(
                    investigationId,
                    record,
                    source: "discord",
                    scheduleOrchestration: (executionRequest, _) =>
                        durableClient.ScheduleNewOrchestrationInstanceAsync("RemediationExecutionOrchestrator", executionRequest));

                responseText = queueResult switch
                {
                    QueueExecutionResult.Queued => $"{responseText} Remediation execution has been queued.",
                    QueueExecutionResult.Disabled => $"{responseText} Execution is currently disabled by configuration.",
                    QueueExecutionResult.AlreadyQueued => $"{responseText} Remediation execution has already been queued.",
                    QueueExecutionResult.NoPlan => $"{responseText} No remediation plan was available to execute.",
                    QueueExecutionResult.QueueFailed => $"{responseText} Failed to queue remediation execution.",
                    _ => responseText,
                };
            }

            var res = req.CreateResponse(HttpStatusCode.OK);
            await res.WriteAsJsonAsync(new
            {
                type = 4,
                data = new { content = responseText, flags = 64 }
            });
            return res;
        }
    }

    private static (string ActionId, string InvestigationId)? ParseCustomId(string customId)
    {
        var idx = customId.IndexOf(':');
        if (idx <= 0 || idx >= customId.Length - 1)
        {
            return null;
        }

        return (customId[..idx], customId[(idx + 1)..]);
    }

    private string ResolveInvestigationId(string investigationReference)
    {
        if (string.IsNullOrWhiteSpace(investigationReference))
        {
            return string.Empty;
        }

        return _state.TryResolveDiscordInvestigationToken(investigationReference, out var investigationId)
            ? investigationId
            : investigationReference;
    }

    private static string ExtractDiscordUserIdentifier(JsonElement payload)
    {
        if (payload.TryGetProperty("member", out var member) && member.ValueKind == JsonValueKind.Object &&
            member.TryGetProperty("user", out var user) && user.ValueKind == JsonValueKind.Object)
        {
            if (user.TryGetProperty("username", out var username) && username.ValueKind == JsonValueKind.String)
            {
                var value = username.GetString();
                if (!string.IsNullOrWhiteSpace(value))
                {
                    return value;
                }
            }
        }

        if (payload.TryGetProperty("user", out var rootUser) && rootUser.ValueKind == JsonValueKind.Object &&
            rootUser.TryGetProperty("username", out var rootUsername) && rootUsername.ValueKind == JsonValueKind.String)
        {
            var value = rootUsername.GetString();
            if (!string.IsNullOrWhiteSpace(value))
            {
                return value;
            }
        }

        return "unknown-user";
    }
}
