# Nightshift: Security Foot-Gun Analysis

**Repository:** Microck/spikehound  
**Date:** 2026-04-05  
**Task:** security-footgun  
**Category:** analysis

---

## Summary

Analysis of all 26 C# source files in spikehound identified **15 security-relevant findings** ranging from P0 (Critical) to P3 (Low). The most severe issues involve an **unauthenticated alert webhook endpoint** that triggers Azure resource mutations, **predictable Discord investigation tokens** that enable authorization bypass, and **deterministic state management** that loses all approval/enforcement state on restart.

---

## P0 — Critical Findings

### F-01: Alert Webhook Endpoint Has No Authentication

- **File:** `Spikehound.Functions/Functions/AlertWebhookFunction.cs`, line 30
- **Code:**
  ```csharp
  [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/alert")]
  ```
- **Description:** The `/webhooks/alert` endpoint uses `AuthorizationLevel.Anonymous`, meaning **any unauthenticated HTTP request** can submit an alert payload. This triggers the full `CoordinatorPipeline` which runs all five agents, and if a remediation plan is produced, Slack/Discord notifications are sent with "Approve" buttons. The endpoint also returns the full `InvestigationReport` including resource IDs, cost data, and diagnostic information.
- **Attack Scenario:** An attacker sends crafted JSON to `/webhooks/alert` with a `resource_id` pointing to a production VM. Operators click "Approve" and the VM is deallocated. Alternatively, flood the endpoint to trigger mass notifications, overwhelming operators.
- **Fix:** Add HMAC-based webhook signature verification, or use `AuthorizationLevel.Function` with an API key, or implement IP allowlisting.

### F-02: Predictable Discord Investigation Tokens Enable Authorization Bypass

- **File:** `Spikehound.Functions/InMemoryState.cs`, lines 76-84
- **Code:**
  ```csharp
  var bytes = Encoding.UTF8.GetBytes(investigationId);
  var hash = SHA256.HashData(bytes);
  var token = Convert.ToBase64String(hash)...
  ```
- **Description:** The Discord investigation token is a deterministic `SHA256(investigationId)` with no secret salt or randomness. The `investigationId` is the `alertId` from the alert payload, which is typically known/guessable.
- **Attack Scenario:** An attacker observes the `alertId` from the unauthenticated endpoint, computes `SHA256(alertId)`, and constructs the Discord `custom_id` value.
- **Fix:** Use cryptographically random tokens (`RandomNumberGenerator.GetBytes`) and store the mapping. Add HMAC-SHA256 with a server-side secret.

### F-03: Discord Investigation Token Fallback Allows Token Bypass

- **File:** `Spikehound.Functions/Functions/DiscordInteractionsFunction.cs`, lines 177-187
- **Code:**
  ```csharp
  return _state.TryResolveDiscordInvestigationToken(investigationReference, out var investigationId)
      ? investigationId
      : investigationReference;  // FALLBACK: uses raw value as investigation ID
  ```
- **Description:** When a Discord interaction is received with a `custom_id`, if it doesn't match any stored token, it's used directly as the `investigationId`. This completely defeats the token system.
- **Attack Scenario:** An attacker crafts a Discord interaction with `custom_id = "approve_remediation:<known-alert-id>"`, bypassing the token mechanism.
- **Fix:** Remove the fallback. Return `string.Empty` (rejecting the request) when the token doesn't resolve.

---

## P1 — High Findings

### F-04: InMemoryState Loses All Approval Records on Restart

- **File:** `Spikehound.Functions/InMemoryState.cs`, entire class
- **Description:** All state (approval records, remediation plans, execution tracking, idempotency cache, Discord tokens) is in `ConcurrentDictionary` instances. On restart (cold start, scale-out, crash, deployment), all state is lost:
  1. Previously rejected approvals can be resubmitted
  2. Idempotency protection is lost
  3. `AlreadyQueued` guard is lost
  4. Discord tokens are lost
- **Fix:** Use Durable Entities, Cosmos DB, or Table Storage for approval records and remediation state.

### F-05: Remediation Execution With No Per-Action Authorization

