---
phase: 03-diagnosis-remediation
plan: 01
subsystem: api
tags: [python, pydantic, azure-openai, diagnosis, fallback]

# Dependency graph
requires:
  - phase: 02-04
    provides: UnifiedFindings aggregation and AgentResult orchestration
provides:
  - Foundry LLM wrapper that centralizes Azure chat completions with typed configuration and response errors
  - Diagnosis schema with strict confidence bounds and test coverage
  - Diagnosis agent that synthesizes findings with LLM and deterministic degraded fallback logic
affects: [03-02, 03-03, 04-01]

# Tech tracking
tech-stack:
  added: []
  patterns: [single-entrypoint-llm-wrapper, deterministic-diagnosis-fallback]

key-files:
  created:
    [
      src/llm/foundry_client.py,
      src/models/diagnosis.py,
      src/agents/diagnosis_agent.py,
      tests/test_confidence_score.py,
    ]
  modified: [src/llm/__init__.py]

key-decisions:
  - "Centralized all Foundry API call details in `FoundryClient.complete_json` to keep diagnosis logic mockable and deterministic."
  - "Treat missing Foundry configuration and response/validation failures as degraded mode, not hard failures, so diagnosis still ships offline."
  - "Implemented deterministic fallback confidence tiers aligned to plan rules (80/60/55/40) for stable behavior in demos and tests."

patterns-established:
  - "LLM output contract enforcement: parse JSON then re-validate with pydantic model before agent returns."
  - "Diagnosis fallback composes actionable evidence, alternatives, and risks even when external LLM is unavailable."

# Metrics
duration: 9 min
completed: 2026-02-11
---

# Phase 3 Plan 1: Diagnosis Agent Summary

**Diagnosis synthesis now converts unified investigator findings into a structured root-cause hypothesis with confidence scoring and deterministic offline fallback.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-11T04:01:08Z
- **Completed:** 2026-02-11T04:10:21Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added a Foundry client wrapper for Azure OpenAI-compatible chat completions with strict env validation and typed response failures.
- Added diagnosis domain models (`RootCauseHypothesis`, `Diagnosis`) with strict confidence range validation and coverage for invalid values.
- Implemented `DiagnosisAgent.run(...)` to produce model-backed diagnosis output via Foundry and deterministic degraded fallback rules when LLM is unavailable.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Foundry LLM client wrapper (minimal, mockable)** - `3374ff8` (feat)
2. **Task 2: Create diagnosis model and confidence scoring helper** - `95c01af` (feat)
3. **Task 3: Implement Diagnosis Agent (UnifiedFindings -> Diagnosis)** - `a9cd344` (feat)

**Plan metadata:** Pending docs commit for summary/state updates.

## Files Created/Modified
- `src/llm/foundry_client.py` - Foundry REST wrapper with typed configuration/response errors and JSON schema validation.
- `src/llm/__init__.py` - Exports Foundry client and typed errors for consistent imports.
- `src/models/diagnosis.py` - Defines diagnosis payload and confidence constraints.
- `tests/test_confidence_score.py` - Guards confidence validation against out-of-range values.
- `src/agents/diagnosis_agent.py` - Adds LLM-backed diagnosis synthesis plus deterministic fallback rules.

## Decisions Made
- Used a thin `FoundryClient` abstraction rather than embedding HTTP calls in the agent to keep diagnosis logic testable and isolated from transport details.
- Standardized Foundry failures into degraded diagnosis behavior so phase requirements remain achievable without cloud credentials.
- Prioritized deterministic fallback evidence and confidence outputs over heuristics with randomness to keep demo behavior reproducible.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

Azure AI Foundry environment variables are required for live LLM synthesis:
- `FOUNDRY_ENDPOINT`
- `FOUNDRY_API_KEY`
- `FOUNDRY_MODEL`

Without these variables the Diagnosis Agent runs in deterministic degraded fallback mode.

## Next Phase Readiness
- Diagnosis requirement coverage for DIAG-01/DIAG-02/DIAG-03 is now in place through schema-backed diagnosis output and confidence scoring.
- Ready to continue with `03-03-PLAN.md` for remaining diagnosis/remediation phase work.
- No blockers carried forward.

---
*Phase: 03-diagnosis-remediation*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist: `src/llm/foundry_client.py`, `src/models/diagnosis.py`, `src/agents/diagnosis_agent.py`, `tests/test_confidence_score.py`.
- Verified task commits exist in git history: `3374ff8`, `95c01af`, `a9cd344`.
