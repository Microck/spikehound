using System;
using System.Collections.Generic;

namespace IncidentWarRoom.Core.Security;

public static class HeaderUtils
{
    public static bool TryGetValue(IReadOnlyDictionary<string, string> headers, string name, out string value)
    {
        if (headers.TryGetValue(name, out value!))
        {
            if (!string.IsNullOrEmpty(value))
            {
                return true;
            }
        }

        var lowered = name.ToLowerInvariant();
        foreach (var pair in headers)
        {
            if (pair.Key.ToLowerInvariant() == lowered && !string.IsNullOrEmpty(pair.Value))
            {
                value = pair.Value;
                return true;
            }
        }

        value = string.Empty;
        return false;
    }
}
