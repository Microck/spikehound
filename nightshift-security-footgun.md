# Spikehound Security Foot-Gun Analysis

**Generated:** 2026-04-02  
**Scope:** Full codebase — 33 C# source files, 3 csproj files, CI/CD config  
**Status:** Automated static analysis

---

## Executive Summary

The Spikehound codebase demonstrates **generally strong security hygiene** in its webhook signature verification (constant-time HMAC comparison, Ed25519 for Discord, timestamp replay protection). However, the analysis identified **9 security findings** ranging from P0 (Critical) to P3 (Low). The most severe issues are an **unauthenticated alert webhook endpoint** that allows arbitrary alert injection, and **predictable Discord investigation tokens** that could enable approval forgery.

---

## Findings Summary

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 1 | **P0** | `AlertWebhookFunction.cs` | 29–31 | Alert webhook endpoint has **no authentication** — anyone can inject fake cost alerts |
| 2 | **P1** | `InMemoryState.cs` | 76–84 | Discord investigation tokens are **deterministic SHA-256 hashes** (no secret/randomness) — predictable without server access |
| 3 | **P1** | `InMemoryState.cs` | 66–74 | Discord investigation tokens **never expire** — old tokens remain valid indefinitely |
| 4 | **P1** | `AlertWebhookFunction.cs` | 29–31 | `AuthorizationLevel.Anonymous` on alert endpoint bypasses Azure Functions host-level auth |
| 5 | **P2** | `SlackSignatureVerifier.cs` | 48–51 | Signature length mismatch returns `false` before constant-time compare — **minor timing leak** on length |
| 6 | **P2** | `WebhookNotificationSink.cs` | 91–97, `ApprovalRemediationWorkflow.cs` 286–295 | Outgoing webhook URLs from environment variables **not validated** — potential SSRF if env var is compromised |
| 7 | **P2** | `HttpUtils.cs` | 30–55 | Custom URL-encoded form parser doesn't handle `+` as space (only `%2B`) — may cause body parse mismatch with Slack signature |
| 8 | **P3** | `HttpUtils.cs` | 13–18 | Request body read into `MemoryStream` with **no size limit** — potential OOM / DoS |
| 9 | **P3** | `Spikehound.Functions.csproj` | 13–22 | Several NuGet packages may have known advisories (see Dependencies section) |

---

## Detailed Findings

### Finding 1 — P0 (Critical): Alert Webhook Endpoint Has No Authentication

- **File:** `dotnet/src/Spikehound.Functions/Functions/AlertWebhookFunction.cs`, line 30
- **Category:** Insecure HTTP endpoint / Missing auth

```csharp
[HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/alert")]
```

**Description:**  
The `/api/webhooks/alert` endpoint accepts POST requests from **any unauthenticated caller**. There is no signature verification, API key check, or any authentication mechanism. Any party with network access can inject arbitrary cost alert payloads, which then flow through the entire investigation → diagnosis → remediation pipeline. If `SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION=true` is set, an attacker who also triggers an approval via Slack/Discord (or if the approval flow is bypassed) could cause **actual Azure VM deallocation**.

This is the entry point for the most dangerous workflow in the system and it has zero inbound authentication.

**Recommendation:**
1. Add HMAC-based signature verification (e.g., a shared secret between Azure Monitor and the function) or require `AuthorizationLevel.Function` / `AuthorizationLevel.Admin`.
2. If Azure Monitor can't send signatures, validate the caller's IP against Azure Monitor's known IP ranges, or place the function behind API Management with a subscription key.
3. At minimum, add an `AuthorizationLevel.Function` key requirement so only callers with the function key can invoke it.

---

### Finding 2 — P1 (High): Predictable Discord Investigation Tokens

- **File:** `dotnet/src/Spikehound.Functions/InMemoryState.cs`, lines 76–84
- **Category:** Cryptographic weakness

```csharp
private static string CreateDiscordInvestigationToken(string investigationId)
{
    var bytes = Encoding.UTF8.GetBytes(investigationId);
    var hash = SHA256.HashData(bytes);
    var token = Convert.ToBase64String(hash)
        .TrimEnd('=')
        .Replace('+', '-')
        .Replace('/', '_');
    return $"{DiscordTokenPrefix}{token}";
}
```

