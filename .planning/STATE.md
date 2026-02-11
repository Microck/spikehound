# TriageForge - Project State

## Current Position

Phase: 4 of 5 (Human Loop)
Plan: 1 of 4
Status: In progress
Last activity: 2026-02-11 - Completed 04-01 slack notification integration plan
Progress: ███████░░░ 12/18 plans complete (67%)

## Current Status

**Current Phase:** Human Loop (Phase 4)
**Next Action:** Execute 04-02 approval interaction plan (`/gsd-execute-phase 4`)

---

## Phase Status

| Phase | Name | Status | Progress |
|-------|------|--------|----------|
| 1 | Foundation | Complete | 4/4 plans complete, 5/5 requirements validated |
| 2 | Investigation | Complete | 4/4 plans complete, 6/6 requirements code-verified |
| 3 | Diagnosis | Complete | 3/3 plans complete, 4/4 requirements code-verified |
| 4 | Human Loop | In Progress | 1/4 plans complete |
| 5 | Demo | Not Started | 0/3 plans complete |

---

## Decisions

| Phase-Plan | Decision | Rationale |
|------------|----------|-----------|
| 01-01 | Keep `src/azure/` without `__init__.py` | Avoids shadowing Azure SDK namespace imports (`azure.identity`, etc.) |
| 01-01 | Keep env loading non-blocking at startup | Allows local FastAPI boot without requiring secrets during early scaffolding |
| 01-02 | Use `DefaultAzureCredential` for both Azure CLI and service principal auth paths | Keeps auth helper side-effect free while supporting local smoke runs and CI-style credentials |
| 01-02 | Restrict Cost Management grouping to `ResourceId` and parse `PreTaxCost` fallback | Matches live Azure Cost Management API behavior and keeps smoke verification reliable |
| 01-03 | Return structured findings even when Azure config is missing | Keeps webhook path stable by surfacing credential/query issues in `notes` instead of failing request handling |
| 01-04 | Run local app with `uvicorn web.app:app --app-dir src` from a single bootstrap script | Eliminates repeated local setup friction and keeps startup command stable across contributors |
| 01-04 | Keep Foundry validation read-only by listing at most one agent in smoke checks | Verifies endpoint/auth connectivity without mutating project resources |
| 02-01 | Keep a shared `AgentResult` envelope (`AgentName`/`AgentStatus`) for all investigator outputs | Lets coordinator aggregate multi-agent results without hardcoded per-agent return shapes |
| 02-01 | Separate incident persistence (`IncidentStore`) from similarity search (`IncidentSearch`) behind interfaces | Preserves swappable Azure backends while keeping deterministic local fallback behavior |
| 02-02 | Keep `ResourceFindings.config` optional in degraded outcomes | Ensures resource investigations still return a schema-valid payload when config lookup fails |
| 02-02 | Resolve target resource IDs via recursive payload key scanning before fallback input | Handles heterogeneous alert payload shapes without hardcoded coordinator coupling |
| 02-03 | Use env-gated backend selection for History Agent | Enables Cosmos/AI Search when configured while keeping deterministic degraded behavior otherwise |
| 02-03 | Restrict Cosmos resource auto-creation to dev/local/test | Prevents accidental production-side provisioning while preserving local ergonomics |
| 02-04 | Run coordinator fan-out with `asyncio.gather` + `asyncio.to_thread` and timeout-to-error conversion | Guarantees parallel investigator start while preserving full aggregation even on slow/failing branches |
| 02-04 | Keep `UnifiedFindings.results` as canonical payload with legacy top-level fields for transition compatibility | Avoids breaking existing consumers/tests while moving webhook contract to multi-agent aggregation |
| 03-01 | Centralize Foundry call details in `FoundryClient.complete_json` with typed config/response errors | Keeps diagnosis logic mockable and deterministic while isolating Azure OpenAI request shape in one place |
| 03-01 | Degrade to deterministic diagnosis fallback when Foundry is unavailable or response parsing fails | Ensures diagnosis remains actionable offline and during missing credentials scenarios |
| 03-01 | Use deterministic confidence tiers (80/60/55/40) tied to explicit fallback rules | Keeps diagnosis behavior reproducible for demo and test workflows |
| 03-02 | Enforce `human_approval_required` as `Literal[True]` in remediation actions | Guarantees remediation suggestions stay safe-by-default and require explicit human approval |
| 03-02 | Use deterministic diagnosis-to-action rules for GPU VM no-shutdown and unexpected runtime cases | Keeps remediation behavior reliable in offline/demo runs without LLM dependency |
| 03-02 | Always emit a fallback `notify_owner` action when no deterministic infrastructure action matches | Ensures remediation plans are never empty for downstream approval workflows |
| 03-03 | Introduce `InvestigationReport` as the coordinator/webhook contract | Preserves unified investigator findings while exposing diagnosis/remediation outputs in one stable response envelope |
| 03-03 | Run diagnosis/remediation via coordinator timeout/error coercion path after investigator fan-out | Keeps degraded and error statuses structured as AgentResults instead of surfacing webhook failures |
| 04-01 | Keep Slack delivery best-effort and non-blocking | Webhook callers should always receive the investigation report even if chat delivery fails |
| 04-01 | Format Slack notifications as `{text, blocks}` from investigation reports | Supports readable fallback text plus richer Slack channel rendering without changing the report contract |
| 04-01 | Trigger Slack send immediately after report generation in `/webhooks/alert` | Aligns notification timing with completed investigations while preserving the existing HTTP response payload |

