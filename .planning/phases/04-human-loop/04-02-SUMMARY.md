---
phase: 04-human-loop
plan: 02
subsystem: integrations
tags: [python, slack, fastapi, hmac, approvals]

# Dependency graph
requires:
  - phase: 04-01
    provides: Slack webhook delivery and report formatting integrated into the alert webhook flow
provides:
  - Slack action endpoint with signature verification and decision capture
  - Approval decision models for approve/reject/investigate outcomes
  - Slack message buttons that carry investigation IDs for follow-up actions
affects: [04-03, 05-01]

# Tech tracking
tech-stack:
  added: []
  patterns: [slack-hmac-signature-validation, in-memory-approval-decision-store]

key-files:
  created: [src/models/approval.py, tests/test_slack_signature.py]
  modified:
    [
      src/integrations/slack.py,
      src/integrations/message_format.py,
      src/web/app.py,
      .planning/phases/04-human-loop/04-USER-SETUP.md,
    ]

key-decisions:
  - "Reject Slack actions when signatures are invalid, missing, or stale to protect approval endpoints from spoofed requests."
  - "Use Slack action_id values as the decision source and carry investigation_id in each button value for deterministic recording."
  - "Persist approval records in process memory for phase 4 velocity, deferring durable storage to later execution/remediation work."

patterns-established:
  - "Interactive Slack actions should always validate HMAC signatures before parsing payloads."
  - "Human-loop decisions should be represented with typed models before wiring execution behavior."

# Metrics
duration: 4 min
completed: 2026-02-11
---

# Phase 4 Plan 2: Slack Approval Interaction Summary

**Slack notifications now include Approve/Reject/Investigate buttons, and a signed callback endpoint records those human decisions as typed approval records in memory.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T17:51:57Z
- **Completed:** 2026-02-11T17:56:30Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Added approval domain models (`ApprovalDecision`, `ApprovalRecord`) plus an in-memory store typing contract.
- Implemented Slack request signature verification (HMAC SHA256 + timestamp freshness window) with unit tests.
- Added Slack action buttons to report blocks and implemented `POST /webhooks/slack/actions` for secure decision recording.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add approval decision model + minimal in-memory store** - `0cf1521` (feat)
2. **Task 2: Add Slack signature verification helper** - `83d7b8f` (feat)
3. **Task 3: Add Slack interactive actions endpoint and wire buttons** - `c94a9bf` (feat)

**Plan metadata:** Pending docs commit for summary/state/roadmap updates.

## Files Created/Modified
- `src/models/approval.py` - Approval enum/model definitions and in-memory store typing alias.
- `src/integrations/slack.py` - Added Slack signature verification helper with freshness enforcement.
- `tests/test_slack_signature.py` - Unit coverage for valid, invalid, and stale Slack signatures.
- `src/integrations/message_format.py` - Added Approve/Reject/Investigate Block Kit buttons with `investigation_id` values.
- `src/web/app.py` - Added `/webhooks/slack/actions` endpoint that verifies signatures, parses payloads, and records approvals.
- `.planning/phases/04-human-loop/04-USER-SETUP.md` - Expanded manual Slack setup steps for interactivity credentials and callback URL.

## Decisions Made
- Treated stale timestamps (>5 minutes) as invalid during signature verification to reduce replay risk.
- Stored approval records keyed by `investigation_id` so later remediation steps can query the latest human decision deterministically.
- Returned explicit 4xx errors for malformed/unsupported Slack action payloads to keep callback failure modes observable.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

External Slack configuration is required. See `./04-USER-SETUP.md` for signing secret, bot token, and interactivity callback setup.

## Next Phase Readiness
- HUMAN-03 implementation is in place for local/dev execution: interactive buttons are rendered and callback requests are validated.
- Approval decisions are available in memory for plan 04-03 remediation execution wiring.
- No blockers carried forward.

---
*Phase: 04-human-loop*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist on disk: `src/models/approval.py`, `tests/test_slack_signature.py`, `.planning/phases/04-human-loop/04-02-SUMMARY.md`.
- Verified task commits exist in git history: `0cf1521`, `83d7b8f`, `c94a9bf`.
