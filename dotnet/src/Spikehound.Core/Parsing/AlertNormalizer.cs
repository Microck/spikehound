using System;
using System.Collections.Generic;
using System.Text.Json;

namespace Spikehound.Core.Parsing;

public sealed record NormalizedAlert(
    string AlertId,
    string RuleName,
    string Severity,
    string FiredDateTime,
    string Summary,
    string? ResourceId
);

public static class AlertNormalizer
{
    public static NormalizedAlert Normalize(JsonElement payload)
    {
        var alertId = FirstNonEmptyString(
            GetString(payload, "alert_id"),
            GetString(payload, "id"),
            GetString(payload, "data", "essentials", "alertId"),
            GetString(payload, "data", "essentials", "originAlertId")
        );

        var ruleName = FirstNonEmptyString(
            GetString(payload, "rule_name"),
            GetString(payload, "ruleName"),
            GetString(payload, "data", "essentials", "alertRule"),
            GetString(payload, "summary"),
            GetString(payload, "title")
        );

        var severity = FirstNonEmptyString(
            GetString(payload, "severity"),
            GetString(payload, "data", "essentials", "severity"),
            GetString(payload, "data", "alertContext", "severity")
        );

        var firedDateTime = FirstNonEmptyString(
            GetString(payload, "fired_date_time"),
            GetString(payload, "firedDateTime"),
            GetString(payload, "data", "essentials", "firedDateTime"),
            GetString(payload, "timestamp")
        );

        var resourceId = FirstNonEmptyString(
            GetString(payload, "resource_id"),
            GetString(payload, "resourceId"),
            FirstStringFromArray(payload, "data", "essentials", "alertTargetIDs"),
            GetString(payload, "data", "alertContext", "resourceId"),
            ScanResourceId(payload)
        );

        return new NormalizedAlert(
            AlertId: alertId ?? "unknown-alert",
            RuleName: ruleName ?? "unknown-rule",
            Severity: severity ?? "unknown",
            FiredDateTime: firedDateTime ?? DateTimeOffset.UtcNow.ToString("O"),
            Summary: ruleName ?? "Alert received",
            ResourceId: resourceId
        );
    }

    private static string? GetString(JsonElement root, params string[] path)
    {
        var current = root;
        foreach (var segment in path)
        {
            if (current.ValueKind != JsonValueKind.Object)
            {
                return null;
            }

            if (!current.TryGetProperty(segment, out var child))
            {
                return null;
            }

            current = child;
        }

        return current.ValueKind == JsonValueKind.String ? current.GetString() : null;
    }

    private static string? FirstStringFromArray(JsonElement root, params string[] path)
    {
        var current = root;
        foreach (var segment in path)
        {
            if (current.ValueKind != JsonValueKind.Object)
            {
                return null;
            }

            if (!current.TryGetProperty(segment, out var child))
            {
                return null;
            }

            current = child;
        }

        if (current.ValueKind != JsonValueKind.Array)
        {
            return null;
        }

        foreach (var item in current.EnumerateArray())
        {
            if (item.ValueKind == JsonValueKind.String)
            {
                var value = item.GetString();
                if (!string.IsNullOrWhiteSpace(value))
                {
                    return value;
                }
            }
        }

        return null;
    }

    private static string? FirstNonEmptyString(params string?[] values)
    {
        foreach (var value in values)
        {
            if (!string.IsNullOrWhiteSpace(value))
            {
                return value.Trim();
            }
        }

        return null;
    }

    private static string? ScanResourceId(JsonElement payload)
    {
        var candidates = new List<string>();
        CollectResourceIdCandidates(payload, candidates);
        foreach (var candidate in candidates)
        {
            if (!string.IsNullOrWhiteSpace(candidate))
            {
                return candidate.Trim();
            }
        }

        return null;
    }

    private static void CollectResourceIdCandidates(JsonElement value, List<string> candidates)
    {
        if (value.ValueKind == JsonValueKind.Object)
        {
            foreach (var property in value.EnumerateObject())
            {
                var lowered = property.Name.ToLowerInvariant();
                var child = property.Value;

                if ((lowered == "resource_id" || lowered == "resourceid" || lowered == "resourceuri") && child.ValueKind == JsonValueKind.String)
                {
                    candidates.Add(child.GetString() ?? "");
                }
                else if (lowered == "id" && child.ValueKind == JsonValueKind.String)
                {
                    var idValue = child.GetString() ?? "";
                    if (idValue.StartsWith("/subscriptions/", StringComparison.OrdinalIgnoreCase))
                    {
                        candidates.Add(idValue);
                    }
                }

                if (child.ValueKind == JsonValueKind.Object || child.ValueKind == JsonValueKind.Array)
                {
                    CollectResourceIdCandidates(child, candidates);
                }
            }

            return;
        }

        if (value.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in value.EnumerateArray())
            {
                CollectResourceIdCandidates(item, candidates);
            }
        }
    }
}
