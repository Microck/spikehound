# Spikehound

## What This Is

A multi-agent system that auto-debugs Azure cost anomalies before humans join the call. When Azure costs spike unexpectedly, specialized agents investigate in parallel — analyzing cost data, resource configurations, and historical incidents — then synthesize a diagnosis and suggest remediation. Built for the Microsoft AI Dev Days Hackathon 2026.

## Core Value

**When Azure costs spike, 5 specialized agents investigate in parallel, diagnose the root cause, and suggest fixes — all before a human needs to look at a dashboard.**

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Coordinator Agent that orchestrates investigation
- [ ] Cost Analyst Agent that queries Azure Cost Management API
- [ ] Resource Agent that gets resource configurations and activity logs
- [ ] History Agent that does RAG over past incidents
- [ ] Diagnosis Agent that synthesizes findings into root cause
- [ ] Remediation Agent that suggests fixes (with human approval)
- [ ] Slack/Teams webhook for human notifications
- [ ] 2-minute demo video showing end-to-end flow

### Out of Scope

- Production deployment — hackathon demo only
- Automatic remediation without approval — human-in-the-loop required
- Non-Azure clouds — tight Azure integration only
- Real-time monitoring dashboard — focus on core investigation flow
- Multiple anomaly types — cost anomalies only for MVP

## Context

**Hackathon:** Microsoft AI Dev Days 2026 (Feb 10 - Mar 15, 2026)

**Target Prizes:**
- Primary: Agentic DevOps ($20,000)
- Secondary: Multi-Agent ($10,000)
- Tertiary: Azure Integration ($10,000)

**Niche:** Azure Cost Anomalies (not generic SRE)
- Nobody does this with multi-agent
- Clear business value ($$$)
- Easy to demo (show cost spike → investigation → fix)
- Less crowded than "generic SRE"

**Prior Art:**
- PagerDuty SRE Agent: Single agent, not multi-agent
- Incident.io AI SRE: Closed source, expensive
- Resolve.ai: Enterprise-only

**Differentiation:**
1. Open Source — all competitors are commercial SaaS
2. Microsoft Stack — Foundry + Agent Framework
3. Self-Hosted — runs in YOUR Azure
4. Specialized Agents — 5+ agents with clear roles
5. Transparent Reasoning — show investigation graph

## Constraints

- **Timeline**: 5 weeks (Feb 10 - Mar 15, 2026)
- **Tech Stack**: Python, Microsoft Agent Framework, Azure AI Foundry
- **Model Access**: GPT-4o via Foundry
- **Storage**: Azure Cosmos DB (incidents), Azure AI Search (RAG)
- **Azure APIs**: Cost Management, Resource Graph, Monitor
- **Demo**: 2-minute video required

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Focus on cost anomalies | Differentiated from generic SRE | — Pending |
| 6 specialized agents | Clear separation of concerns | — Pending |
| GPU VM scenario for demo | Easy to stage, clear business impact | — Pending |
| Slack for human loop | Popular, easy webhook integration | — Pending |

---
*Last updated: 2026-02-08 after project initialization*
