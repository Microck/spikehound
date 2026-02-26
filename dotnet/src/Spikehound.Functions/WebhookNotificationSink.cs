using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Core.Models;
using Spikehound.Core.Orchestration;
using Microsoft.Extensions.Logging;

namespace Spikehound.Functions;

public sealed class WebhookNotificationSink : INotificationSink
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly InMemoryState _state;
    private readonly ILogger<WebhookNotificationSink> _logger;

    public WebhookNotificationSink(
        IHttpClientFactory httpClientFactory,
        InMemoryState state,
        ILogger<WebhookNotificationSink> logger)
    {
        _httpClientFactory = httpClientFactory;
        _state = state;
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

        var payload = BuildSlackPayload(report);

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
        var botToken = Environment.GetEnvironmentVariable("DISCORD_BOT_TOKEN") ?? string.Empty;
        var channelId = Environment.GetEnvironmentVariable("DISCORD_CHANNEL_ID") ?? string.Empty;
        var webhookUrl = Environment.GetEnvironmentVariable("DISCORD_WEBHOOK_URL") ?? string.Empty;

        if (string.IsNullOrWhiteSpace(webhookUrl) &&
            (string.IsNullOrWhiteSpace(botToken) || string.IsNullOrWhiteSpace(channelId)))
        {
            return;
        }

        var payload = BuildDiscordPayload(report);
        try
        {
            if (!string.IsNullOrWhiteSpace(botToken) && !string.IsNullOrWhiteSpace(channelId))
            {
                await PostDiscordBotMessageAsync(channelId, botToken, payload, cancellationToken);
                return;
            }

            if (!string.IsNullOrWhiteSpace(webhookUrl))
            {
                await PostDiscordWebhookAsync(webhookUrl, payload, cancellationToken);
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "discord_notification_failed");
        }
    }

    private async Task PostDiscordWebhookAsync(string webhookUrl, object payload, CancellationToken cancellationToken)
    {
        var client = _httpClientFactory.CreateClient();
        var webhookWithComponents = AppendQueryParameter(webhookUrl, "with_components", "true");
        using var resp = await client.PostAsJsonAsync(webhookWithComponents, payload, cancellationToken);
        resp.EnsureSuccessStatusCode();
    }

    private async Task PostDiscordBotMessageAsync(string channelId, string botToken, object payload, CancellationToken cancellationToken)
    {
        var client = _httpClientFactory.CreateClient();
        using var request = new HttpRequestMessage(HttpMethod.Post, $"https://discord.com/api/v10/channels/{channelId}/messages")
        {
            Content = JsonContent.Create(payload),
        };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bot", botToken);

        using var resp = await client.SendAsync(request, cancellationToken);
        resp.EnsureSuccessStatusCode();
    }

    private object BuildSlackPayload(InvestigationReport report)
    {
        var alertId = report.UnifiedFindings.AlertId;
        var rootCause = report.DiagnosisResult.Data?.Hypothesis.Explanation
            ?? report.DiagnosisResult.Errors.FirstOrDefault()
            ?? "Diagnosis unavailable.";
        var confidenceText = report.DiagnosisResult.Data is null ? "n/a" : $"{report.DiagnosisResult.Data.Confidence}%";
        var topCost = report.UnifiedFindings.CostFindings
            .OrderByDescending(x => x.Cost)
            .FirstOrDefault();
        var topCostText = topCost is null
            ? "No explicit cost finding"
            : $"`{Truncate(topCost.ResourceId, 120)}` ({topCost.Cost:0.##} {topCost.Currency})";

        var firstAction = report.RemediationResult.Data?.Actions.FirstOrDefault();
        var firstActionText = firstAction is null
            ? "No remediation action available"
            : $"{firstAction.Type} on `{Truncate(firstAction.TargetResourceId, 120)}`";

        var blocks = new List<object>
        {
            new
            {
                type = "section",
                text = new { type = "mrkdwn", text = $"*Incident investigation complete*\nAlert: `{alertId}`" },
            },
            new
            {
                type = "section",
                fields = new object[]
                {
                    new { type = "mrkdwn", text = $"*Top cost driver*\n{topCostText}" },
                    new { type = "mrkdwn", text = $"*Confidence*\n{confidenceText}" },
                },
            },
            new
            {
                type = "section",
                text = new { type = "mrkdwn", text = $"*Root cause*\n{Truncate(rootCause, 400)}" },
            },
            new
            {
                type = "section",
                text = new { type = "mrkdwn", text = $"*First remediation action*\n{firstActionText}" },
            },
        };

        if (firstAction is not null)
        {
            blocks.Add(new
            {
                type = "actions",
                elements = new object[]
                {
                    new
                    {
                        type = "button",
                        text = new { type = "plain_text", text = "Approve", emoji = true },
                        style = "primary",
                        action_id = "approve_remediation",
                        value = alertId,
                    },
                    new
                    {
                        type = "button",
                        text = new { type = "plain_text", text = "Reject", emoji = true },
                        style = "danger",
                        action_id = "reject_remediation",
                        value = alertId,
                    },
                    new
                    {
                        type = "button",
                        text = new { type = "plain_text", text = "Investigate More", emoji = true },
                        action_id = "investigate_more",
                        value = alertId,
                    },
                },
            });
        }

        return new
        {
            text = $"Investigation `{alertId}` complete.",
            blocks,
        };
    }

    private object BuildDiscordPayload(InvestigationReport report)
    {
        var alertId = report.UnifiedFindings.AlertId;
        var rootCause = report.DiagnosisResult.Data?.Hypothesis.Explanation
            ?? report.DiagnosisResult.Errors.FirstOrDefault()
            ?? "Diagnosis unavailable.";
        var confidenceText = report.DiagnosisResult.Data is null ? "n/a" : $"{report.DiagnosisResult.Data.Confidence}%";

        var firstAction = report.RemediationResult.Data?.Actions.FirstOrDefault();
        var investigationToken = _state.RememberDiscordInvestigationToken(alertId);

        var contentLines = new List<string>
        {
            "Incident investigation complete",
            $"Alert: `{alertId}`",
            $"Confidence: {confidenceText}",
            $"Root cause: {Truncate(rootCause, 300)}",
        };

        if (firstAction is not null)
        {
            contentLines.Add($"First remediation action: {firstAction.Type} on `{Truncate(firstAction.TargetResourceId, 100)}`");
        }

        if (firstAction is null)
        {
            return new
            {
                content = string.Join("\n", contentLines),
                allowed_mentions = new { parse = Array.Empty<string>() },
            };
        }

        return new
        {
            content = string.Join("\n", contentLines),
            allowed_mentions = new { parse = Array.Empty<string>() },
            components = new object[]
            {
                new
                {
                    type = 1,
                    components = new object[]
                    {
                        new
                        {
                            type = 2,
                            style = 3,
                            custom_id = $"approve_remediation:{investigationToken}",
                            label = "Approve",
                        },
                        new
                        {
                            type = 2,
                            style = 4,
                            custom_id = $"reject_remediation:{investigationToken}",
                            label = "Reject",
                        },
                        new
                        {
                            type = 2,
                            style = 1,
                            custom_id = $"investigate_more:{investigationToken}",
                            label = "Investigate More",
                        },
                    },
                },
            },
        };
    }

    private static string Truncate(string value, int maxLength)
    {
        if (string.IsNullOrEmpty(value) || value.Length <= maxLength)
        {
            return value;
        }

        if (maxLength <= 3)
        {
            return value[..maxLength];
        }

        return value[..(maxLength - 3)] + "...";
    }

    private static string AppendQueryParameter(string url, string key, string value)
    {
        var marker = $"{key}=";
        if (url.Contains(marker, StringComparison.OrdinalIgnoreCase))
        {
            return url;
        }

        var separator = url.Contains('?', StringComparison.Ordinal) ? "&" : "?";
        return $"{url}{separator}{key}={Uri.EscapeDataString(value)}";
    }
}
