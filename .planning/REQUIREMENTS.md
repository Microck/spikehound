# Requirements

## v1 Requirements

### Foundation (FOUND)

- [x] **FOUND-01**: Azure subscription with Cost Management enabled
- [x] **FOUND-02**: Foundry project initialized with Agent Framework
- [x] **FOUND-03**: Coordinator Agent skeleton with state management
- [x] **FOUND-04**: Cost Analyst Agent queries Cost Management API
- [x] **FOUND-05**: Basic data model for cost anomalies

### Investigation (INV)

- [x] **INV-01**: Resource Agent queries Azure Resource Graph
- [x] **INV-02**: Resource Agent gets activity logs for resource changes
- [x] **INV-03**: History Agent with Azure AI Search for RAG
- [x] **INV-04**: History Agent stores and retrieves past incidents
- [x] **INV-05**: Coordinator spawns agents in parallel
- [x] **INV-06**: Coordinator collects and aggregates findings

### Diagnosis (DIAG)

- [x] **DIAG-01**: Diagnosis Agent synthesizes multi-agent findings
- [x] **DIAG-02**: Diagnosis Agent produces root cause hypothesis
- [x] **DIAG-03**: Diagnosis Agent provides confidence scoring
- [x] **DIAG-04**: Remediation Agent suggests fix actions

### Human Loop (HUMAN)

- [x] **HUMAN-01**: Slack webhook for investigation notifications
- [x] **HUMAN-02**: Human-readable summary in Slack message
- [x] **HUMAN-03**: Approval buttons (Approve/Reject/Investigate)
- [x] **HUMAN-04**: Remediation execution with approval

### Demo (DEMO)

- [x] **DEMO-01**: Staged cost anomaly scenario (GPU VM left running)
- [ ] **DEMO-02**: 2-minute video showing full investigation flow *(manual recording/upload pending)*
- [x] **DEMO-03**: README with architecture and setup instructions
- [x] **DEMO-04**: Architecture diagram showing all 6 agents

---

## v2 Requirements

### Enhancements

- [ ] Azure Monitor alert webhook trigger (real alerts)
- [ ] Multiple anomaly types (not just cost spikes)
- [ ] Web dashboard for visualization
- [ ] Fix verification (confirm cost returned to normal)

---

## Out of Scope

- **Production deployment** — hackathon demo only
- **Auto-remediation without approval** — human-in-the-loop required
- **Non-Azure clouds** — Azure only
- **Real-time dashboard** — focus on investigation flow
- **Multiple alert types** — cost anomalies only

---

## Traceability

| REQ-ID | Phase | Status | Success Criteria |
|--------|-------|--------|------------------|
| FOUND-01 | Phase 1: Foundation | Complete | Azure subscription accessible |
| FOUND-02 | Phase 1: Foundation | Complete | Foundry project running |
| FOUND-03 | Phase 1: Foundation | Complete | Coordinator accepts alerts |
| FOUND-04 | Phase 1: Foundation | Complete | Cost data retrieved for last 7 days |
| FOUND-05 | Phase 1: Foundation | Complete | Anomaly model defined |
| INV-01 | Phase 2: Investigation | Complete | Resource config retrieved |
| INV-02 | Phase 2: Investigation | Complete | Activity logs show who changed what |
| INV-03 | Phase 2: Investigation | Complete | RAG returns similar incidents |
| INV-04 | Phase 2: Investigation | Complete | Incidents stored and retrievable |
| INV-05 | Phase 2: Investigation | Complete | 3 agents run in parallel |
| INV-06 | Phase 2: Investigation | Complete | Unified findings object produced |
| DIAG-01 | Phase 3: Diagnosis | Complete | Findings synthesized |
| DIAG-02 | Phase 3: Diagnosis | Complete | Root cause identified |
| DIAG-03 | Phase 3: Diagnosis | Complete | Confidence score 0-100% |
| DIAG-04 | Phase 3: Diagnosis | Complete | At least one fix suggested |
| HUMAN-01 | Phase 4: Human Loop | Complete | Slack message received |
| HUMAN-02 | Phase 4: Human Loop | Complete | Summary is readable |
| HUMAN-03 | Phase 4: Human Loop | Complete | Buttons work |
| HUMAN-04 | Phase 4: Human Loop | Complete | Fix executed on approval |
| DEMO-01 | Phase 5: Demo | Complete | Scenario reproducible |
| DEMO-02 | Phase 5: Demo | Pending | Video under 2 minutes *(manual recording/upload pending)* |
| DEMO-03 | Phase 5: Demo | Complete | README complete |
| DEMO-04 | Phase 5: Demo | Complete | Diagram shows all agents |

**Coverage:** 22/22 requirements mapped (100%)
