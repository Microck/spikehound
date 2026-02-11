---
phase: 02-investigation-pipeline
plan: 04
subsystem: api
tags: [python, asyncio, parallel-orchestration, fastapi, pydantic, agent-result]

# Dependency graph
requires:
  - phase: 02-02
    provides: Resource agent findings and degraded-mode behavior
  - phase: 02-03
    provides: History agent backend selection and stable AgentResult envelope
provides:
  - Coordinator parallel orchestration for cost/resource/history investigators with per-agent timeout handling
  - Unified findings aggregation that merges all investigator results deterministically
  - Webhook response contract exposing `UnifiedFindings` with three investigator result entries
affects: [03-01, 04-01]

# Tech tracking
tech-stack:
  added: []
  patterns: [parallel-agent-fanout, timeout-to-agent-error, unified-findings-aggregation]

key-files:
  created: [tests/test_parallel_investigation.py]
  modified:
    [
      src/agents/cost_analyst.py,
      src/agents/resource_agent.py,
      src/agents/history_agent.py,
      src/agents/coordinator.py,
      src/models/findings.py,
      src/web/app.py,
    ]

key-decisions:
  - "Implemented coordinator fan-out with `asyncio.gather` + `asyncio.to_thread` and converted per-agent timeout events into `AgentStatus.ERROR` results."
  - "Kept a sync `handle_alert` wrapper around async orchestration for compatibility while making webhook path use `handle_alert_async` directly."
  - "Retained legacy top-level fields (`alert_id`, `cost_findings`, `notes`) in `UnifiedFindings` for non-breaking transition while establishing canonical `results` mapping."

patterns-established:
  - "Investigator agents share `run(alert_payload, hints=None) -> AgentResult[...]` and surface config gaps as degraded outcomes."
  - "Parallel behavior is validated deterministically with thread events + barrier synchronization instead of flaky timing thresholds."

# Metrics
duration: 7 min
completed: 2026-02-11
---

# Phase 2 Plan 4: Parallel Investigation Coordinator Summary

**Coordinator now executes Cost, Resource, and History investigations concurrently with timeout-safe aggregation into a unified webhook findings contract.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-11T02:27:53Z
- **Completed:** 2026-02-11T02:35:48Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Standardized investigator run contracts so all three agents return `AgentResult` envelopes with explicit degraded/error semantics.
- Added coordinator parallel fan-out (`asyncio.gather` + `asyncio.to_thread`) with deterministic merge into `UnifiedFindings` and per-agent timeout handling.
- Updated `/webhooks/alert` to return unified findings and added a deterministic parallel-start test that fails if orchestration regresses to sequential execution.

## Task Commits

Each task was committed atomically:

1. **Task 1: Convert investigators to consistent `run(..., hints=None) -> AgentResult` envelope** - `a5e8555` (feat)
2. **Task 2: Implement coordinator parallel execution with timeouts and unified merge** - `5afeb58` (feat)
3. **Task 3: Return unified webhook findings + deterministic parallel orchestration test** - `75f38a2` (feat)

**Plan metadata:** Pending docs commit for summary/state updates.

## Files Created/Modified
- `src/agents/cost_analyst.py` - Wrapped cost investigation output in `AgentResult[InvestigationFindings]` with degraded/error handling.
- `src/agents/resource_agent.py` - Aligned run signature and promoted runtime exceptions to `AgentStatus.ERROR` responses.
- `src/agents/history_agent.py` - Aligned run signature and converted persistence/search runtime failures into `AgentStatus.ERROR` outcomes.
- `src/agents/coordinator.py` - Added async parallel orchestration, per-agent timeout mapping, merge path, and compatibility wrapper.
- `src/models/findings.py` - Extended `UnifiedFindings.merge(...)` to include deterministic results mapping and unified response fields.
- `src/web/app.py` - Updated webhook endpoint to await coordinator parallel pipeline and return unified findings JSON.
- `tests/test_parallel_investigation.py` - Added barrier-based parallel-start proof and webhook unified-schema coverage.

## Decisions Made
- Coordinator execution uses `asyncio.gather` with threaded sync-agent execution to guarantee concurrent investigator starts while keeping each agent implementation synchronous.
- Timeout and unexpected execution failures are represented as explicit `AgentResult(status=error)` entries, preserving full 3-agent aggregation even when one branch fails.
- Unified webhook response keeps both canonical `results` map and compatibility fields during the transition to avoid contract breakage in existing tests.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

None - no additional external service or secret setup required for this plan.

## Next Phase Readiness
- Investigation pipeline requirement coverage now includes INV-05 and INV-06 (parallel fan-out + unified aggregation).
- Phase 2 is ready for closure and handoff into Phase 3 diagnosis planning/execution.
- No blockers carried forward.

---
*Phase: 02-investigation-pipeline*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required file exists on disk: `tests/test_parallel_investigation.py`.
- Verified task commits `a5e8555`, `5afeb58`, and `75f38a2` exist in git history.
