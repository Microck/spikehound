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

public sealed class SlackActionsFunction
{
    private static readonly IReadOnlyDictionary<string, ApprovalDecision> ActionDecisionMap = new Dictionary<string, ApprovalDecision>(StringComparer.Ordinal)
    {
        ["approve_remediation"] = ApprovalDecision.Approve,
        ["reject_remediation"] = ApprovalDecision.Reject,
        ["investigate_more"] = ApprovalDecision.Investigate,
    };

    private readonly InMemoryState _state;
    private readonly ApprovalRemediationWorkflow _approvalWorkflow;
    private readonly ILogger<SlackActionsFunction> _logger;

    public SlackActionsFunction(
        InMemoryState state,
        ApprovalRemediationWorkflow approvalWorkflow,
        ILogger<SlackActionsFunction> logger)
    {
        _state = state;
        _approvalWorkflow = approvalWorkflow;
        _logger = logger;
    }

    [Function("webhooks_slack_actions")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/slack/actions")] HttpRequestData req,
        [DurableClient] DurableTaskClient durableClient)
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
            await HttpUtils.WritePlainTextAsync(bad, "missing slack payload");
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
            await HttpUtils.WritePlainTextAsync(bad, "invalid slack payload");
            return bad;
        }

        using (payloadDoc)
        {
            if (!payloadDoc.RootElement.TryGetProperty("actions", out var actions) || actions.ValueKind != JsonValueKind.Array || actions.GetArrayLength() == 0)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "missing slack action");
                return bad;
            }

            var action = actions[0];
            if (action.ValueKind != JsonValueKind.Object)
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "invalid slack action");
                return bad;
            }

            var actionId = action.TryGetProperty("action_id", out var actionIdEl) ? (actionIdEl.GetString() ?? "") : "";
            if (!ActionDecisionMap.TryGetValue(actionId, out var decision))
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "unsupported slack action");
                return bad;
            }

            var investigationId = action.TryGetProperty("value", out var valueEl) ? (valueEl.GetString() ?? "") : "";
            if (string.IsNullOrWhiteSpace(investigationId))
            {
                var bad = req.CreateResponse(HttpStatusCode.BadRequest);
                await HttpUtils.WritePlainTextAsync(bad, "missing investigation id");
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
                var queueResult = await _approvalWorkflow.QueueApprovedExecutionAsync(
                    investigationId,
                    record,
                    source: "slack",
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
