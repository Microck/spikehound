using System;
using System.Text.Json;
using Spikehound.Core.Parsing;
using Xunit;

namespace Spikehound.Core.Tests;

public sealed class AlertNormalizerTests
{
    [Fact]
    public void Normalize_UsesDirectFields_WhenPresent()
    {
        using var doc = JsonDocument.Parse(
            "{\"alert_id\":\"a1\",\"rule_name\":\"r1\",\"severity\":\"sev\",\"fired_date_time\":\"t\",\"resource_id\":\"/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1\"}"
        );

        var normalized = AlertNormalizer.Normalize(doc.RootElement);

        Assert.Equal("a1", normalized.AlertId);
        Assert.Equal("r1", normalized.RuleName);
        Assert.Equal("sev", normalized.Severity);
        Assert.Equal("t", normalized.FiredDateTime);
        Assert.Equal("r1", normalized.Summary);
        Assert.Equal("/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1", normalized.ResourceId);
    }

    [Fact]
    public void Normalize_ScansForResourceId_WhenNotProvidedDirectly()
    {
        var body = "{" +
                   "\"data\":{\"essentials\":{\"alertId\":\"azure-alert-1\"}}," +
                   "\"something\":{\"nested\":[{\"id\":\"/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm2\"}]}" +
                   "}";

        using var doc = JsonDocument.Parse(body);
        var normalized = AlertNormalizer.Normalize(doc.RootElement);

        Assert.Equal("azure-alert-1", normalized.AlertId);
        Assert.Equal("/subscriptions/s1/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm2", normalized.ResourceId);
        Assert.False(string.IsNullOrWhiteSpace(normalized.RuleName));
    }

    [Fact]
    public void Normalize_FallsBackToDefaults_WhenMissing()
    {
        using var doc = JsonDocument.Parse("{}");

        var normalized = AlertNormalizer.Normalize(doc.RootElement);

        Assert.Equal("unknown-alert", normalized.AlertId);
        Assert.Equal("unknown-rule", normalized.RuleName);
        Assert.Equal("unknown", normalized.Severity);
        Assert.Equal("Alert received", normalized.Summary);
        Assert.True(DateTimeOffset.TryParse(normalized.FiredDateTime, out _));
    }
}
