# TriageForge Roadmap

## Overview

Multi-agent system that auto-debugs Azure cost anomalies before humans join the call. Built for Microsoft AI Dev Days Hackathon 2026.

**Timeline:** 5 weeks (Feb 10 - Mar 15, 2026)
**Target Prizes:** Agentic DevOps ($20k), Multi-Agent ($10k), Azure Integration ($10k)

---

## Phase 1: Foundation

**Goal:** Basic infrastructure + Cost Analyst Agent working
**Status:** Complete (2026-02-11)

**Duration:** ~1 week

**Requirements Covered:**
- FOUND-01: Azure subscription with Cost Management enabled
- FOUND-02: Foundry project initialized with Agent Framework
- FOUND-03: Coordinator Agent skeleton with state management
- FOUND-04: Cost Analyst Agent queries Cost Management API
- FOUND-05: Basic data model for cost anomalies

**Success Criteria:**
1. Azure subscription accessible with Cost Management enabled
2. Foundry project running with Agent Framework SDK
3. Coordinator Agent can receive alert webhooks
4. Cost Analyst Agent retrieves cost data for last 7 days
5. Anomaly data model defined and validated

**Deliverables:**
- `src/agents/coordinator.py`
- `src/agents/cost_analyst.py`
- `src/models/anomaly.py`
- `infra/foundry_config.yaml`

---

## Phase 2: Investigation Pipeline

**Goal:** 3 agents (Cost, Resource, History) working in parallel

**Duration:** ~1 week

**Requirements Covered:**
- INV-01: Resource Agent queries Azure Resource Graph
- INV-02: Resource Agent gets activity logs for resource changes
- INV-03: History Agent with Azure AI Search for RAG
- INV-04: History Agent stores and retrieves past incidents
- INV-05: Coordinator spawns agents in parallel
- INV-06: Coordinator collects and aggregates findings

**Success Criteria:**
1. Resource Agent retrieves resource configurations
2. Resource Agent shows who/what modified resources
3. History Agent RAG returns similar past incidents
4. Coordinator spawns 3 agents in parallel
5. Unified findings object aggregated from all agents

**Deliverables:**
- `src/agents/resource_agent.py`
- `src/agents/history_agent.py`
- `src/storage/incident_store.py`
- `src/models/findings.py`

---

## Phase 3: Diagnosis & Remediation

**Goal:** End-to-end investigation with suggestions

**Duration:** ~1 week

**Requirements Covered:**
- DIAG-01: Diagnosis Agent synthesizes multi-agent findings
- DIAG-02: Diagnosis Agent produces root cause hypothesis
- DIAG-03: Diagnosis Agent provides confidence scoring
- DIAG-04: Remediation Agent suggests fix actions

**Success Criteria:**
1. Diagnosis Agent synthesizes findings from all 3 investigators
2. Root cause hypothesis generated with explanation
3. Confidence score 0-100% provided
4. Remediation Agent suggests at least one fix action

**Deliverables:**
- `src/agents/diagnosis_agent.py`
- `src/agents/remediation_agent.py`
- `src/models/diagnosis.py`

---

## Phase 4: Human Loop

**Goal:** Slack notifications with approval flow

**Duration:** ~1 week

**Requirements Covered:**
- HUMAN-01: Slack webhook for investigation notifications
- HUMAN-02: Human-readable summary in Slack message
- HUMAN-03: Approval buttons (Approve/Reject/Investigate)
- HUMAN-04: Remediation execution with approval

**Success Criteria:**
1. Slack webhook sends notification on investigation complete
2. Summary is readable by non-technical user
3. Interactive buttons work (Approve/Reject)
4. Approved fix is executed automatically

**Deliverables:**
- `src/integrations/slack.py`
- `src/execution/remediation.py`

---

## Phase 5: Demo & Submit

**Goal:** Polished demo and documentation

**Duration:** ~1 week

**Requirements Covered:**
- DEMO-01: Staged cost anomaly scenario (GPU VM left running)
- DEMO-02: 2-minute video showing full investigation flow
- DEMO-03: README with architecture and setup instructions
- DEMO-04: Architecture diagram showing all 6 agents

**Success Criteria:**
1. GPU VM scenario reproducible on demand
2. Video under 2 minutes, shows full flow
3. README includes setup, architecture, usage
4. Architecture diagram shows all 6 agents clearly

**Deliverables:**
- `demo/scenario.md`
- `demo/video.mp4`
- `README.md`
- `docs/architecture.png`

---

## Phase Dependencies

```
Phase 1 (Foundation) → Phase 2 (Investigation) → Phase 3 (Diagnosis) → Phase 4 (Human Loop) → Phase 5 (Demo)
```

---

## Coverage Validation

All 22 v1 requirements are mapped:
- Phase 1: FOUND-01 to FOUND-05 (5 requirements)
- Phase 2: INV-01 to INV-06 (6 requirements)
- Phase 3: DIAG-01 to DIAG-04 (4 requirements)
- Phase 4: HUMAN-01 to HUMAN-04 (4 requirements)
- Phase 5: DEMO-01 to DEMO-04 (4 requirements)

**Total: 22/22 requirements covered (100%)**

---

*Last updated: 2026-02-08*
