---
phase: quick-003-add-discord-interactive-approval-flow-pa
plan: 01
subsystem: api
tags: [discord, approvals, fastapi, signatures, slack-parity]

requires:
  - phase: quick-002-upgrade-discord-notifications-to-high-tier-ux-and-reliability
    provides: Discord notification formatting and delivery reliability primitives
provides:
  - Signed Discord interaction verification with Ed25519 and replay-window enforcement
  - Discord interaction callback endpoint mapped to shared approval decisions
  - Regression tests for Discord interaction parity with Slack remediation flow
affects: [human-loop, discord, slack, remediation]

tech-stack:
  added: [pynacl]
  patterns:
    - Verify Discord signatures against raw request body before JSON parsing
    - Keep cross-platform action mapping via shared action IDs and ApprovalDecision values

key-files:
  created:
    - tests/test_discord_interactions.py
    - .planning/quick/003-add-discord-interactive-approval-flow-pa/003-SUMMARY.md
  modified:
    - requirements.txt
    - src/integrations/discord.py
    - src/integrations/message_format.py
    - src/web/app.py
    - tests/test_discord_formatting.py
    - .env.example

key-decisions:
  - Reused the existing ACTION_DECISION_MAP for Discord callbacks to preserve Slack/Discord decision parity.
  - Returned Discord interaction responses as type 4 with ephemeral flags for immediate acknowledgment UX.

patterns-established:
  - "Discord button IDs are encoded as {action}:{investigation_id} for deterministic parsing."
  - "Signed callback verification uses a strict 5-minute timestamp tolerance and fails closed."

duration: 6m
completed: 2026-02-13
---

# Phase [quick-003] Plan [01]: Discord Interactive Approval Flow Summary

**Discord now supports signed approve/reject/investigate interactions that feed the existing in-memory approval and remediation execution path used by Slack.**

## Performance

- **Duration:** 6m
- **Started:** 2026-02-13T01:29:23Z
- **Completed:** 2026-02-13T01:35:25Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Added `verify_discord_signature` (Ed25519, stale timestamp rejection, fail-closed header/key handling) plus custom-id helpers in `src/integrations/discord.py`.
- Extended `format_investigation_report_for_discord` to include Approve/Reject/Investigate buttons wired with deterministic `custom_id` values carrying investigation IDs.
- Implemented `POST /webhooks/discord/interactions` in `src/web/app.py` with signature-first validation, ping support, decision recording parity, and approve-only remediation queueing.
- Added focused interaction tests and formatter assertions, and documented `DISCORD_INTERACTIONS_PUBLIC_KEY` in `.env.example`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Discord interaction primitives (signed callback validation + decision IDs)** - `fc5cb72` (feat)
2. **Task 2: Add secure Discord interactions endpoint with decision mapping parity** - `4465b61` (feat)
3. **Task 3: Add Discord interaction tests + Slack non-regression checks** - `8f6102d` (test)

## Files Created/Modified

- `requirements.txt` - Added `pynacl` dependency for Discord signature verification.
- `src/integrations/discord.py` - Added signature verifier, custom-id build/parse helpers, and header normalization helper.
- `src/integrations/message_format.py` - Added Discord button component row with deterministic custom IDs.
- `src/web/app.py` - Added signed Discord interactions webhook endpoint and decision persistence flow.
- `tests/test_discord_interactions.py` - Added signature, ping, decision mapping, and remediation queueing coverage.
- `tests/test_discord_formatting.py` - Added assertions for action button structure and custom ID wiring.
- `.env.example` - Added `DISCORD_INTERACTIONS_PUBLIC_KEY` documentation.

## Decisions Made

- Kept Slack behavior unchanged by adding Discord routing as a parallel path rather than altering Slack handlers or signature flow.
- Used existing `ApprovalDecision` semantics and investigate reason text to avoid introducing Discord-specific state divergence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Environment defaulted to `python3` instead of `python`/`pytest` CLI aliases**
- **Found during:** Task 1 and Task 3 verification
- **Issue:** `python` command was unavailable and `pytest` referenced a different interpreter without required packages.
- **Fix:** Executed verification with `python3 -m compileall` and `python3 -m pytest`.
- **Files modified:** None
- **Verification:** Targeted compile and pytest commands succeeded under `python3`.
- **Committed in:** N/A (execution environment only)

**2. [Rule 3 - Blocking] Missing local test dependencies for Azure SDK/pytest imports**
- **Found during:** Task 3 verification
- **Issue:** Test import path failed due to missing `azure.mgmt.compute` and `pytest` under the active interpreter.
- **Fix:** Installed runtime and dev dependencies via `python3 -m pip install --break-system-packages -r requirements.txt` and `python3 -m pip install --break-system-packages -r requirements-dev.txt`.
- **Files modified:** None
- **Verification:** `python3 -m pytest -q tests/test_discord_interactions.py tests/test_discord_formatting.py tests/test_slack_action_execution.py tests/test_slack_signature.py` passed.
- **Committed in:** N/A (execution environment only)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Environment-only fixes were required to run verification; implementation scope remained unchanged.

## Authentication Gates

None.

## Issues Encountered

None beyond local environment toolchain mismatch resolved via Rule 3.

## User Setup Required

External Discord setup is required:
- Add `DISCORD_INTERACTIONS_PUBLIC_KEY` from the Discord Developer Portal.
- Configure Discord Interactions Endpoint URL to `/webhooks/discord/interactions` on the deployed app.

## Next Phase Readiness

- Discord and Slack now share deterministic approval semantics and remediation queue behavior.
- Ready for manual smoke tests against real Discord interactions endpoint once public key + endpoint are configured.

## Self-Check: PASSED

- Verified summary and new test files exist on disk.
- Verified task commits `fc5cb72`, `4465b61`, and `8f6102d` exist in git history.

---

*Phase: quick-003-add-discord-interactive-approval-flow-pa*
*Completed: 2026-02-13*
