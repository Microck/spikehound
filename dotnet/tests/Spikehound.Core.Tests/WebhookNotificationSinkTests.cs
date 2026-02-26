using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Core.Models;
using Spikehound.Functions;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace Spikehound.Core.Tests;

public sealed class WebhookNotificationSinkTests
{
    private sealed class RecordingHandler : HttpMessageHandler
    {
        public List<(HttpRequestMessage Request, string Body)> Requests { get; } = [];

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var body = request.Content is null
                ? string.Empty
                : await request.Content.ReadAsStringAsync(cancellationToken);

            Requests.Add((request, body));
            return new HttpResponseMessage(HttpStatusCode.OK);
        }
    }

    private sealed class StaticHttpClientFactory : IHttpClientFactory
    {
        private readonly HttpClient _client;

        public StaticHttpClientFactory(HttpClient client)
        {
            _client = client;
        }

        public HttpClient CreateClient(string name) => _client;
    }

    private sealed class EnvScope : IDisposable
    {
        private readonly Dictionary<string, string?> _previous = [];

        public EnvScope(params (string Name, string? Value)[] variables)
        {
            foreach (var (name, value) in variables)
            {
                _previous[name] = Environment.GetEnvironmentVariable(name);
                Environment.SetEnvironmentVariable(name, value);
            }
        }

        public void Dispose()
        {
            foreach (var (name, previousValue) in _previous)
            {
                Environment.SetEnvironmentVariable(name, previousValue);
            }
        }
    }

    [Fact]
    public async Task NotifyAsync_SendsSlackBlocksWithApprovalButtons()
    {
        using var env = new EnvScope(
            ("SLACK_WEBHOOK_URL", "https://hooks.slack.test/services/abc"),
            ("DISCORD_WEBHOOK_URL", null),
            ("DISCORD_BOT_TOKEN", null),
            ("DISCORD_CHANNEL_ID", null));

        var handler = new RecordingHandler();
        var client = new HttpClient(handler);
        var state = new InMemoryState();
        var sink = new WebhookNotificationSink(
            new StaticHttpClientFactory(client),
            state,
            NullLogger<WebhookNotificationSink>.Instance);

        await sink.NotifyAsync(CreateReport(), CancellationToken.None);

        var request = Assert.Single(handler.Requests);
        Assert.Equal("https://hooks.slack.test/services/abc", request.Request.RequestUri?.ToString());

        using var body = JsonDocument.Parse(request.Body);
        Assert.True(body.RootElement.TryGetProperty("blocks", out var blocks));
        Assert.Equal(JsonValueKind.Array, blocks.ValueKind);

        var actionBlock = blocks.EnumerateArray().FirstOrDefault(x =>
            x.TryGetProperty("type", out var typeEl) &&
            string.Equals(typeEl.GetString(), "actions", StringComparison.Ordinal));

        Assert.Equal(JsonValueKind.Object, actionBlock.ValueKind);
        Assert.True(actionBlock.TryGetProperty("elements", out var elements));
        Assert.Equal(JsonValueKind.Array, elements.ValueKind);

        var actionIds = elements.EnumerateArray()
            .Select(x => x.GetProperty("action_id").GetString())
            .ToArray();

        Assert.Equal(new[] { "approve_remediation", "reject_remediation", "investigate_more" }, actionIds);
    }

    [Fact]
    public async Task NotifyAsync_UsesDiscordBotModeWithResolvableTokenizedCustomIds()
    {
        using var env = new EnvScope(
            ("SLACK_WEBHOOK_URL", null),
            ("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/111/abc"),
            ("DISCORD_BOT_TOKEN", "discord-bot-token"),
            ("DISCORD_CHANNEL_ID", "123456789012345678"));

        var handler = new RecordingHandler();
        var client = new HttpClient(handler);
        var state = new InMemoryState();
        var sink = new WebhookNotificationSink(
            new StaticHttpClientFactory(client),
            state,
            NullLogger<WebhookNotificationSink>.Instance);

        var report = CreateReport();
        await sink.NotifyAsync(report, CancellationToken.None);

        var request = Assert.Single(handler.Requests);
        Assert.Equal(
            "https://discord.com/api/v10/channels/123456789012345678/messages",
            request.Request.RequestUri?.ToString());
        Assert.Equal("Bot", request.Request.Headers.Authorization?.Scheme);
        Assert.Equal("discord-bot-token", request.Request.Headers.Authorization?.Parameter);

        using var body = JsonDocument.Parse(request.Body);
        Assert.True(body.RootElement.TryGetProperty("components", out var components));
        var row = Assert.Single(components.EnumerateArray());
        var buttons = row.GetProperty("components").EnumerateArray().ToArray();
        Assert.Equal(3, buttons.Length);

        var approveCustomId = buttons[0].GetProperty("custom_id").GetString();
        Assert.NotNull(approveCustomId);
        Assert.StartsWith("approve_remediation:inv_", approveCustomId, StringComparison.Ordinal);
        Assert.DoesNotContain(report.UnifiedFindings.AlertId, approveCustomId!, StringComparison.Ordinal);

        var token = approveCustomId!["approve_remediation:".Length..];
        Assert.True(state.TryResolveDiscordInvestigationToken(token, out var resolvedInvestigationId));
        Assert.Equal(report.UnifiedFindings.AlertId, resolvedInvestigationId);
    }

    private static InvestigationReport CreateReport()
    {
        const string alertId = "/subscriptions/11111111-2222-3333-4444-555555555555/providers/Microsoft.AlertsManagement/alerts/demo-gpu-spike-001";
        var now = DateTimeOffset.UtcNow;

        var findings = new UnifiedFindings(
            AlertSummary: new Dictionary<string, object?>
            {
                ["alert_id"] = alertId,
                ["severity"] = "Sev1",
            },
            Results: new Dictionary<AgentName, AgentResult<object?>>(),
            AlertId: alertId,
            ReceivedAt: now,
            CostFindings:
            [
                new CostFinding(
                    ResourceId: "/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/spikehound-demo-rg/providers/Microsoft.Compute/virtualMachines/spikehound-gpu-vm",
                    Cost: 450,
                    Currency: "USD"),
            ],
            ResourceFindings: null,
            HistoryFindings: null,
            Notes: "test");

        var diagnosis = new Diagnosis(
            Hypothesis: new RootCauseHypothesis(
                Title: "VM left running",
                Explanation: "GPU VM remained running for 72 hours after training completed.",
                Evidence: ["cost spike", "no auto-shutdown"]),
            Confidence: 85,
            Alternatives: [],
            Risks: []);

        var plan = new RemediationPlan(
            Summary: "Stop and deallocate VM",
            Actions:
            [
                new RemediationAction(
                    Type: RemediationActionType.StopVm,
                    TargetResourceId: "/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/spikehound-demo-rg/providers/Microsoft.Compute/virtualMachines/spikehound-gpu-vm",
                    Parameters: new Dictionary<string, object?>(),
                    RiskLevel: RemediationRiskLevel.High),
            ],
            RollbackNotes: "Start VM if needed");

        return new InvestigationReport(
            UnifiedFindings: findings,
            DiagnosisResult: AgentResult<Diagnosis>.Ok(AgentName.Diagnosis, now, now, diagnosis),
            RemediationResult: AgentResult<RemediationPlan>.Ok(AgentName.Remediation, now, now, plan));
    }
}
