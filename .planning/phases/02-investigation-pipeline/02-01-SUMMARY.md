---
phase: 02-investigation-pipeline
plan: 01
subsystem: api
tags: [python, pydantic, agent-protocol, incident-search]

# Dependency graph
requires:
  - phase: 01-03
    provides: Findings contract and coordinator orchestration seam
provides:
  - Shared `AgentResult` envelope and investigator status enums
  - Unified findings merge model for deterministic multi-agent aggregation
  - Incident persistence interface separated from similarity search interface
affects: [02-02, 02-03, 02-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [typed-agent-result-envelope, deterministic-findings-merge, store-search-boundary]

key-files:
  created:
    [
      src/models/agent_protocol.py,
      tests/test_findings_merge.py,
      src/storage/incident_store.py,
      src/storage/incident_search.py,
    ]
  modified: [src/models/findings.py]

key-decisions:
  - "Keep `InvestigationFindings` backward-compatible while adding optional resource/history sections for upcoming agents."
  - "Use deterministic sorting inside `UnifiedFindings.merge` so aggregate output is stable regardless of input order."

patterns-established:
  - "Agent contracts use `AgentName` + `AgentStatus` enums and a single `AgentResult` envelope."
  - "History tooling composes separate `IncidentStore` and `IncidentSearch` interfaces with a local fallback implementation."

# Metrics
duration: 3 min
completed: 2026-02-11
---

# Phase 2 Plan 1: Investigation Pipeline Contracts Summary

**Shared agent protocol contracts, deterministic findings merge logic, and decoupled incident store/search interfaces are now in place for parallel investigator integration.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-11T02:09:03Z
- **Completed:** 2026-02-11T02:12:28Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added `AgentName`, `AgentStatus`, and generic `AgentResult` models so all investigator agents can return a single typed envelope.
- Extended findings models with optional `resource_findings`/`history_findings` and introduced `UnifiedFindings.merge(...)` for deterministic coordinator aggregation.
- Added `IncidentStore` and `IncidentSearch` interfaces plus in-memory fallback implementations to keep persistence and similarity search concerns separated.
- Added merge-focused tests that assert order-independent aggregation and per-agent status/error retention.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define agent protocol models (inputs, outputs, status)** - `e3dbf12` (feat)
2. **Task 2: Expand Findings model to support multiple investigators** - `3c2cc27` (feat)
3. **Task 3: Add incident store + incident search interfaces (memory stubs)** - `ff6ae6b` (feat)

**Plan metadata:** Pending final docs commit after summary/state updates.

## Files Created/Modified
- `src/models/agent_protocol.py` - Defines shared investigator name/status enums and the common `AgentResult` envelope.
- `src/models/findings.py` - Adds new findings sections and `UnifiedFindings.merge` deterministic aggregation helper.
- `tests/test_findings_merge.py` - Validates merge determinism and per-agent status/error preservation.
- `src/storage/incident_store.py` - Adds `IncidentRecord` plus store interface and in-memory store implementation.
- `src/storage/incident_search.py` - Adds search interface and deterministic local keyword-overlap fallback.

## Decisions Made
- Preserved existing `InvestigationFindings` shape while adding optional sections to avoid breaking current webhook/coordinator integrations.
- Made merge ordering deterministic via canonical sort keys so coordinator output is stable across parallel-agent completion order.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Ready for `02-02-PLAN.md` with protocol and storage/search seams now established.
- No blockers carried forward from this plan.

---
*Phase: 02-investigation-pipeline*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist on disk.
- Verified task commits `e3dbf12`, `3c2cc27`, and `ff6ae6b` exist in git history.
