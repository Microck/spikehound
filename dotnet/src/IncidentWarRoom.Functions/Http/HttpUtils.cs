using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker.Http;

namespace IncidentWarRoom.Functions.Http;

public static class HttpUtils
{
    public static async Task<byte[]> ReadBodyBytesAsync(HttpRequestData req)
    {
        using var ms = new MemoryStream();
        await req.Body.CopyToAsync(ms);
        return ms.ToArray();
    }

    public static Dictionary<string, string> HeadersToDictionary(HttpHeadersCollection headers)
    {
        var dict = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var pair in headers)
        {
            dict[pair.Key] = string.Join(",", pair.Value);
        }
        return dict;
    }

    public static Dictionary<string, string> ParseFormUrlEncoded(string body)
    {
        var values = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        if (string.IsNullOrEmpty(body))
        {
            return values;
        }

        foreach (var chunk in body.Split('&', StringSplitOptions.RemoveEmptyEntries))
        {
            var idx = chunk.IndexOf('=');
            if (idx <= 0)
            {
                continue;
            }

            var key = WebUtility.UrlDecode(chunk[..idx]);
            var value = WebUtility.UrlDecode(chunk[(idx + 1)..]);
            if (!string.IsNullOrEmpty(key))
            {
                values[key] = value;
            }
        }

        return values;
    }

    public static long NowEpochSeconds() => DateTimeOffset.UtcNow.ToUnixTimeSeconds();
}
