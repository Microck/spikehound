using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using NSec.Cryptography;

namespace IncidentWarRoom.Core.Security;

public static class DiscordSignatureVerifier
{
    public const int MaxAgeSeconds = 60 * 5;

    public static bool Verify(
        ReadOnlySpan<byte> rawBody,
        IReadOnlyDictionary<string, string> headers,
        string publicKeyHex,
        long nowEpochSeconds,
        int maxAgeSeconds = MaxAgeSeconds)
    {
        if (string.IsNullOrWhiteSpace(publicKeyHex))
        {
            return false;
        }

        if (!HeaderUtils.TryGetValue(headers, "X-Signature-Timestamp", out var timestamp) ||
            !HeaderUtils.TryGetValue(headers, "X-Signature-Ed25519", out var signatureHex))
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

        if (!Hex.TryDecode(publicKeyHex, out var publicKeyBytes) || publicKeyBytes.Length != 32)
        {
            return false;
        }

        if (!Hex.TryDecode(signatureHex, out var signatureBytes) || signatureBytes.Length != 64)
        {
            return false;
        }

        var algorithm = SignatureAlgorithm.Ed25519;
        PublicKey publicKey;
        try
        {
            publicKey = PublicKey.Import(algorithm, publicKeyBytes, KeyBlobFormat.RawPublicKey);
        }
        catch (CryptographicException)
        {
            return false;
        }

        var timestampBytes = Encoding.UTF8.GetBytes(timestamp);
        var signedPayload = new byte[timestampBytes.Length + rawBody.Length];
        Buffer.BlockCopy(timestampBytes, 0, signedPayload, 0, timestampBytes.Length);
        rawBody.CopyTo(signedPayload.AsSpan(timestampBytes.Length));

        return algorithm.Verify(publicKey, signedPayload, signatureBytes);
    }
}