**Description:**  
The Discord investigation token is a deterministic SHA-256 hash of the `investigationId` (which is the `alertId` from the alert payload). Since the `alertId` is:
1. Often predictable or publicly visible in Azure alert data
2. Returned in the alert webhook response (line 79 of `AlertWebhookFunction.cs`)
3. Included in Slack notification payloads (line 172 of `WebhookNotificationSink.cs` — the `value` field of buttons)

An attacker who knows the `investigationId` can **compute the token locally** without any server access. This token is what Discord interaction buttons use to reference investigations. If an attacker can forge a Discord interaction callback (e.g., via a compromised Discord bot token or API abuse), they can approve arbitrary remediation actions.

**Recommendation:**
1. Use `RandomNumberGenerator` to generate cryptographically random tokens instead of a deterministic hash.
2. Store the mapping in `DiscordInvestigationTokens` as currently done, but generate the token as: `inv_{Base64Url(RandomNumberGenerator.GetBytes(32))}`.

---

### Finding 3 — P1 (High): Discord Investigation Tokens Never Expire

- **File:** `dotnet/src/Spikehound.Functions/InMemoryState.cs`, lines 66–74
- **Category:** Missing security control

```csharp
public string RememberDiscordInvestigationToken(string investigationId)
{
    var token = CreateDiscordInvestigationToken(investigationId);
    DiscordInvestigationTokens[token] = investigationId;
    return token;
}
```

**Description:**  
Tokens stored in `DiscordInvestigationTokens` (`ConcurrentDictionary<string, string>`) are never removed or expired. While `_processed` reports are pruned by `PruneExpired()`, the Discord token dictionary grows without bound and tokens remain valid for the lifetime of the process. An old token for a resolved investigation could be replayed.

**Recommendation:**
1. Add a timestamp to the stored token entries and reject tokens older than a configurable TTL (e.g., 24 hours).
2. Alternatively, prune the `DiscordInvestigationTokens` dictionary alongside `_processed` in `PruneExpired()`.

---

### Finding 4 — P1 (High): Azure Functions AuthorizationLevel.Anonymous on All Endpoints

- **File:** Multiple function files
  - `AlertWebhookFunction.cs`, line 30
  - `SlackActionsFunction.cs`, line 43
  - `DiscordInteractionsFunction.cs`, line 43
  - `HealthFunction.cs`, line 12
- **Category:** Insecure HTTP endpoints

```csharp
[HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/slack/actions")]
[HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/discord/interactions")]
[HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/alert")]
[HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "health")]
```

**Description:**  
All four HTTP endpoints use `AuthorizationLevel.Anonymous`, which means Azure Functions host-level authentication (function keys, admin keys) is completely disabled. The Slack and Discord endpoints rely on application-level signature verification, which is acceptable. However:
- The **alert endpoint** has no application-level verification at all (see Finding 1).
- The **health endpoint** exposing operational status to the world is a minor information disclosure.
- Using `Anonymous` means the function keys feature of Azure Functions is unusable as a defense-in-depth layer.

**Recommendation:**
1. Alert endpoint: Use `AuthorizationLevel.Function` at minimum. If Azure Monitor can't send keys, consider IP allowlisting.
2. Health endpoint: Acceptable as `Anonymous` for probes, but consider returning less information.
3. Slack/Discord endpoints: `Anonymous` is acceptable since they implement their own cryptographic signature verification.

---

### Finding 5 — P2 (Medium): Timing Leak on Signature Length Mismatch (Slack)

- **File:** `dotnet/src/Spikehound.Core/Security/SlackSignatureVerifier.cs`, lines 48–51
- **Category:** Webhook signature verification / Timing attack

```csharp
var computedBytes = Encoding.ASCII.GetBytes(computedSignature);
var signatureBytes = Encoding.ASCII.GetBytes(signature);
if (computedBytes.Length != signatureBytes.Length)
{
    return false;  // ← Early return before constant-time comparison
}
return CryptographicOperations.FixedTimeEquals(computedBytes, signatureBytes);
```

**Description:**  
When the computed and provided signatures have different lengths, the method returns `false` immediately without entering the constant-time comparison. A remote attacker can potentially distinguish between "wrong length" and "right length but wrong content" responses, which leaks information about the expected signature length.

In practice, Slack signatures always have the format `v0=` + 64 hex chars = 67 bytes, so an attacker already knows the expected length. This is therefore a **low-risk theoretical issue** rather than a practical attack vector.