---

## Blockers/Concerns Carried Forward

None.

---

## Recent Activity

| Date | Activity |
|------|----------|
| 2026-02-11 | Completed 04-01 human-loop plan with Slack webhook client, report formatter, and webhook-triggered Slack send integration plus formatter test coverage |
| 2026-02-11 | Completed 03-03 coordinator integration plan with full webhook report schema, deterministic local e2e pipeline test, and manual smoke validation of cost/resource/history/diagnosis/remediation output sections |
| 2026-02-11 | Completed 03-01 diagnosis plan with Foundry client wrapper, diagnosis schema, and deterministic diagnosis-agent fallback logic |
| 2026-02-11 | Completed 03-02 remediation plan with structured safe-by-default action models, remediation agent, and behavior tests |
| 2026-02-11 | Phase 2 verification accepted; live Azure validation deferred by approval |
| 2026-02-11 | Completed 02-04 parallel coordinator plan with concurrent cost/resource/history orchestration, timeout-safe aggregation, unified webhook response, and deterministic barrier-based parallel test |
| 2026-02-11 | Completed 02-03 history backend plan with Cosmos incident store, Azure AI Search lookup, graceful History Agent fallback, and smoke coverage |
| 2026-02-11 | Completed 02-02 resource investigation plan with Azure Resource Graph/Activity Logs wrappers, typed resource findings models, and Resource Agent smoke coverage |
| 2026-02-11 | Completed 02-01 investigation pipeline contracts plan with agent protocol models, deterministic findings merge tests, and incident store/search interfaces |
| 2026-02-11 | Phase 1 verification accepted; Foundry live endpoint check deferred by approval |
| 2026-02-11 | Completed 01-04 foundation ergonomics/foundry plan with dev launcher, pytest smoke harness, and read-only Foundry SDK smoke script |
| 2026-02-11 | Completed 01-03 foundation vertical slice (webhook -> coordinator -> cost analyst -> findings) with pytest and manual webhook smoke verification |
| 2026-02-11 | Completed 01-02 foundation plan with Azure cost smoke verification and anomaly model validation |
| 2026-02-11 | Completed 01-01 scaffold plan with atomic task commits and verification |
| 2026-02-08 | Project initialized, requirements defined, roadmap created |

---

## Session Continuity

- Last session: 2026-02-11T17:48:17Z
- Stopped at: Completed 04-01 slack notification integration plan
- Resume file: `.planning/phases/04-human-loop/04-02-PLAN.md`

---

*Last updated: 2026-02-11*
