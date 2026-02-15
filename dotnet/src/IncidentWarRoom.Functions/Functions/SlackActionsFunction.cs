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

public sealed class SlackActionsFunction
{
    private static readonly IReadOnlyDictionary<string, ApprovalDecision> ActionDecisionMap = new Dictionary<string, ApprovalDecision>(StringComparer.Ordinal)
    {
        ["approve_remediation"] = ApprovalDecision.Approve,
        ["reject_remediation"] = ApprovalDecision.Reject,
        ["investigate_more"] = ApprovalDecision.Investigate,
    };

    private readonly InMemoryState _state;
    private readonly ILogger<SlackActionsFunction> _logger;

    public SlackActionsFunction(InMemoryState state, ILogger<SlackActionsFunction> logger)
    {
        _state = state;
        _logger = logger;
    }

    [Function("webhooks_slack_actions")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/slack/actions")] HttpRequestData req)
    {
        var bodyBytes = await HttpUtils.ReadBodyBytesAsync(req);
        var headers = HttpUtils.HeadersToDictionary(req.Headers);
        var secret = Environment.GetEnvironmentVariable("SLACK_SIGNING_SECRET") ?? string.Empty;

        if (!SlackSignatureVerifier.Verify(bodyBytes, headers, secret, HttpUtils.NowEpochSeconds()))
        {
            return req.CreateResponse(HttpStatusCode.Unauthorized);
        }

        var bodyText = System.Text.Encoding.UTF8.GetString(bodyBytes);
        var form = HttpUtils.ParseFormUrlEncoded(bodyText);
        if (!form.TryGetValue("payload", out var payloadRaw) || string.IsNullOrWhiteSpace(payloadRaw))
        {
            var bad = req.CreateResponse(HttpStatusCode.BadRequest);
            bad.WriteString("missing slack payload");
            return bad;
        }

        JsonDocument payloadDoc;
        try
        {
            payloadDoc = JsonDocument.Parse(payloadRaw);
        }
        catch (JsonException)
        {
            var bad = req.CreateResponse(HttpStatusCode.BadRequest);
            bad.WriteString("invalid slack payload");
            return bad;
        }

        using (payloadDoc)
        {
            if (!payloadDoc.RootElement.TryGetProperty("actions", out var actions) || actions.ValueKind != JsonValueKind.Array || actions.GetArrayLength() == 0)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                bad.WriteString("missing slack action");
                return bad;
            }

            var action = actions[0];
            if (action.ValueKind != JsonValueKind.Object)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                bad.WriteString("invalid slack action");
                return bad;
            }

            var actionId = action.TryGetProperty("action_id", out var actionIdEl) ? (actionIdEl.GetString() ?? "") : "";
            if (!ActionDecisionMap.TryGetValue(actionId, out var decision))
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                bad.WriteString("unsupported slack action");
                return bad;
            }

            var investigationId = action.TryGetProperty("value", out var valueEl) ? (valueEl.GetString() ?? "") : "";
            if (string.IsNullOrWhiteSpace(investigationId))
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                bad.WriteString("missing investigation id");
                return bad;
            }

            var decidedBy = ExtractUserIdentifier(payloadDoc.RootElement);
            var record = new ApprovalRecord(
                InvestigationId: investigationId,
                Decision: decision,
                DecidedBy: decidedBy,
                DecidedAt: DateTimeOffset.UtcNow,
                Reason: decision == ApprovalDecision.Investigate ? "Requested additional investigation" : null);

            _state.ApprovalRecords[investigationId] = record;
            _logger.LogInformation("slack_approval_recorded: {investigationId} {decision} {decidedBy}", investigationId, decision, decidedBy);

            var responseText = $"Recorded *{decision.ToString().ToLowerInvariant()}* decision for investigation `{investigationId}`.";
            if (decision == ApprovalDecision.Approve)
            {
                responseText = $"{responseText} Remediation execution has been queued.";
            }

            var res = req.CreateResponse(HttpStatusCode.OK);
            await res.WriteAsJsonAsync(new { text = responseText });
            return res;
        }
    }

    private static string ExtractUserIdentifier(JsonElement payload)
    {
        if (payload.TryGetProperty("user", out var user) && user.ValueKind == JsonValueKind.Object)
        {
            foreach (var key in new[] { "username", "name", "id" })
            {
                if (user.TryGetProperty(key, out var val) && val.ValueKind == JsonValueKind.String)
                {
                    var str = val.GetString();
                    if (!string.IsNullOrWhiteSpace(str))
                    {
                        return str;
                    }
                }
            }
        }

        return "unknown-user";
    }
}
