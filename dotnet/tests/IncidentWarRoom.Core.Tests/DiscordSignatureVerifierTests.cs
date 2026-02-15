using System.Collections.Generic;
using System.Text;
using IncidentWarRoom.Core.Security;
using NSec.Cryptography;
using Xunit;

namespace IncidentWarRoom.Core.Tests;

public sealed class DiscordSignatureVerifierTests
{
    private static (Key Key, string PublicKeyHex) CreateSigningKey()
    {
        var algorithm = SignatureAlgorithm.Ed25519;
        var key = Key.Create(algorithm, new KeyCreationParameters
        {
            ExportPolicy = KeyExportPolicies.AllowPlaintextExport,
        });

        var publicKey = key.PublicKey.Export(KeyBlobFormat.RawPublicKey);
        return (key, Hex.Encode(publicKey));
    }

    [Fact]
    public void Verify_AcceptsValidSignature()
    {
        var (key, publicKeyHex) = CreateSigningKey();
        using var _ = key;
        const long nowEpoch = 1_777_777_777;
        var timestamp = nowEpoch.ToString();
        var body = Encoding.UTF8.GetBytes("{\"type\":1}");

        var signedPayload = Encoding.UTF8.GetBytes(timestamp);
        var data = new byte[signedPayload.Length + body.Length];
        Buffer.BlockCopy(signedPayload, 0, data, 0, signedPayload.Length);
        Buffer.BlockCopy(body, 0, data, signedPayload.Length, body.Length);

        var signature = SignatureAlgorithm.Ed25519.Sign(key, data);

        var headers = new Dictionary<string, string>
        {
            ["X-Signature-Ed25519"] = Hex.Encode(signature),
            ["X-Signature-Timestamp"] = timestamp,
        };

        Assert.True(DiscordSignatureVerifier.Verify(body, headers, publicKeyHex, nowEpoch));
    }

    [Fact]
    public void Verify_RejectsInvalidSignature()
    {
        var (key, publicKeyHex) = CreateSigningKey();
        using var _ = key;
        const long nowEpoch = 1_777_777_777;
        var timestamp = nowEpoch.ToString();
        var body = Encoding.UTF8.GetBytes("{\"type\":1}");

        var headers = new Dictionary<string, string>
        {
            ["X-Signature-Ed25519"] = new string('0', 128),
            ["X-Signature-Timestamp"] = timestamp,
        };

        Assert.False(DiscordSignatureVerifier.Verify(body, headers, publicKeyHex, nowEpoch));
    }

    [Fact]
    public void Verify_RejectsStaleTimestamp()
    {
        var (key, publicKeyHex) = CreateSigningKey();
        using var _ = key;
        const long nowEpoch = 1_777_777_777;
        var staleTimestamp = (nowEpoch - 301).ToString();
        var body = Encoding.UTF8.GetBytes("{\"type\":1}");

        var signedPayload = Encoding.UTF8.GetBytes(staleTimestamp);
        var data = new byte[signedPayload.Length + body.Length];
        Buffer.BlockCopy(signedPayload, 0, data, 0, signedPayload.Length);
        Buffer.BlockCopy(body, 0, data, signedPayload.Length, body.Length);

        var signature = SignatureAlgorithm.Ed25519.Sign(key, data);

        var headers = new Dictionary<string, string>
        {
            ["X-Signature-Ed25519"] = Hex.Encode(signature),
            ["X-Signature-Timestamp"] = staleTimestamp,
        };

        Assert.False(DiscordSignatureVerifier.Verify(body, headers, publicKeyHex, nowEpoch));
    }
}
