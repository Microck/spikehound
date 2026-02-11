---
phase: 04-human-loop
plan: 04
subsystem: api
tags: [python, fastapi, azure-monitor, idempotency, retries]

# Dependency graph
requires:
  - phase: 04-03
    provides: Approval-gated remediation execution and Slack follow-up reporting
provides:
  - Azure Monitor common schema webhook normalization for stable investigation fields
  - In-memory webhook idempotency cache with TTL for duplicate alert suppression
  - Transient-error retry loop for coordinator agent runs
  - Realistic Azure payload parsing and resilience tests
affects: [05-01, demo]

# Tech tracking
tech-stack:
  added: []
  patterns: [ingress-payload-normalization, webhook-idempotency-cache, transient-error-retry]

key-files:
  created:
    [
      tests/conftest.py,
      tests/test_alert_payload_parsing.py,
    ]
  modified:
    [
      src/web/app.py,
      src/web/settings.py,
      src/agents/coordinator.py,
    ]

key-decisions:
  - "Normalize webhook payloads at the FastAPI boundary so every downstream agent receives deterministic keys."
  - "Use alert_id as the in-memory idempotency key with a configurable TTL to avoid duplicate pipeline execution."
  - "Retry once only when error messages indicate transient timeout/network conditions."

patterns-established:
  - "Webhook handlers should normalize external schemas into an internal contract before orchestration."
  - "In-memory demo caches should be guarded by deterministic test fixtures to prevent cross-test state leakage."

# Metrics
duration: 7 min
completed: 2026-02-11
---

# Phase 4 Plan 4: Webhook Hardening Summary

**Webhook intake now accepts Azure Monitor common schema alerts, derives stable investigation IDs, suppresses duplicate alert executions, and retries transient orchestration errors once before returning a report.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-11T19:27:59Z
- **Completed:** 2026-02-11T19:35:10Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added alert normalization for Azure Monitor common schema (`alert_id`, `rule_name`, `severity`, `fired_date_time`, `resource_id`) while preserving support for existing simple payloads.
- Updated coordinator alert summary handling so investigation identifiers come from normalized `alert_id` and carry rule/severity/timestamp context.
- Added configurable idempotency TTL and retry count settings, idempotent webhook response caching, and transient error retry behavior.
- Added realistic webhook tests for Azure payload parsing, duplicate webhook deduplication, and transient retry execution.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add alert payload normalization (Azure Monitor common schema)** - `82483ef` (feat)
2. **Task 2: Add idempotency + basic retry policy** - `2019101` (feat)
3. **Task 3: Add tests for realistic alert payload parsing** - `dd451ae` (test)

**Plan metadata:** Pending docs commit for summary/state/roadmap updates.

## Files Created/Modified
- `src/web/app.py` - Added alert normalization, idempotency cache handling, and transient error retry orchestration.
- `src/agents/coordinator.py` - Standardized investigation ID extraction and propagated normalized alert context fields.
- `src/web/settings.py` - Added `IDEMPOTENCY_TTL_SECONDS` and `MAX_AGENT_RETRIES` settings.
- `tests/conftest.py` - Added autouse fixture to reset in-memory webhook state between tests.
- `tests/test_alert_payload_parsing.py` - Added realistic Azure Monitor payload, idempotency, and retry behavior tests.

## Decisions Made
- Normalize at webhook ingress rather than inside each agent to avoid schema branching in multiple places.
- Keep idempotency state in-memory for demo scope and expose TTL via settings for predictable tuning.
- Limit transient retries to one configurable pass to avoid runaway loops while still recovering from brief faults.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reset in-memory webhook state between tests**
- **Found during:** Task 2 (Add idempotency + basic retry policy)
- **Issue:** New idempotency cache persisted alert IDs across tests, causing duplicate-detection to reuse stale reports and fail existing webhook assertions.
- **Fix:** Added an autouse pytest fixture that clears webhook in-memory stores (`approval_records`, `latest_reports`, `latest_remediation_plans`, `processed_investigations`) before every test.
- **Files modified:** tests/conftest.py
- **Verification:** `. .venv/bin/activate && PYTHONPATH=src pytest -q` (33 passed)
- **Committed in:** `2019101` (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Deviation was required for reliable test isolation after introducing idempotency state; no scope creep.

## Authentication Gates

None.

## Issues Encountered

- Initial Task 2 test run failed because new idempotency cache leaked state across tests using shared alert IDs; resolved with `tests/conftest.py` fixture reset.

## User Setup Required

None - no new external service configuration required for this plan.

## Next Phase Readiness
- Human-loop webhook intake is now resilient to realistic Azure payloads and duplicate delivery.
- Retry behavior improves tolerance for transient failures without changing approval-gated execution semantics.
- Ready to begin Phase 5 demo preparation (`05-01-PLAN.md`).

---
*Phase: 04-human-loop*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist on disk: `tests/conftest.py`, `tests/test_alert_payload_parsing.py`.
- Verified task commits exist in git history: `82483ef`, `2019101`, `dd451ae`.
