using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;

namespace IncidentWarRoom.Core.Security;

public static class SlackSignatureVerifier
{
    public static bool Verify(
        ReadOnlySpan<byte> rawBody,
        IReadOnlyDictionary<string, string> headers,
        string signingSecret,
        long nowEpochSeconds,
        int maxAgeSeconds = 60 * 5)
    {
        if (string.IsNullOrWhiteSpace(signingSecret))
        {
            return false;
        }

        if (!HeaderUtils.TryGetValue(headers, "X-Slack-Request-Timestamp", out var timestamp) ||
            !HeaderUtils.TryGetValue(headers, "X-Slack-Signature", out var signature))
        {
            return false;
        }

        if (!long.TryParse(timestamp, out var timestampInt))
        {
            return false;
        }

        if (Math.Abs(nowEpochSeconds - timestampInt) > maxAgeSeconds)
        {
            return false;
        }

        var bodyText = Encoding.UTF8.GetString(rawBody);
        var signedPayload = Encoding.UTF8.GetBytes($"v0:{timestamp}:{bodyText}");

        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(signingSecret));
        var digest = hmac.ComputeHash(signedPayload);
        var computedSignature = "v0=" + Hex.Encode(digest);

        // Constant-time compare.
        var computedBytes = Encoding.ASCII.GetBytes(computedSignature);
        var signatureBytes = Encoding.ASCII.GetBytes(signature);
        if (computedBytes.Length != signatureBytes.Length)
        {
            return false;
        }

        return CryptographicOperations.FixedTimeEquals(computedBytes, signatureBytes);
    }
}
