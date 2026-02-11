---
phase: 02-investigation-pipeline
plan: 02
subsystem: api
tags: [python, azure-resource-graph, azure-activity-logs, pydantic, agent-result]

# Dependency graph
requires:
  - phase: 02-01
    provides: Shared `AgentResult` envelope and findings extension points for investigator outputs
provides:
  - Azure Resource Graph wrapper returning normalized object-array rows
  - Azure Activity Logs wrapper returning stable change metadata fields
  - Resource findings models and ResourceAgent implementation with graceful degradation behavior
affects: [02-03, 03-01, 04-01]

# Tech tracking
tech-stack:
  added: [azure-mgmt-resourcegraph, azure-mgmt-resource, azure-mgmt-monitor]
  patterns: [azure-wrapper-normalization, resource-agent-graceful-degradation]

key-files:
  created:
    [
      src/azure/resource_graph.py,
      src/azure/activity_logs.py,
      src/models/resource_findings.py,
      src/agents/resource_agent.py,
      tests/test_resource_agent_smoke.py,
    ]
  modified: [requirements.txt]

key-decisions:
  - "Keep `ResourceFindings.config` optional so degraded runs still return a valid typed envelope."
  - "Resolve resource IDs from nested alert payload keys before falling back to explicit `resource_id` input."

patterns-established:
  - "Azure client wrappers convert SDK responses into stable dict shapes before agent-layer mapping."
  - "Investigator agents degrade with actionable notes instead of raising when Azure setup is missing."

# Metrics
duration: 7 min
completed: 2026-02-11
---

# Phase 2 Plan 2: Resource Agent Investigation Summary

**Resource Agent now correlates Azure Resource Graph configuration and 7-day Activity Log changes into a typed `AgentResult` while degrading gracefully when Azure setup is missing.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-11T02:15:17Z
- **Completed:** 2026-02-11T02:22:46Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Added reusable Azure SDK wrappers for Resource Graph queries and Activity Log retrieval with normalized output shapes.
- Added `ResourceConfig`, `ResourceChange`, and `ResourceFindings` models for typed resource evidence payloads.
- Implemented `ResourceAgent.run(...)` returning `AgentResult[ResourceFindings]` with resource-id discovery and degraded behavior when credentials/config are unavailable.
- Added a smoke test that validates the resource-agent envelope without requiring live Azure credentials.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Azure SDK wrappers for Resource Graph and Activity Logs** - `f2b79fa` (feat)
2. **Task 2: Create Resource findings model** - `4c85cd7` (feat)
3. **Task 3: Implement Resource Agent (returns AgentResult[ResourceFindings])** - `992cc43` (feat)

**Plan metadata:** Pending final docs commit after summary/state updates.

## Files Created/Modified
- `requirements.txt` - Added Azure SDK dependencies for resource graph, resource management, and monitor clients.
- `src/azure/resource_graph.py` - Added `query_resources(...)` wrapper using `ResourceGraphClient.resources(QueryRequest(...))` with object-array format.
- `src/azure/activity_logs.py` - Added `list_activity_logs(...)` wrapper with normalized stable fields (`timestamp`, `caller`, `operation`, `status`, `resource_id`).
- `src/models/resource_findings.py` - Added typed models for resource configuration, resource changes, and aggregate findings.
- `src/agents/resource_agent.py` - Added resource investigation flow with target resource resolution, Azure querying, and graceful degradation.
- `tests/test_resource_agent_smoke.py` - Added non-Azure smoke test asserting `AgentResult` envelope and degraded status behavior.

## Decisions Made
- Made `ResourceFindings.config` optional to keep degraded responses schema-valid even when Resource Graph returns no config.
- Chose recursive alert-payload key scanning (`resource_id`, `resourceId`, `resourceUri`, subscription-like `id`) so the agent can derive target resources from varied alert shapes.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Issues Encountered
- Initial `pytest -q` run failed in `tests/test_history_agent_smoke.py` due a transient `NameError` from concurrent 02-03 branch work; re-running after workspace sync produced a clean pass with no extra 02-02 code changes.

## User Setup Required

None - this plan reuses existing Azure setup expectations from the phase and adds no new manual setup steps.

## Next Phase Readiness
- Resource evidence pipeline is ready for coordinator integration with history findings in `02-03`.
- No blockers carried forward for this plan.

---
*Phase: 02-investigation-pipeline*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist on disk.
- Verified task commits `f2b79fa`, `4c85cd7`, and `992cc43` exist in git history.
