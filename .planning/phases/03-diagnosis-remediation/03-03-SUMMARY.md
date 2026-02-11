---
phase: 03-diagnosis-remediation
plan: 03
subsystem: api
tags: [python, fastapi, coordinator, diagnosis, remediation, testing]

# Dependency graph
requires:
  - phase: 03-01
    provides: Diagnosis agent synthesis with deterministic fallback output
  - phase: 03-02
    provides: Remediation agent with safe-by-default action modeling
provides:
  - Coordinator now orchestrates investigators, diagnosis, and remediation in one pipeline run
  - Stable webhook report schema returning unified findings plus diagnosis/remediation AgentResults
  - Deterministic local e2e coverage for full webhook wiring without Azure/Foundry credentials
affects: [04-01, 05-01]

# Tech tracking
tech-stack:
  added: []
  patterns: [coordinator-post-investigation-synthesis, response-model-enforced-webhook-schema, deterministic-local-e2e-monkeypatch]

key-files:
  created: [tests/test_e2e_pipeline_local.py]
  modified:
    [
      src/agents/coordinator.py,
      src/models/findings.py,
      src/web/app.py,
      tests/test_parallel_investigation.py,
      tests/test_webhook_flow.py,
    ]

key-decisions:
  - "Introduced `InvestigationReport` as the coordinator/webhook contract so unified findings and downstream agent outputs remain explicit and type-safe."
  - "Kept diagnosis and remediation outputs as top-level AgentResult sections rather than mutating `UnifiedFindings.results`, preserving investigator aggregation semantics."
  - "Bound `/webhooks/alert` to `response_model=InvestigationReport` to guarantee stable JSON shape for downstream Slack formatting."

patterns-established:
  - "Coordinator now executes investigation fan-out first, then sequential diagnosis/remediation synthesis using shared timeout/error coercion logic."
  - "Webhook integration tests should validate top-level report sections (`unified_findings`, `diagnosis_result`, `remediation_result`) and nested investigator result statuses."

# Metrics
duration: 12 min
completed: 2026-02-11
---

# Phase 3 Plan 3: Coordinator Pipeline Integration Summary

**Single-call incident analysis now returns investigator findings plus diagnosis and remediation suggestions in a stable report payload that is test-covered end-to-end offline.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-11T04:16:05Z
- **Completed:** 2026-02-11T04:28:13Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Extended `CoordinatorAgent` to run diagnosis after investigator fan-out and remediation after diagnosis, returning an `InvestigationReport`.
- Updated `/webhooks/alert` to return the full typed report contract (unified findings + diagnosis result + remediation result).
- Added deterministic local e2e coverage for the full webhook pipeline with monkeypatched investigator/diagnosis/remediation agents.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend coordinator pipeline to include diagnosis and remediation** - `5d266a0` (feat)
2. **Task 2: Update webhook response to return the full report** - `275e0a4` (feat)
3. **Task 3: Add a local e2e test with monkeypatched agents** - `f8d29c0` (test)

**Plan metadata:** Pending docs commit for summary/state updates.

## Files Created/Modified
- `src/agents/coordinator.py` - Added post-investigation diagnosis/remediation orchestration and report-level return shape.
- `src/models/findings.py` - Added `InvestigationReport` model containing unified findings plus diagnosis/remediation AgentResults.
- `src/web/app.py` - Switched webhook response to `InvestigationReport` schema.
- `tests/test_parallel_investigation.py` - Updated coordinator/webhook assertions for report schema and patched diagnosis/remediation for deterministic behavior.
- `tests/test_webhook_flow.py` - Updated webhook assertions to verify nested report sections.
- `tests/test_e2e_pipeline_local.py` - Added deterministic local e2e test for full webhook pipeline wiring.

## Decisions Made
- Used the existing timeout/error coercion path for diagnosis and remediation calls to keep degraded/error handling behavior consistent across all agent stages.
- Kept investigator outputs under `unified_findings.results` while exposing diagnosis/remediation separately to avoid breaking investigator aggregation semantics.
- Validated manual smoke output against explicit five sections (cost/resource/history + diagnosis + remediation) to confirm Slack-friendly stability.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated legacy webhook contract tests to match report schema**
- **Found during:** Task 2 (Update webhook response to return the full report)
- **Issue:** Existing tests asserted legacy webhook payload shape and failed full `pytest` verification after report contract update.
- **Fix:** Updated `tests/test_parallel_investigation.py` and `tests/test_webhook_flow.py` to assert `InvestigationReport` sections and nested investigator results.
- **Files modified:** `tests/test_parallel_investigation.py`, `tests/test_webhook_flow.py`
- **Verification:** `. .venv/bin/activate && PYTHONPATH=src pytest -q`
- **Committed in:** `275e0a4` (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary alignment to keep verification green after intended webhook contract evolution; no scope creep.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness
- Phase 3 objective is now met: one webhook call returns investigation findings plus diagnosis/remediation suggestions.
- Output contract is stable and covered by deterministic local tests, ready for Slack human-loop integration work in Phase 4.
- No blockers carried forward.

---
*Phase: 03-diagnosis-remediation*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist on disk: `tests/test_e2e_pipeline_local.py`, `.planning/phases/03-diagnosis-remediation/03-03-SUMMARY.md`.
- Verified task commits exist in git history: `5d266a0`, `275e0a4`, `f8d29c0`.
