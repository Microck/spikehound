---
phase: quick-002-upgrade-discord-notifications-to-high-ti
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/integrations/message_format.py
  - src/integrations/discord.py
  - tests/test_discord_formatting.py
  - tests/test_discord_webhook.py
  - .env.example
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Discord alert messages render as rich, readable webhook messages (not plain text-only dumps)."
    - "Discord delivery retries boundedly on 429/transient failures and remains non-blocking if delivery still fails."
    - "Discord payloads are mention-safe by default (no accidental @everyone/@here/user-role pings)."
    - "Slack notification behavior and wiring remain unchanged."
  artifacts:
    - path: "src/integrations/message_format.py"
      provides: "Discord formatter returns rich payload with embed fields and mention-safe metadata"
      exports: ["format_investigation_report_for_discord"]
    - path: "src/integrations/discord.py"
      provides: "Discord sender with rate-limit/transient retry handling and bounded backoff"
      exports: ["send_discord_webhook"]
    - path: "tests/test_discord_webhook.py"
      provides: "Retry behavior coverage for 429/transient/permanent failure paths"
    - path: "tests/test_discord_formatting.py"
      provides: "Discord rich payload + mention safety assertions"
    - path: ".env.example"
      provides: "Optional Discord retry tuning env vars"
  key_links:
    - from: "src/web/app.py"
      to: "src/integrations/message_format.py"
      via: "format_investigation_report_for_discord(report)"
      pattern: "format_investigation_report_for_discord"
    - from: "src/web/app.py"
      to: "src/integrations/discord.py"
      via: "send_discord_webhook(discord_message)"
      pattern: "send_discord_webhook"
    - from: "src/integrations/message_format.py"
      to: "Discord webhook JSON"
      via: "allowed_mentions + embeds fields"
      pattern: "allowed_mentions|embeds"
---

<objective>
Upgrade Discord notifications to production-grade quality with rich message UX, resilient webhook delivery, and safe mention handling.

Purpose: Improve operator readability and delivery reliability in Discord while preserving existing Slack behavior exactly.
Output: Enhanced Discord payload formatter, hardened webhook sender retry logic, and focused reliability/safety test coverage.
</objective>

<execution_context>
@/home/ubuntu/.config/opencode/get-shit-done/workflows/execute-plan.md
@/home/ubuntu/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@src/integrations/discord.py
@src/integrations/message_format.py
@src/web/app.py
@tests/test_discord_formatting.py
@tests/test_slack_formatting.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Upgrade Discord formatter to rich, mention-safe webhook payloads</name>
  <files>src/integrations/message_format.py</files>
  <action>
- Refactor `format_investigation_report_for_discord(report)` to return a richer Discord payload:
  - Keep a concise `content` summary line for clients that do not render embeds.
  - Add one primary embed containing alert ID, top cost drivers, confidence, root cause, and first remediation action in labeled fields.
  - Include deterministic formatting/length guards so oversized values cannot produce invalid webhook payloads.
- Add mention safety directly in formatter output:
  - Include `allowed_mentions` that disables implicit mentions by default (`parse: []`).
  - Ensure any alert-derived user data is placed in safe text fields (no intentional mention expansion).
- Do not modify `format_investigation_report_for_slack` or shared Slack formatting helpers.
  </action>
  <verify>
python -m compileall src/integrations/message_format.py
  </verify>
  <done>
- Discord formatter output includes `content`, `embeds`, and `allowed_mentions`.
- Output still contains the key investigation facts already present in Slack text.
- Slack formatter behavior is untouched.
  </done>
</task>

<task type="auto">
  <name>Task 2: Harden Discord sender with rate-limit-aware retries</name>
  <files>
src/integrations/discord.py
.env.example
  </files>
  <action>
- Upgrade `send_discord_webhook(payload)` to use bounded retry logic for reliability:
  - Retry on HTTP 429 using `Retry-After` (or equivalent rate-limit headers) when available.
  - Retry on transient transport/server errors (timeouts, connection resets, 5xx).
  - Fail fast on permanent client errors (non-429 4xx) to avoid noisy loops.
  - Keep overall behavior best-effort and non-blocking (never raise to caller).
- Add small, explicit retry/backoff constants (and optional env overrides documented in `.env.example`) so tuning does not require code changes.
- Preserve Slack behavior by limiting changes to Discord integration code only.
  </action>
  <verify>
python -m compileall src/integrations/discord.py
  </verify>
  <done>
- Discord sender performs bounded retries for transient/rate-limit failures.
- Sender still returns without exception after exhausted retries.
- Slack integration code path remains unchanged.
  </done>
</task>

<task type="auto">
  <name>Task 3: Add focused tests for Discord UX, retry semantics, and Slack non-regression</name>
  <files>
tests/test_discord_formatting.py
tests/test_discord_webhook.py
  </files>
  <action>
- Extend `tests/test_discord_formatting.py` to assert:
  - Rich payload shape (`content` + `embeds`) and presence of key fields.
  - Mention safety metadata (`allowed_mentions.parse == []`).
  - JSON serialization still succeeds.
- Add `tests/test_discord_webhook.py` with sender behavior coverage:
  - 429 response path retries and eventually succeeds.
  - transient network/timeout path retries and eventually succeeds.
  - permanent 4xx path does not retry repeatedly.
  - exhausted retry path logs warning and does not raise.
- Run targeted regression tests that include Slack formatting to confirm no Slack contract drift.
  </action>
  <verify>
pytest -q tests/test_discord_formatting.py tests/test_discord_webhook.py tests/test_slack_formatting.py
  </verify>
  <done>
- New Discord tests pass and enforce retry/safety behavior.
- Existing Slack formatting test still passes without modification.
  </done>
</task>

</tasks>

<verification>
- `pytest -q tests/test_discord_formatting.py tests/test_discord_webhook.py tests/test_slack_formatting.py` passes.
- Manual smoke (optional): trigger `/webhooks/alert` and confirm Discord renders embed-rich output with no real mention ping behavior.
</verification>

<success_criteria>
- Discord notifications now deliver readable rich payloads suitable for incident channels.
- Delivery is resilient to Discord rate limits/transient failures with bounded retries.
- Mention behavior is safe-by-default and Slack behavior remains unchanged.
</success_criteria>

<output>
After completion, create `.planning/quick/002-upgrade-discord-notifications-to-high-ti/002-SUMMARY.md`.
</output>