**Recommendation:**  
This is acceptable in practice since the signature format is fixed and publicly documented. If you want to be pedantic, pad both sides to a fixed length before comparing, or always run the comparison even if lengths differ (returning a pre-computed `false` result).

---

### Finding 6 — P2 (Medium): Outgoing Webhook URLs Not Validated (SSRF Risk)

- **Files:**
  - `dotnet/src/Spikehound.Functions/WebhookNotificationSink.cs`, lines 39, 63, 94
  - `dotnet/src/Spikehound.Functions/Remediation/ApprovalRemediationWorkflow.cs`, lines 171, 185, 229
- **Category:** SSRF / Insecure outbound requests

```csharp
var url = Environment.GetEnvironmentVariable("SLACK_WEBHOOK_URL");
// ... directly used in:
var resp = await client.PostAsJsonAsync(url, payload, cancellationToken);
```

**Description:**  
Webhook URLs (`SLACK_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL`) and the Discord channel API URL are read from environment variables and used directly in HTTP requests without validation. If an attacker can modify environment variables (e.g., via a compromised CI/CD pipeline, container escape, or Azure Function app setting misconfiguration), they could redirect outbound requests to an internal service (SSRF) or an attacker-controlled server to exfiltrate investigation reports containing Azure resource IDs, cost data, and diagnostic information.

**Recommendation:**
1. Validate that webhook URLs start with `https://hooks.slack.com/` and `https://discord.com/api/` respectively.
2. Consider using `SocketsHttpHandler` with configured `ConnectCallback` or a custom `HttpMessageHandler` that restricts outbound connections to allowed hosts.

---

### Finding 7 — P2 (Medium): Custom Form Parser May Break Slack Signature Verification

- **File:** `dotnet/src/Spikehound.Functions/Http/HttpUtils.cs`, lines 30–55
- **Category:** Webhook signature verification bypass

```csharp
public static Dictionary<string, string> ParseFormUrlEncoded(string body)
{
    // ...
    var key = WebUtility.UrlDecode(chunk[..idx]);
    var value = WebUtility.UrlDecode(chunk[(idx + 1)..]);
    // ...
}
```

**Description:**  
The custom form parser uses `WebUtility.UrlDecode` which decodes percent-encoded characters but **does not treat `+` as space**. The standard `application/x-www-form-urlencoded` format specifies that `+` represents a space character. If Slack ever sends a payload containing literal `+` characters (which `Uri.EscapeDataString` in their SDK produces as `%2B`), the parse output would differ from what Slack's signing algorithm expects.

More critically: the signature verification on line 50 of `SlackActionsFunction.cs` operates on `bodyBytes` (the raw body), while the form parsing on line 56 operates on the UTF-8 decoded string. If there's any discrepancy in encoding between what Slack signed and what the server receives (e.g., due to a reverse proxy normalizing URLs), the signature check could fail or — in edge cases — be bypassed if the parsed payload differs from what was signed.

**Recommendation:**  
1. Replace the custom parser with `System.Web.HttpUtility.ParseQueryString()` or `Microsoft.AspNetCore.WebUtilities.QueryHelpers.ParseQuery()` which correctly handle `+` as space.
2. Ensure the raw body bytes used for signature verification are **never modified** before verification (which is currently correctly handled — the raw `bodyBytes` are verified before parsing).

---

### Finding 8 — P3 (Low): Unbounded Request Body Read (DoS)

- **File:** `dotnet/src/Spikehound.Functions/Http/HttpUtils.cs`, lines 13–18
- **Category:** Denial of Service

```csharp
public static async Task<byte[]> ReadBodyBytesAsync(HttpRequestData req)
{
    using var ms = new MemoryStream();
    await req.Body.CopyToAsync(ms);
    return ms.ToArray();
}
```

**Description:**  
The request body is read into a `MemoryStream` with no size limit. An attacker could send an extremely large POST body (multiple GB) to exhaust server memory. This affects all three webhook endpoints.

Azure Functions does impose a default request body size limit (~100MB for the consumption plan), so this is mitigated at the infrastructure level. However, for defense-in-depth, the application should enforce its own reasonable limit.