- **File:** `Spikehound.Functions/Remediation/ApprovalRemediationWorkflow.cs`, lines 287-291
- **Description:** Single boolean env var gates all remediation. No per-action-type authorization, no resource-level scoping, no restriction on which subscriptions/resource groups can be targeted.
- **Fix:** Implement allowlists for target subscriptions/resource groups, per-action-type enablement flags, and resource tag-based protection.

### F-06: No Input Validation on Alert Payload Size or Structure

- **File:** `Spikehound.Core/Parsing/AlertNormalizer.cs`, lines 138-191
- **Description:** `CollectResourceIdCandidates` performs unbounded recursive traversal of incoming JSON. No limit on nesting depth, payload size, or number of properties. Combined with F-01, this is a DoS vector.
- **Fix:** Add maximum body size check, limit `JsonDocument.Parse` with `MaxDepth`, add recursion depth counter.

### F-07: Error Messages Leak Internal Details

- **File:** `Spikehound.Core/Execution/RemediationExecution.cs`, lines 67-75
- **Description:** Raw exception messages from Azure SDK (containing subscription IDs, resource group names, tenant IDs) are sent to Slack/Discord channels.
- **Fix:** Sanitize exception messages before including in outcomes. Log full exception server-side only.

---

## P2 — Medium Findings

### F-08: No Rate Limiting on Any Endpoint
- **Files:** All function files
- **Description:** None of the HTTP endpoints implement rate limiting. The unauthenticated `/webhooks/alert` is especially concerning.
- **Fix:** Implement rate limiting at API gateway level or using Azure Functions throttling.

### F-09: Slack/Discord Endpoints Use Anonymous Authorization
- **Files:** `SlackActionsFunction.cs`, `DiscordInteractionsFunction.cs`
- **Description:** `AuthorizationLevel.Anonymous` on webhook endpoints. Signature verification is the sole defense.
- **Fix:** Acceptable for webhooks, but add IP allowlisting for Slack/Discord IP ranges as defense-in-depth.

### F-10: No Request Body Size Limits
- **File:** `Spikehound.Functions/Http/HttpUtils.cs`, lines 13-18
- **Description:** `ReadBodyBytesAsync` copies request body to MemoryStream with no size limit.
- **Fix:** Add maximum body size constant (e.g., 1MB).

### F-11: Slack Signature Verification Minor Timing Leak
- **File:** `Spikehound.Core/Security/SlackSignatureVerifier.cs`, lines 48-51
- **Description:** Length check before `FixedTimeEquals` is a minor timing leak. Low risk given fixed Slack signature format.
- **Fix:** Pad shorter value to match longer before comparing.

### F-12: DefaultAzureCredential Without Scope Limiting
- **File:** `Spikehound.Functions/Program.cs`, line 22
- **Description:** `ArmClient` created with `DefaultAzureCredential()` without specifying subscription ID or scope.
- **Fix:** Specify default subscription ID. Use managed identity with minimal required permissions.

---

## P3 — Low Findings

### F-13: Health Endpoint Exposes Service State Without Authentication
- **File:** `Spikehound.Functions/Functions/HealthFunction.cs`
- **Description:** Unauthenticated endpoint always returns `{ ok: true }` with no dependency checks.

### F-14: PruneExpired Only Called on New Alert — Memory Growth
- **File:** `Spikehound.Functions/InMemoryState.cs`, lines 55-64
- **Description:** No maximum capacity on dictionaries. Pruning only happens on new alerts. Unbounded memory growth possible.

### F-15: Durable Orchestration Activities Are Stubs
- **File:** `Spikehound.Functions/Durable/DurableCoordinatorOrchestration.cs`
- **Description:** All durable activity functions return hardcoded `"degraded"` strings and ignore input. If durable mode is enabled, meaningless results still trigger notifications.

---

## Priority Fix Order

1. **F-01**: Add authentication to alert webhook (API key or HMAC)
2. **F-03**: Remove token fallback — reject unresolved tokens
3. **F-02**: Use random tokens with HMAC instead of bare SHA256
4. **F-04**: Persist state to durable storage
5. **F-05**: Add resource-level scoping for remediation
6. **F-06**: Add input validation and payload size limits
7. **F-07**: Sanitize error messages before sending to external channels

---

*Generated by Nightshift v3 (GLM 5.1)*
