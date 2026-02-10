# TriageForge

> Multi-agent system that auto-investigates Azure cost anomalies before humans join the call

## Vision

Every month, Azure bills surprise teams. A single misconfigured VM can cost thousands. **TriageForge** is a multi-agent system that automatically detects cost anomalies, investigates root causes, and suggests remediation - all before a human even opens the alert.

## One-Liner

"A swarm of AI agents that investigates Azure cost spikes and tells you exactly what went wrong."

## Target Prize

- **Primary:** Agentic DevOps ($20,000)
- **Secondary:** Best Multi-Agent System ($10,000)
- **Tertiary:** Best Azure Integration ($10,000)

## The Problem

Azure cost anomalies are hard to debug:
- Cost data is buried in dashboards
- Finding the specific resource takes time
- Understanding WHY costs spiked requires investigation
- Manual process delays response

## The Solution

TriageForge - A multi-agent investigation system:
1. **Detects** cost anomalies via Azure Monitor alerts
2. **Dispatches** specialized agents in parallel
3. **Investigates** resources, activity logs, history
4. **Diagnoses** root cause with confidence
5. **Suggests** remediation with human approval

## Why This Wins

1. **Differentiated niche** - Cost anomalies, not generic SRE
2. **Multi-agent showcase** - 6 specialized agents
3. **Microsoft stack** - Deep Azure integration
4. **Open source** - All competitors are commercial
5. **Business value** - Cost savings = immediate ROI
6. **Human-in-the-loop** - Responsible AI

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | Microsoft Agent Framework |
| Model Hosting | Microsoft Foundry (GPT-4o) |
| Cost Data | Azure Cost Management API |
| Resource Data | Azure Resource Graph |
| Metrics | Azure Monitor |
| Alerts | Azure Monitor Alerts |
| History | Azure AI Search (RAG) |
| Storage | Azure Cosmos DB |
| Runtime | Python 3.11+ |

## Architecture

```
              ┌─────────────────┐
              │  Azure Monitor  │
              │  Cost Alerts    │
              └────────┬────────┘
                       │
           ┌───────────▼───────────┐
           │   COORDINATOR AGENT   │
           └───────────┬───────────┘
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
[Cost Analyst]   [Resource Agent]  [History Agent]
     │                 │                 │
     └─────────────────┼─────────────────┘
                       ▼
           ┌───────────────────────┐
           │   DIAGNOSIS AGENT     │
           └───────────┬───────────┘
                       ▼
           ┌───────────────────────┐
           │  REMEDIATION AGENT    │
           └───────────┬───────────┘
                       ▼
           ┌───────────────────────┐
           │   HUMAN APPROVAL      │
           └───────────────────────┘
```

## Agents

| Agent | Role |
|-------|------|
| Coordinator | Orchestrates investigation, manages state |
| Cost Analyst | Queries Cost Management API, finds anomaly |
| Resource Agent | Gets resource config, activity logs |
| History Agent | RAG over past incidents |
| Diagnosis Agent | Synthesizes findings into root cause |
| Remediation Agent | Suggests fixes, executes with approval |

## Demo Script (2 minutes)

1. **[0:00-0:15]** "Every month, Azure bills surprise teams..."
2. **[0:15-0:30]** Alert fires: Cost spike detected
3. **[0:30-1:00]** Agents investigate in parallel (split screen)
4. **[1:00-1:20]** Diagnosis: "GPU VM missing auto-shutdown, 94% confidence"
5. **[1:20-1:40]** Slack notification with [Approve] button
6. **[1:40-1:55]** Human approves, fix applied, cost normalized
7. **[1:55-2:00]** "TriageForge: Multi-agent cost investigation"

## Constraints

- Must use Microsoft Agent Framework
- Must use Azure Cost Management API
- Must have human approval for remediation
- Demo must be under 2 minutes
- Repo must be public by Feb 10

## Out of Scope (v1)

- Real-time monitoring (alert-triggered only)
- Non-cost incidents
- Full dashboard UI
- Multiple cloud providers
