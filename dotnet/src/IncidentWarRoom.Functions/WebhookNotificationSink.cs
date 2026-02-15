using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading;
using System.Threading.Tasks;
using IncidentWarRoom.Core.Models;
using IncidentWarRoom.Core.Orchestration;
using Microsoft.Extensions.Logging;

namespace IncidentWarRoom.Functions;

public sealed class WebhookNotificationSink : INotificationSink
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<WebhookNotificationSink> _logger;

    public WebhookNotificationSink(IHttpClientFactory httpClientFactory, ILogger<WebhookNotificationSink> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    public async Task NotifyAsync(InvestigationReport report, CancellationToken cancellationToken)
    {
        await NotifySlackAsync(report, cancellationToken);
        await NotifyDiscordAsync(report, cancellationToken);
    }

    private async Task NotifySlackAsync(InvestigationReport report, CancellationToken cancellationToken)
    {
        var url = Environment.GetEnvironmentVariable("SLACK_WEBHOOK_URL");
        if (string.IsNullOrWhiteSpace(url))
        {
            return;
        }

        var payload = new
        {
            text = $"Investigation `{report.UnifiedFindings.AlertId}` completed. Remediation: {report.RemediationResult.Data?.Summary ?? "none"}."
        };

        try
        {
            var client = _httpClientFactory.CreateClient();
            using var resp = await client.PostAsJsonAsync(url, payload, cancellationToken);
            resp.EnsureSuccessStatusCode();
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "slack_notification_failed");
        }
    }

    private async Task NotifyDiscordAsync(InvestigationReport report, CancellationToken cancellationToken)
    {
        var url = Environment.GetEnvironmentVariable("DISCORD_WEBHOOK_URL");
        if (string.IsNullOrWhiteSpace(url))
        {
            return;
        }

        var payload = new
        {
            content = $"Investigation `{report.UnifiedFindings.AlertId}` completed. Remediation: {report.RemediationResult.Data?.Summary ?? "none"}.",
            allowed_mentions = new { parse = Array.Empty<string>() },
        };

        try
        {
            var client = _httpClientFactory.CreateClient();
            using var resp = await client.PostAsJsonAsync(url, payload, cancellationToken);
            resp.EnsureSuccessStatusCode();
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "discord_notification_failed");
        }
    }
}