**Recommendation:**  
Add a size check during the read:
```csharp
public static async Task<byte[]> ReadBodyBytesAsync(HttpRequestData req, int maxBytes = 1_048_576)
{
    using var ms = new MemoryStream();
    await req.Body.CopyToAsync(ms);
    if (ms.Length > maxBytes)
        throw new InvalidOperationException($"Request body exceeds {maxBytes} bytes.");
    return ms.ToArray();
}
```

---

### Finding 9 — P3 (Low): Dependency Version Review

- **Files:**
  - `dotnet/src/Spikehound.Functions/Spikehound.Functions.csproj`
  - `dotnet/src/Spikehound.Core/Spikehound.Core.csproj`
  - `dotnet/tests/Spikehound.Core.Tests/Spikehound.Core.Tests.csproj`
- **Category:** Dependency vulnerabilities

| Package | Version | Notes |
|---------|---------|-------|
| `NSec.Cryptography` | 25.4.0 | Current — no known critical CVEs |
| `Azure.Identity` | 1.17.1 | Current — check for MSAL-related advisories |
| `Azure.ResourceManager` | 1.13.2 | Current |
| `Azure.ResourceManager.Compute` | 1.14.0 | Current |
| `Microsoft.ApplicationInsights.WorkerService` | 2.23.0 | Older — 2.22.0 had high-severity info disclosure (CVE-2024-0057 in downstream MSAL); verify patched |
| `Microsoft.Azure.Functions.Worker` | 2.51.0 | Current |
| `Microsoft.Azure.Functions.Worker.ApplicationInsights` | 2.50.0 | Current |
| `Microsoft.Azure.Functions.Worker.Extensions.DurableTask` | 1.14.1 | Current |
| `Microsoft.Azure.Functions.Worker.Extensions.Http.AspNetCore` | 2.1.0 | Current |
| `Microsoft.Azure.Functions.Worker.Sdk` | 2.0.7 | Current |
| `xunit` | 2.5.3 | Current |
| `Microsoft.NET.Test.Sdk` | 17.8.0 | Older — consider updating to 17.12+ |

**Recommendation:**
1. Run `dotnet list package --vulnerable` and `dotnet list package --outdated` against the solution.
2. Consider enabling NuGet audit mode by adding `<NuGetAudit>true</NuGetAudit>` to `Directory.Build.props`.
3. Update `Microsoft.ApplicationInsights.WorkerService` to the latest 2.x release.

---

## Positive Security Observations

The following practices are **well-implemented** and worth highlighting:

1. **Slack signature verification uses `CryptographicOperations.FixedTimeEquals`** — proper constant-time comparison preventing timing attacks (line 53 of `SlackSignatureVerifier.cs`).

2. **Discord signature verification uses Ed25519** via `NSec.Cryptography` — a modern, secure signature algorithm with no timing side channels in the library's `Verify` call.

3. **Timestamp replay protection** — Both Slack and Discord verifiers check timestamps against a 5-minute window (300 seconds), preventing replay attacks.

4. **No hardcoded production secrets** — All credentials are read from environment variables. Test secrets are clearly marked as test-only constants.

5. **Proper null/empty guarding on secrets** — Both `SlackSignatureVerifier.Verify` and `DiscordSignatureVerifier.Verify` return `false` if the signing secret or public key is empty.

6. **No SQL injection vectors** — The codebase uses no SQL or database access.

7. **No command injection vectors** — No `Process.Start`, shell execution, or dynamic command construction.

8. **No insecure random** — No use of `System.Random` for security-sensitive purposes.

9. **Safe hex encoding/decoding** — Uses `Convert.FromHexString` / `Convert.ToHexString` with proper error handling.

10. **Azure credential management** — Uses `DefaultAzureCredential` (managed identity / service principal) rather than embedded credentials.

---

## Remediation Priority

| Priority | Finding | Effort | Impact |
|----------|---------|--------|--------|
| 🔴 Immediate | F1: Add auth to alert webhook | Low | Prevents arbitrary alert injection |
| 🔴 Immediate | F2: Randomize Discord tokens | Low | Prevents token prediction attacks |
| 🟡 Soon | F3: Add token expiry | Low | Limits replay window |
| 🟡 Soon | F4: Use AuthorizationLevel.Function on alert endpoint | Low | Defense in depth |
| 🟢 When convenient | F5–F9 | Low–Medium | Hardening |

---

*End of security foot-gun analysis.*
