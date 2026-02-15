using System;
using System.Collections.Generic;
using System.Net;
using System.Text.Json;
using System.Threading.Tasks;
using IncidentWarRoom.Core.Models;
using IncidentWarRoom.Core.Security;
using IncidentWarRoom.Functions.Http;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;

namespace IncidentWarRoom.Functions.Functions;

public sealed class DiscordInteractionsFunction
{
    private static readonly IReadOnlyDictionary<string, ApprovalDecision> ActionDecisionMap = new Dictionary<string, ApprovalDecision>(StringComparer.Ordinal)
    {
        ["approve_remediation"] = ApprovalDecision.Approve,
        ["reject_remediation"] = ApprovalDecision.Reject,
        ["investigate_more"] = ApprovalDecision.Investigate,
    };

    private readonly InMemoryState _state;
    private readonly ILogger<DiscordInteractionsFunction> _logger;

    public DiscordInteractionsFunction(InMemoryState state, ILogger<DiscordInteractionsFunction> logger)
    {
        _state = state;
        _logger = logger;
    }

    [Function("webhooks_discord_interactions")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/discord/interactions")] HttpRequestData req)
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
            bad.WriteString("invalid discord payload");
            return bad;
        }

        using (payloadDoc)
        {
            var root = payloadDoc.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                bad.WriteString("invalid discord payload");
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
                bad.WriteString("unsupported discord interaction type");
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
                bad.WriteString("invalid discord action");
                return bad;
            }

            var (actionId, investigationId) = parsed.Value;
            if (!ActionDecisionMap.TryGetValue(actionId, out var decision))
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                bad.WriteString("unsupported discord action");
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
                responseText = $"{responseText} Remediation execution has been queued.";
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
