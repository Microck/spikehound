---
phase: 02-investigation-pipeline
verified: 2026-02-11T02:42:43Z
status: passed
score: 9/9 must-haves verified
human_verification_approved: 2026-02-11
human_verification:
  - test: "Live Resource Graph + Activity Logs path"
    expected: "ResourceAgent returns status=ok with populated resource config and recent change rows for a known Azure resource"
    why_human: "Requires real Azure subscription, RBAC, and service responses that cannot be validated offline"
  - test: "Live Cosmos DB + Azure AI Search history retrieval"
    expected: "HistoryAgent persists incident records and returns at least one similar incident with status=ok"
    why_human: "Requires cloud credentials, provisioned index/container, and seeded incident data"
---

# Phase 2: Investigation Pipeline Verification Report

**Phase Goal:** 3 agents (Cost, Resource, History) working in parallel
**Verified:** 2026-02-11T02:42:43Z
**Status:** passed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | All investigator agents return a consistent result envelope | ✓ VERIFIED | `CostAnalystAgent.run` returns `AgentResult` in `src/agents/cost_analyst.py:27`; `ResourceAgent.run` in `src/agents/resource_agent.py:30`; `HistoryAgent.run` in `src/agents/history_agent.py:39`. |
| 2 | Coordinator can merge multiple agent findings deterministically | ✓ VERIFIED | Deterministic sort key in `UnifiedFindings.merge` at `src/models/findings.py:50` and `_result_sort_key` at `src/models/findings.py:117`; determinism test in `tests/test_findings_merge.py:31`. |
| 3 | Incident persistence and similarity search are split behind separate interfaces | ✓ VERIFIED | `IncidentStore` interface in `src/storage/incident_store.py:23`; `IncidentSearch` interface in `src/storage/incident_search.py:12`; composition used in `src/agents/history_agent.py:46`. |
| 4 | Resource Agent can query Resource Graph for a resource id | ✓ VERIFIED | Resource KQL + query call in `src/agents/resource_agent.py:171` and `src/agents/resource_agent.py:179`; wrapper uses `ResourceGraphClient` in `src/azure/resource_graph.py:22`. |
| 5 | Resource Agent can retrieve Activity Logs for recent changes | ✓ VERIFIED | Activity log call in `src/agents/resource_agent.py:221`; Azure Monitor list call in `src/azure/activity_logs.py:90`. |
| 6 | History Agent can retrieve similar incidents via `IncidentSearch` (or fallback) | ✓ VERIFIED | Search invocation in `src/agents/history_agent.py:65`; backend/fallback selection in `src/agents/history_agent.py:123`; degraded fallback test in `tests/test_history_agent_smoke.py:32`. |
| 7 | Incident records can be stored and read back via `IncidentStore` (or fallback) | ✓ VERIFIED | Persist via `store.put` in `src/agents/history_agent.py:55`; read via `store.get` in `src/agents/history_agent.py:249`; Cosmos implementation in `src/storage/cosmos_incident_store.py:60`. |
| 8 | Coordinator spawns Cost, Resource, and History agents in parallel | ✓ VERIFIED | Parallel fan-out with `asyncio.gather` in `src/agents/coordinator.py:57` and threaded execution in `src/agents/coordinator.py:97`; barrier-based proof in `tests/test_parallel_investigation.py:39`. |
| 9 | Coordinator aggregates all results into `UnifiedFindings` | ✓ VERIFIED | Aggregation call in `src/agents/coordinator.py:78`; webhook returns merged JSON in `src/web/app.py:30`; response schema test in `tests/test_parallel_investigation.py:147`. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/models/agent_protocol.py` | Base protocol for agent inputs/outputs | ✓ VERIFIED | Exists, 36 lines, substantive enums/models, imported by all investigator agents (`src/agents/coordinator.py:15`). |
| `src/models/findings.py` | Unified findings merge and schema | ✓ VERIFIED | Exists, 128 lines, deterministic merge logic (`src/models/findings.py:43`), used by coordinator (`src/agents/coordinator.py:78`). |
| `src/storage/incident_store.py` | Persistence interface + fallback implementation | ✓ VERIFIED | Exists, 60 lines, abstract interface plus memory implementation, wired in history agent (`src/agents/history_agent.py:19`). |
| `src/storage/incident_search.py` | Similarity search interface + fallback implementation | ✓ VERIFIED | Exists, 68 lines, local search uses store candidates (`src/storage/incident_search.py:32`), wired in history agent (`src/agents/history_agent.py:17`). |
| `src/azure/resource_graph.py` | Resource Graph client wrapper | ✓ VERIFIED | Exists, 39 lines, concrete SDK query (`src/azure/resource_graph.py:30`), called by resource agent (`src/agents/resource_agent.py:179`). |
| `src/azure/activity_logs.py` | Activity Logs client wrapper | ✓ VERIFIED | Exists, 94 lines, concrete Azure Monitor query (`src/azure/activity_logs.py:90`), called by resource agent (`src/agents/resource_agent.py:221`). |
| `src/agents/resource_agent.py` | Resource investigation agent | ✓ VERIFIED | Exists, 276 lines, returns `AgentResult`, handles degraded/error paths, exercised by smoke test (`tests/test_resource_agent_smoke.py:10`). |
| `src/storage/cosmos_incident_store.py` | Cosmos-backed `IncidentStore` implementation | ✓ VERIFIED | Exists, 111 lines, `put/get/list_recent` implemented, selected by history agent when env is configured (`src/agents/history_agent.py:133`). |
| `src/storage/ai_search_incident_search.py` | AI Search-backed `IncidentSearch` implementation | ✓ VERIFIED | Exists, 97 lines, `SearchClient.search` call (`src/storage/ai_search_incident_search.py:42`), selected by history agent (`src/agents/history_agent.py:134`). |
| `src/agents/history_agent.py` | History investigation agent | ✓ VERIFIED | Exists, 286 lines, persists + searches with fallback behavior, exercised by smoke tests (`tests/test_history_agent_smoke.py:21`). |
| `src/agents/coordinator.py` | Parallel orchestration + aggregation | ✓ VERIFIED | Exists, 216 lines, timeout-protected concurrent fan-out and merge, validated by deterministic parallel test (`tests/test_parallel_investigation.py:39`). |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/models/findings.py` | `src/models/agent_protocol.py` | Typed `AgentResult` envelope | WIRED | `UnifiedFindings.results` uses `dict[AgentName, AgentResult[Any]]` in `src/models/findings.py:33`. |
| `src/storage/incident_search.py` | `src/storage/incident_store.py` | Local fallback candidate scan | WIRED | `LocalIncidentSearch` reads from `store.list_recent(...)` in `src/storage/incident_search.py:32`. |
| `src/agents/resource_agent.py` | `src/azure/resource_graph.py` | Resource Graph KQL query | WIRED | Agent calls `query_resources(...)` in `src/agents/resource_agent.py:179`; wrapper executes SDK call in `src/azure/resource_graph.py:30`. |
| `src/agents/resource_agent.py` | `src/azure/activity_logs.py` | Activity Logs retrieval | WIRED | Agent calls `list_activity_logs(...)` in `src/agents/resource_agent.py:221`; wrapper executes Azure call in `src/azure/activity_logs.py:90`. |
| `src/agents/history_agent.py` | `src/storage/incident_store.py` | `put/get` incident persistence | WIRED | Writes via `store.put` (`src/agents/history_agent.py:55`) and reads via `store.get` (`src/agents/history_agent.py:249`). |
| `src/agents/history_agent.py` | `src/storage/incident_search.py` | `search_similar` | WIRED | History search call in `src/agents/history_agent.py:65`; fallback `LocalIncidentSearch` constructed in `src/agents/history_agent.py:130`. |
| `src/storage/ai_search_incident_search.py` | `azure.search.documents` | `SearchClient.search` | WIRED | SDK invocation exists in `src/storage/ai_search_incident_search.py:42`. |
| `src/agents/coordinator.py` | Cost/Resource/History agents | Async fan-out + merge | WIRED | Concurrent gather at `src/agents/coordinator.py:57`, merge at `src/agents/coordinator.py:78`. |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
| --- | --- | --- |
| INV-01 Resource Agent queries Azure Resource Graph | ✓ SATISFIED (code-level) | Live Azure execution still requires human verification. |
| INV-02 Resource Agent gets activity logs for resource changes | ✓ SATISFIED (code-level) | Live Azure execution still requires human verification. |
| INV-03 History Agent with Azure AI Search for RAG | ✓ SATISFIED (code-level) | Live Azure Search verification requires provisioned index/credentials. |
| INV-04 History Agent stores and retrieves past incidents | ✓ SATISFIED (code-level) | Live Cosmos verification requires provisioned container/credentials. |
| INV-05 Coordinator spawns agents in parallel | ✓ SATISFIED | Deterministic barrier-based test passes (`tests/test_parallel_investigation.py:39`). |
| INV-06 Coordinator collects and aggregates findings | ✓ SATISFIED | Unified merge + webhook schema validated (`tests/test_parallel_investigation.py:147`). |

