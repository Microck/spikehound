---
phase: 03-diagnosis-remediation
plan: 02
subsystem: api
tags: [python, pydantic, remediation, safety, agent-result]

# Dependency graph
requires:
  - phase: 02-04
    provides: Unified findings aggregation and shared AgentResult envelope
provides:
  - Structured remediation models with safe-by-default human approval requirements
  - Remediation agent that converts diagnosis context into deterministic fix suggestions
  - Remediation suggestion tests validating non-empty output and approval safety
affects: [03-03, 04-01]

# Tech tracking
tech-stack:
  added: []
  patterns: [deterministic-remediation-rules, safe-by-default-approval]

key-files:
  created:
    [
      src/models/remediation.py,
      src/agents/remediation_agent.py,
      tests/test_remediation_suggestions.py,
    ]
  modified: []

key-decisions:
  - "Encoded `human_approval_required` as `Literal[True]` so every remediation action is safe-by-default."
  - "Implemented deterministic remediation rules for GPU VM + no-shutdown and unexpected VM runtime scenarios."
  - "Added a guaranteed `notify_owner` fallback action so remediation plans are never empty."

patterns-established:
  - "Remediation actions are always represented as typed Pydantic objects before handoff to human approval flows."
  - "Diagnosis text is normalized into rule triggers to keep remediation suggestions deterministic in offline/demo mode."

# Metrics
duration: 7 min
completed: 2026-02-11
---

# Phase 3 Plan 2: Remediation Suggestion Agent Summary

**Remediation planning now produces typed, safe-by-default action suggestions from diagnosis context, with deterministic VM shutdown heuristics and test coverage for approval gating.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-11T04:01:04Z
- **Completed:** 2026-02-11T04:08:40Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added a remediation domain model (`RemediationActionType`, `RemediationAction`, `RemediationPlan`) with non-empty plan validation.
- Implemented `RemediationAgent.run(unified_findings, diagnosis)` with deterministic rules and optional Foundry-assisted generation.
- Added tests that enforce non-empty remediation suggestions and mandatory human approval on every action.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define remediation models (actions, safety, approval)** - `74be249` (feat)
2. **Task 2: Implement Remediation Agent (Diagnosis -> RemediationPlan)** - `2dde7f7` (feat)
3. **Task 3: Add tests for remediation suggestion behavior** - `7030b49` (test)

**Plan metadata:** Pending docs commit for summary/state updates.

## Files Created/Modified
- `src/models/remediation.py` - Defines remediation action/plan schema with strict safety defaults.
- `src/agents/remediation_agent.py` - Maps diagnosis signals to structured remediation actions and returns `AgentResult[RemediationPlan]`.
- `tests/test_remediation_suggestions.py` - Verifies remediation suggestions are non-empty and `human_approval_required` is always true.

## Decisions Made
- Enforced `human_approval_required` as always true at the schema layer instead of relying on caller discipline.
- Prioritized deterministic rule-based suggestions for demo reliability while allowing optional Foundry enhancement via dependency injection.
- Guaranteed at least one suggestion (`notify_owner`) when no rule matches so downstream approval flow always has structured output.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

None - no additional external service or secret setup required for this plan.

## Next Phase Readiness
- Remediation suggestions now satisfy DIAG-04 requirements for structured, approvable actions.
- Coordinator integration plan (`03-03`) can consume `RemediationAgent` output directly as `AgentResult` data.
- No blockers carried forward.

---
*Phase: 03-diagnosis-remediation*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist on disk: `src/models/remediation.py`, `src/agents/remediation_agent.py`, `tests/test_remediation_suggestions.py`.
- Verified task commits `74be249`, `2dde7f7`, and `7030b49` exist in git history.
