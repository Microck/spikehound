---
phase: quick-001-add-discord-notifications
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/integrations/discord.py
  - src/integrations/message_format.py
  - src/web/app.py
  - tests/test_discord_formatting.py
  - .env.example
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Slack notifications remain unchanged (still best-effort + env-gated)."
    - "Discord notifications send alongside Slack when DISCORD_WEBHOOK_URL is set."
    - "Discord notifications are skipped (no error) when DISCORD_WEBHOOK_URL is missing."
  artifacts:
    - path: "src/integrations/discord.py"
      provides: "Discord webhook sender (env-gated, best-effort)"
    - path: "src/integrations/message_format.py"
      provides: "Discord message formatter for InvestigationReport"
      exports: ["format_investigation_report_for_discord"]
    - path: "src/web/app.py"
      provides: "Alert webhook triggers both Slack + Discord notifications"
    - path: ".env.example"
      provides: "Documents DISCORD_WEBHOOK_URL"
  key_links:
    - from: "src/web/app.py"
      to: "src/integrations/discord.py"
      via: "send_webhook call"
      pattern: "send_.*discord"
    - from: "src/web/app.py"
      to: "src/integrations/message_format.py"
      via: "format_investigation_report_for_discord"
      pattern: "format_investigation_report_for_discord"
---

<objective>
Add Discord notifications (webhook-based) alongside existing Slack notifications.

Purpose: Provide Discord delivery without disrupting Slack, and keep it optional via env gating.
Output: Discord webhook sender + formatter + alert webhook wiring + minimal unit coverage.
</objective>

<execution_context>
@/home/ubuntu/.config/opencode/get-shit-done/workflows/execute-plan.md
@/home/ubuntu/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@src/web/app.py
@src/integrations/slack.py
@src/integrations/message_format.py
@tests/test_slack_formatting.py
@.env.example
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add Discord webhook integration + formatter</name>
  <files>
src/integrations/discord.py
src/integrations/message_format.py
  </files>
  <action>
- Create `src/integrations/discord.py` mirroring the Slack integration style:
  - Read `DISCORD_WEBHOOK_URL` from env; if missing, log info and return (no exception).
  - Use `httpx.post(..., timeout=10.0)` and `raise_for_status()`; catch `httpx.HTTPError` and log warning.
  - Keep function naming unambiguous (e.g., `send_discord_webhook(...)`) so Slack imports remain unchanged.
- Extend `src/integrations/message_format.py` with `format_investigation_report_for_discord(report)`:
  - Reuse the same summary facts as Slack (alert id, top cost drivers, confidence, root cause, first action).
  - Return a dict payload compatible with Discord webhook JSON (at minimum `{ "content": "..." }`).
  </action>
  <verify>
python -m compileall src/integrations/discord.py src/integrations/message_format.py
  </verify>
  <done>
- `src/integrations/discord.py` exists and is env-gated + best-effort.
- `format_investigation_report_for_discord()` returns a non-empty `content` string for a valid report.
  </done>
</task>

<task type="auto">
  <name>Task 2: Wire Discord send into alert webhook (preserve Slack behavior)</name>
  <files>src/web/app.py</files>
  <action>
- In `src/web/app.py` `/webhooks/alert` handler, keep Slack send exactly as-is.
- Add a second best-effort Discord send after Slack:
  - Format with `format_investigation_report_for_discord(report)`.
  - Send via `send_discord_webhook(...)`.
  - Wrap Discord send in its own try/except so Discord failure cannot affect Slack or the HTTP response.
  </action>
  <verify>
python -m compileall src/web/app.py
  </verify>
  <done>
- Slack notifications still trigger and failures stay non-blocking.
- Discord notifications trigger on the same webhook path when configured, and are non-blocking.
  </done>
</task>

<task type="auto">
  <name>Task 3: Add minimal tests + env example entry</name>
  <files>
tests/test_discord_formatting.py
.env.example
  </files>
  <action>
- Add `tests/test_discord_formatting.py` modeled after `tests/test_slack_formatting.py`:
  - Use the same sample `InvestigationReport` construction.
  - Assert formatter returns a dict with non-empty `content` and includes key details (resource label, confidence, root cause, first remediation action).
  - Assert payload is JSON serializable (via `json.dumps`).
- Update `.env.example` with a new `# Discord` section and `DISCORD_WEBHOOK_URL=` entry (do not touch `.env`).
  </action>
  <verify>
pytest -q
  </verify>
  <done>
- New test passes.
- `.env.example` documents `DISCORD_WEBHOOK_URL`.
  </done>
</task>

</tasks>

<verification>
- `pytest -q` passes.
- Manually (optional): run the app and hit `/webhooks/alert` with a sample payload; confirm Slack still works and Discord posts when `DISCORD_WEBHOOK_URL` is set.
</verification>

<success_criteria>
- Discord webhook delivery is added without any Slack behavior regressions.
- Discord delivery is fully optional via `DISCORD_WEBHOOK_URL`.
</success_criteria>

<output>
After completion, create `.planning/quick/001-add-discord-notifications-alongside-slac/001-SUMMARY.md`.
</output>
