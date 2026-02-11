---
phase: 01-foundation
plan: 04
subsystem: testing
tags: [python, fastapi, pytest, azure-ai-projects, azure-ai-foundry]

# Dependency graph
requires:
  - phase: 01-01
    provides: FastAPI webhook app scaffold and runtime dependency baseline
  - phase: 01-02
    provides: Azure credential patterns and Cost Management smoke workflow
provides:
  - One-command local dev launcher that boots uvicorn with dependency bootstrap
  - Pytest harness with `pythonpath = src` and FastAPI smoke coverage
  - Foundry endpoint configuration and read-only SDK smoke check script
affects: [01-03, 02-01, 02-02]

# Tech tracking
tech-stack:
  added: [azure-ai-projects]
  patterns: [idempotent-dev-bootstrap-script, pytest-pythonpath-harness, read-only-foundry-connectivity-check]

key-files:
  created:
    [
      pytest.ini,
      scripts/dev.sh,
      tests/test_smoke.py,
      infra/foundry_config.yaml,
      src/azure/foundry.py,
      scripts/foundry_smoke.py,
      .planning/phases/01-foundation/01-USER-SETUP.md,
    ]
  modified: [requirements.txt, .env.example]

key-decisions:
  - "Use `uvicorn web.app:app` with `--app-dir src` so local startup works without manual `PYTHONPATH` export."
  - "Keep Foundry smoke validation read-only by listing at most one agent and avoiding create/update calls."

patterns-established:
  - "Developer bootstrap scripts should create `.venv` when missing and remain safe to rerun."
  - "External service checks should ship with non-destructive smoke scripts plus a matching USER-SETUP checklist."

# Metrics
duration: 4 min
completed: 2026-02-11
---

# Phase 1 Plan 4: Developer Ergonomics + Foundry Smoke Summary

**Local developer startup/testing is now one command, and Foundry project connectivity can be validated safely with a read-only Agent Framework SDK smoke script.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T01:47:30Z
- **Completed:** 2026-02-11T01:52:05Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Added `scripts/dev.sh` to bootstrap the virtualenv, install dependencies, and run the FastAPI app via `uvicorn web.app:app`.
- Added `pytest.ini` and `tests/test_smoke.py` so test runs import `src` modules cleanly and verify app boot + `/health` behavior.
- Added Foundry configuration and SDK integration pieces (`AZURE_AI_PROJECT_ENDPOINT`, `infra/foundry_config.yaml`, `src/azure/foundry.py`).
- Added `scripts/foundry_smoke.py` that authenticates through `DefaultAzureCredential` and performs a read-only list-agents call.
- Generated `.planning/phases/01-foundation/01-USER-SETUP.md` for required human-side Foundry endpoint setup.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dev script + pytest harness + smoke test** - `e9eea95` (feat)
2. **Task 2: Add Foundry config + non-destructive smoke script** - `8f12f00` (feat)

**Plan metadata:** Pending final docs commit after summary/state updates.

## Files Created/Modified
- `scripts/dev.sh` - Idempotent local startup script for venv bootstrap + `uvicorn` launch.
- `pytest.ini` - Sets `pythonpath = src` and test discovery defaults.
- `tests/test_smoke.py` - Verifies FastAPI app import and `/health` endpoint response.
- `requirements.txt` - Adds `azure-ai-projects` for Foundry project client support.
- `.env.example` - Documents `AZURE_AI_PROJECT_ENDPOINT`.
- `infra/foundry_config.yaml` - Non-secret Foundry endpoint placeholder wired to env var.
- `src/azure/foundry.py` - Exposes endpoint validation and `AIProjectClient` factory.
- `scripts/foundry_smoke.py` - Read-only Foundry connectivity check (lists up to one agent).
- `.planning/phases/01-foundation/01-USER-SETUP.md` - Human checklist for endpoint retrieval and smoke verification.

## Decisions Made
- Kept the dev launcher self-contained (`.venv` creation + dependency install + app startup) to reduce setup friction for later phase work.
- Implemented Foundry smoke behavior as read-only listing to avoid side effects during validation.

## Deviations from Plan

None - plan executed exactly as written.

## Authentication Gates

None.

## Issues Encountered

None.

## User Setup Required

External setup is required for Foundry endpoint retrieval. See `01-USER-SETUP.md`.

## Next Phase Readiness
- Developer bootstrap/test ergonomics are ready for ongoing agent implementation work.
- Foundry dependency + helper layer is in place; once `AZURE_AI_PROJECT_ENDPOINT` is set, the read-only smoke script can validate access quickly.
- Remaining Foundation work is still gated on completing `01-03-PLAN.md`.

---
*Phase: 01-foundation*
*Completed: 2026-02-11*

## Self-Check: PASSED

- Verified required files exist on disk (`scripts/dev.sh`, `pytest.ini`, `tests/test_smoke.py`, `infra/foundry_config.yaml`, `src/azure/foundry.py`, `scripts/foundry_smoke.py`, `.planning/phases/01-foundation/01-USER-SETUP.md`).
- Verified task commits `e9eea95` and `8f12f00` exist in git history.
