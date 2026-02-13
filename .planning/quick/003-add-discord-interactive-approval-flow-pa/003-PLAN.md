---
phase: quick-003-add-discord-interactive-approval-flow-pa
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - .env.example
  - src/integrations/discord.py
  - src/integrations/message_format.py
  - src/web/app.py
  - tests/test_discord_interactions.py
  - tests/test_discord_formatting.py
  - tests/test_slack_action_execution.py
autonomous: true
user_setup:
  - service: discord
    why: "Receive signed Discord button interactions for human approval decisions"
    env_vars:
      - name: DISCORD_INTERACTIONS_PUBLIC_KEY
        source: "Discord Developer Portal -> Application -> General Information -> Public Key"
    dashboard_config:
      - task: "Set Interactions Endpoint URL to the deployed `/webhooks/discord/interactions` route"
        location: "Discord Developer Portal -> Application -> General Information"

must_haves:
  truths:
    - "Discord incident notifications include Approve/Reject/Investigate interactive actions tied to investigation IDs."
    - "Discord interaction callbacks are rejected when signatures are invalid, missing, or stale."
    - "Discord action IDs map deterministically to approve/reject/investigate decisions and persist in the shared in-memory approval store."
    - "Approve decisions from Discord queue the same remediation execution path already used by Slack approvals."
    - "Slack interactive flow and Slack signature verification behavior remain unchanged."
  artifacts:
    - path: "src/integrations/discord.py"
      provides: "Discord interaction signature verification helper and action-id parsing utilities"
      exports: ["verify_discord_signature"]
    - path: "src/integrations/message_format.py"
      provides: "Discord report payload includes interaction components for approve/reject/investigate"
      exports: ["format_investigation_report_for_discord"]
    - path: "src/web/app.py"
      provides: "`POST /webhooks/discord/interactions` endpoint with ping handling, signature checks, and decision recording"
    - path: "tests/test_discord_interactions.py"
      provides: "Coverage for Discord signature verification and action callback mapping"
    - path: ".env.example"
      provides: "Documents Discord interaction public key configuration"
  key_links:
    - from: "src/integrations/message_format.py"
      to: "src/web/app.py"
      via: "button `custom_id` format carrying decision + investigation_id"
      pattern: "approve_remediation:|reject_remediation:|investigate_more:"
    - from: "src/web/app.py"
      to: "src/integrations/discord.py"
      via: "verify_discord_signature(raw_body, headers)"
      pattern: "verify_discord_signature"
    - from: "src/web/app.py"
      to: "src/models/approval.py"
      via: "ApprovalRecord persisted in `approval_records`"
      pattern: "approval_records\[investigation_id\]"
    - from: "src/web/app.py"
      to: "src/web/app.py::_execute_approved_remediation"
      via: "BackgroundTasks for approve decisions"
      pattern: "background_tasks\.add_task\(_execute_approved_remediation"
---

<objective>
Add Discord interactive approval flow parity with Slack while preserving current Slack behavior.

Purpose: Enable secure, signed Discord Approve/Reject/Investigate callbacks that feed the same human-loop decision + remediation pipeline.
Output: Discord interaction signature verification, Discord action callback endpoint, decision mapping to `ApprovalDecision`, and regression-safe test coverage.
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
@src/models/approval.py
@tests/test_slack_action_execution.py
@tests/test_discord_webhook.py
@.env.example
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add Discord interaction primitives (signed callback validation + decision IDs)</name>
  <files>
requirements.txt
src/integrations/discord.py
src/integrations/message_format.py
  </files>
  <action>
- Add Discord interaction signature verification in `src/integrations/discord.py`:
  - Introduce `verify_discord_signature(raw_body, headers) -> bool` using Discord's Ed25519 scheme (`X-Signature-Ed25519`, `X-Signature-Timestamp`, timestamp+body payload).
  - Fail closed when signature headers or `DISCORD_INTERACTIONS_PUBLIC_KEY` are missing.
  - Reject stale timestamps (same 5-minute replay guard strategy used for Slack).
  - Add `PyNaCl` (`pynacl`) to `requirements.txt` if not already present; do not add optional/unused crypto libraries.
- Extend `format_investigation_report_for_discord(report)` to include one action row with three buttons:
  - `approve_remediation:{investigation_id}`
  - `reject_remediation:{investigation_id}`
  - `investigate_more:{investigation_id}`
  - Keep existing rich embed, content summary, and mention-safety behavior unchanged.
