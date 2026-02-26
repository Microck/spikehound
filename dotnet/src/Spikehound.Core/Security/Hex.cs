using System;

namespace Spikehound.Core.Security;

public static class Hex
{
    public static bool TryDecode(string hex, out byte[] bytes)
    {
        bytes = Array.Empty<byte>();
        if (string.IsNullOrWhiteSpace(hex))
        {
            return false;
        }

        if (hex.Length % 2 != 0)
        {
            return false;
        }

        try
        {
            bytes = Convert.FromHexString(hex);
            return true;
        }
        catch (FormatException)
        {
            return false;
        }
    }

    public static string Encode(byte[] bytes) => Convert.ToHexString(bytes).ToLowerInvariant();
}
