using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using IncidentWarRoom.Core.Security;
using Xunit;

namespace IncidentWarRoom.Core.Tests;

public sealed class SlackSignatureVerifierTests
{
    private static string Sign(string secret, string timestamp, string rawBody)
    {
        var payload = Encoding.UTF8.GetBytes($"v0:{timestamp}:{rawBody}");
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(secret));
        var digest = hmac.ComputeHash(payload);
        return "v0=" + Hex.Encode(digest);
    }

    [Fact]
    public void Verify_AcceptsValidSignature()
    {
        const string secret = "test-signing-secret";
        const string rawBody = "payload=%7B%22type%22%3A%22block_actions%22%7D";
        const long nowEpoch = 1_777_777_777;
        var timestamp = nowEpoch.ToString();

        var headers = new Dictionary<string, string>
        {
            ["X-Slack-Request-Timestamp"] = timestamp,
            ["X-Slack-Signature"] = Sign(secret, timestamp, rawBody),
        };

        Assert.True(
            SlackSignatureVerifier.Verify(
                Encoding.UTF8.GetBytes(rawBody),
                headers,
                signingSecret: secret,
                nowEpochSeconds: nowEpoch));
    }

    [Fact]
    public void Verify_RejectsInvalidSignature()
    {
        const string secret = "test-signing-secret";
        const string rawBody = "payload=%7B%22type%22%3A%22block_actions%22%7D";
        const long nowEpoch = 1_777_777_777;
        var timestamp = nowEpoch.ToString();

        var headers = new Dictionary<string, string>
        {
            ["X-Slack-Request-Timestamp"] = timestamp,
            ["X-Slack-Signature"] = "v0=invalid",
        };

        Assert.False(
            SlackSignatureVerifier.Verify(
                Encoding.UTF8.GetBytes(rawBody),
                headers,
                signingSecret: secret,
                nowEpochSeconds: nowEpoch));
    }

    [Fact]
    public void Verify_RejectsStaleTimestamp()
    {
        const string secret = "test-signing-secret";
        const string rawBody = "payload=%7B%22type%22%3A%22block_actions%22%7D";
        const long nowEpoch = 1_777_777_777;
        var staleTimestamp = (nowEpoch - 301).ToString();

        var headers = new Dictionary<string, string>
        {
            ["X-Slack-Request-Timestamp"] = staleTimestamp,
            ["X-Slack-Signature"] = Sign(secret, staleTimestamp, rawBody),
        };

        Assert.False(
            SlackSignatureVerifier.Verify(
                Encoding.UTF8.GetBytes(rawBody),
                headers,
                signingSecret: secret,
                nowEpochSeconds: nowEpoch));
    }
}