- Do not modify Slack formatter output or Slack helper functions.
  </action>
  <verify>
python -m compileall src/integrations/discord.py src/integrations/message_format.py
  </verify>
  <done>
- Discord formatter emits deterministic component `custom_id` values that carry decision + investigation id.
- Discord signature verifier exists and returns False for missing/invalid/stale signatures.
- Slack message formatting behavior is unchanged.
  </done>
</task>

<task type="auto">
  <name>Task 2: Add secure Discord interactions endpoint with decision mapping parity</name>
  <files>src/web/app.py</files>
  <action>
- Add `POST /webhooks/discord/interactions` in `src/web/app.py`:
  - Read raw request body and verify with `verify_discord_signature` before any JSON parsing.
  - Handle Discord ping (`type=1`) with immediate `{"type": 1}` response.
  - Handle message component callbacks (`type=3`) by parsing `data.custom_id` in `{action}:{investigation_id}` format.
  - Map actions to existing decisions with parity to Slack:
    - `approve_remediation` -> `ApprovalDecision.APPROVE`
    - `reject_remediation` -> `ApprovalDecision.REJECT`
    - `investigate_more` -> `ApprovalDecision.INVESTIGATE`
  - Persist `ApprovalRecord` in `approval_records[investigation_id]` using same semantics as Slack (user id/name extraction + investigate reason).
  - Queue `_execute_approved_remediation` via `BackgroundTasks` only for approve decisions.
  - Return an interaction response payload acknowledging the recorded decision (ephemeral response is acceptable).
- Keep existing `/webhooks/slack/actions`, `ACTION_DECISION_MAP`, and Slack execution behavior unchanged.
  </action>
  <verify>
python -m compileall src/web/app.py
  </verify>
  <done>
- Discord callback endpoint rejects unsigned/invalid requests with 401.
- Valid Discord component interactions record decisions with the same decision vocabulary as Slack.
- Approve decisions queue remediation; reject/investigate do not trigger remediation execution.
  </done>
</task>

<task type="auto">
  <name>Task 3: Add Discord interaction tests + Slack non-regression checks</name>
  <files>
tests/test_discord_interactions.py
tests/test_discord_formatting.py
tests/test_slack_action_execution.py
.env.example
  </files>
  <action>
- Create `tests/test_discord_interactions.py` covering:
  - valid Discord signature accepted, invalid signature rejected, stale timestamp rejected.
  - ping payload returns `{"type": 1}`.
  - approve/reject/investigate callbacks map to correct `ApprovalDecision` and persist expected `ApprovalRecord` fields.
  - approve callback queues remediation execution path; reject/investigate do not.
- Extend `tests/test_discord_formatting.py` to assert Discord payload includes components with expected `custom_id` prefixes and investigation id wiring.
- Run Slack regression coverage (existing `tests/test_slack_action_execution.py`) without changing assertions; only update if required for shared fixture compatibility.
- Update `.env.example` with `DISCORD_INTERACTIONS_PUBLIC_KEY=` and a brief comment that it is required for signed interaction callbacks.
  </action>
  <verify>
pytest -q tests/test_discord_interactions.py tests/test_discord_formatting.py tests/test_slack_action_execution.py tests/test_slack_signature.py
  </verify>
  <done>
- Discord interaction tests enforce signature safety and decision parity behavior.
- Discord formatter tests confirm interactive buttons are wired to investigation IDs.
- Slack action/signature tests continue passing with no behavior drift.
  </done>
</task>

</tasks>

<verification>
- `pytest -q tests/test_discord_interactions.py tests/test_discord_formatting.py tests/test_slack_action_execution.py tests/test_slack_signature.py` passes.
- Optional manual smoke: send a Discord interaction ping + button callback to `/webhooks/discord/interactions` and confirm signature enforcement + decision recording logs.
</verification>

<success_criteria>
- Discord now supports secure interactive approval callbacks with approve/reject/investigate parity to Slack.
- Approval decisions from Discord feed the existing in-memory approval + remediation execution path.
- Slack behavior remains unchanged across webhook delivery, signature checks, and action execution.
</success_criteria>

<output>
After completion, create `.planning/quick/003-add-discord-interactive-approval-flow-pa/003-SUMMARY.md`.
</output>