### Anti-Patterns Found

No blocker/warning anti-patterns found in phase-modified source and test files.

Scan evidence:
- No `TODO/FIXME/placeholder/not implemented` markers in `src/` or phase tests.
- No empty handler stubs or placeholder JSX/API responses.

### Human Verification Required

Approved by user on 2026-02-11. Live Azure checks were deferred for later validation.

### 1. Resource Graph + Activity Logs Live Check

**Test:** Run `ResourceAgent.run(...)` with valid `AZURE_SUBSCRIPTION_ID` and a known resource id.
**Expected:** `status=ok`, `data.config` populated, and `data.recent_changes` contains normalized entries.
**Why human:** Requires real Azure RBAC access and service-side data.

### 2. Cosmos + AI Search Live RAG Check

**Test:** Configure all vars from `.planning/phases/02-investigation-pipeline/02-USER-SETUP.md`, seed at least one incident, then run `HistoryAgent.run(...)`.
**Expected:** `status=ok` with one or more `matches` including stable `id` (and optional `score`).
**Why human:** Requires external cloud services, credentials, and index/container correctness.

### Gaps Summary

No code-level gaps found for Phase 2 must-haves. Parallel orchestration and unified aggregation are implemented and test-verified. Remaining work is live-cloud validation only.

Verification command evidence:
- `. .venv/bin/activate && PYTHONPATH=src pytest -q`
- Result: `17 passed in 0.77s`

---

_Verified: 2026-02-11T02:42:43Z_
_Verifier: Claude (gsd-verifier)_
