---
phase: 02-investigation-pipeline
plan: 03
subsystem: api
tags: [python, azure-cosmos, azure-ai-search, history-agent, rag]

# Dependency graph
requires:
  - phase: 02-01
    provides: Shared `AgentResult` envelope and incident store/search interfaces
provides:
  - Cosmos-backed incident persistence implementation
  - Azure AI Search-backed incident similarity lookup implementation
  - History Agent with graceful degradation when Azure backends are missing
affects: [02-02, 02-04, 03-01]

# Tech tracking
tech-stack:
  added: [azure-cosmos, azure-search-documents]
  patterns: [env-driven-backend-selection, graceful-degradation-with-stable-envelope]

key-files:
  created:
    [
      src/storage/cosmos_incident_store.py,
      src/storage/ai_search_incident_search.py,
      src/models/history_findings.py,
      src/agents/history_agent.py,
      tests/test_history_agent_smoke.py,
      .planning/phases/02-investigation-pipeline/02-USER-SETUP.md,
    ]
  modified: [requirements.txt]

key-decisions:
  - "Use Cosmos/AI Search only when all required env vars are configured, otherwise degrade safely with empty matches."
  - "Allow Cosmos database/container auto-creation only in dev/local/test environments; require pre-provisioning elsewhere."

patterns-established:
  - "History agent always returns AgentResult[HistoryFindings] and never crashes on missing backend configuration."
  - "Backend wrappers validate credentials/configuration with clear runtime messages for coordinator-safe degradation paths."

# Metrics
duration: 8 min
completed: 2026-02-11
---

# Phase 2 Plan 3: History Agent Backends Summary

**History investigation now supports Cosmos incident persistence and Azure AI Search similarity lookup while returning a stable degraded envelope when backend credentials are unavailable.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-11T02:15:33Z
- **Completed:** 2026-02-11T02:23:46Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Added `CosmosIncidentStore` with explicit env validation, incident CRUD methods, and dev-safe container provisioning rules.
- Added `AzureAISearchIncidentSearch` that uses `SearchClient.search(...)` and validates required AI Search env vars at call time.
- Implemented `HistoryAgent` and history findings models that persist alerts, query similar incidents, and preserve a stable degraded response shape.
- Added smoke tests that verify history agent envelope behavior and graceful degradation when Azure backend env vars are missing.
- Generated Phase 2 user setup instructions for Cosmos/AI Search secret collection and dashboard checks.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Cosmos DB IncidentStore implementation** - `f40b766` (feat)
2. **Task 2: Add Azure AI Search IncidentSearch implementation** - `af35473` (feat)
3. **Task 3: Implement History Agent (returns AgentResult[HistoryFindings])** - `941c1cf` (feat)

**Plan metadata:** Pending final docs commit after summary/state updates.

## Files Created/Modified
- `requirements.txt` - Added Cosmos and AI Search SDK dependencies.
- `src/storage/cosmos_incident_store.py` - Cosmos-backed `IncidentStore` implementation.
- `src/storage/ai_search_incident_search.py` - Azure AI Search-backed `IncidentSearch` implementation.
- `src/models/history_findings.py` - Pydantic models for history query output and similar incident entries.
- `src/agents/history_agent.py` - History agent orchestration and graceful degradation behavior.
- `tests/test_history_agent_smoke.py` - Smoke tests for envelope correctness and degraded fallback behavior.
- `.planning/phases/02-investigation-pipeline/02-USER-SETUP.md` - Human-required external setup checklist for Azure services.

## Decisions Made
- Used an env-gated backend selection path: default agent construction attempts Azure backends only when all required vars are present, otherwise degrades with empty matches.
- Kept Cosmos provisioning strict outside dev/local/test to avoid accidental production resource creation while preserving local developer ergonomics.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing Azure AI Search dependency during task verification**
- **Found during:** Task 2 (Add Azure AI Search IncidentSearch implementation)
- **Issue:** Verification import failed because `azure-search-documents` was newly added to `requirements.txt` but not yet installed in the virtualenv.
- **Fix:** Re-ran dependency installation (`pip install -r requirements.txt -r requirements-dev.txt`) before re-running the Task 2 verification command.
- **Files modified:** None (environment-only fix)
- **Verification:** `PYTHONPATH=src python3 -c "from storage.ai_search_incident_search import AzureAISearchIncidentSearch; print('ok')"`
- **Committed in:** `af35473` (Task 2 commit)

**2. [Rule 1 - Bug] Fixed NameError in incident record creation path**
- **Found during:** Task 3 (Implement History Agent)
- **Issue:** `_build_record` was a static method but referenced `self._unique(...)`, causing a runtime `NameError` in tests.
- **Fix:** Replaced instance reference with `HistoryAgent._unique(...)` for static-safe tag deduplication.
- **Files modified:** `src/agents/history_agent.py`
- **Verification:** `PYTHONPATH=src pytest -q`
- **Committed in:** `941c1cf` (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes were required for task completion and runtime correctness; no scope creep introduced.

## Authentication Gates

None.

## Issues Encountered
None.

## User Setup Required

**External services require manual configuration.** See `02-USER-SETUP.md` for:
- Environment variables to add
- Azure dashboard checks
- Verification commands

## Next Phase Readiness
- History backend contracts and graceful fallback behavior are in place.
- Ready to continue the remaining Investigation plan (`02-04`).
- No blockers carried forward.

---
*Phase: 02-investigation-pipeline*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist on disk.
- Verified task commits `f40b766`, `af35473`, and `941c1cf` exist in git history.
