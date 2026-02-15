# Spikehound

Multi-agent system that automatically investigates and remediates Azure cost anomalies before humans join the call.

**Built for:** Microsoft AI Dev Days Hackathon 2026

## What It Does

Spikehound receives Azure Monitor cost alerts and runs a parallel investigation pipeline:

1. **Coordinator Agent** receives the alert and orchestrates the investigation
2. **Cost Analyst** queries Azure Cost Management API to identify top cost drivers
3. **Resource Agent** queries Azure Resource Graph and Activity Logs to find resource details and recent changes
4. **History Agent** searches Azure AI Search (RAG) for similar past incidents
5. **Diagnosis Agent** synthesizes all findings into a root cause hypothesis with confidence score
6. **Remediation Agent** suggests fix actions (e.g., stop VM) with human approval requirement
7. **Human Loop** receives a Slack notification with Approve/Reject/Investigate buttons; approved actions execute automatically

## Architecture

![Spikehound Architecture](docs/architecture.png)

```
Azure Monitor Alert
       ↓
 Coordinator Webhook (/api/webhooks/alert)
       ↓
  ┌────┬─────────────────────────┬─────────────┐
  ↓    │                         │              │
Cost   │    History                │
Agent  │    Agent                  │
  ↓    │    ↓                     │
Cost   │  Similar Incidents        │
Findings│  (Azure AI Search)       │
  ↓    │                         │
  └────┴─────────────────────────┴─────────────┘
              ↓
        Unified Findings
              ↓
      Diagnosis Agent
              ↓
    Root Cause (85% confidence)
              ↓
    Remediation Agent
              ↓
  Remediation Plan (requires approval)
              ↓
     Slack Notification
  (Approve/Reject/Investigate buttons)
              ↓
    [Human clicks Approve]
              ↓
      Remediation Execution
  (Azure Compute: stop_vm)
              ↓
    Follow-up Slack Message
```

## Quick Start

### Primary Stack: .NET 8 + Azure Functions (isolated)

This repo has been migrated to a “perfect stack” Functions app under `dotnet/`.

### 1. Run Tests (no external services)

```bash
cd dotnet
/home/ubuntu/.dotnet/dotnet test
```

### 2. Run the Functions app locally

Prereqs:
- .NET 8 (already available here as `/home/ubuntu/.dotnet/dotnet`)
- Azure Functions Core Tools v4 (`func`) for local hosting

```bash
cd dotnet/src/IncidentWarRoom.Functions
func start
```

Local base URL (default): `http://localhost:7071`

Endpoints:
- `POST /api/webhooks/alert` (alert ingestion)
- `GET /api/health`
- `POST /api/webhooks/slack/actions`
- `POST /api/webhooks/discord/interactions`

### 3. Configure env (optional)

The hackathon demo runs without Azure creds by default (agents return structured degraded results).

Optional environment variables:
- `INCIDENT_WR_CLOUD_ENABLED=true` (enables cloud-backed agents when implemented/configured)
- `SLACK_WEBHOOK_URL` (send Slack notifications)
- `SLACK_SIGNING_SECRET` (verify Slack interactive callbacks)
- `DISCORD_WEBHOOK_URL` (send Discord notifications)
- `DISCORD_INTERACTIONS_PUBLIC_KEY` (verify Discord interactions)

Safety toggles:
- `INCIDENT_WR_ALLOW_REMEDIATION_EXECUTION=true` (still requires explicit human approval)

---

Legacy implementation note:

- The previous Python/FastAPI implementation has been archived privately (repo: `Microck/legacy-python-archives`, path: `spikehound/`) and removed from this repo to keep the primary stack clean.

## Demo

For a complete, reproducible demo scenario, see [demo/scenario.md](demo/scenario.md).

The demo shows:
- A staged GPU VM cost anomaly (\$450/day vs \$12.50/day baseline)
- Multi-agent investigation pipeline in action
- Slack notification with approval buttons
- Remediation execution (stop VM) after approval

## Safety

### Human Approval Required

All remediation actions require explicit human approval via Slack buttons before execution.

**Safe-by-default:**
- Actions are marked with `human_approval_required=True`
- Only "Approve" triggers execution
- "Reject" and "Investigate More" only record the decision

### No Production Deployment

**Out of scope:**
- Auto-scaling configurations
- Production CI/CD pipelines
- Multi-tenant deployment
- Persistent state storage (approvals are in-memory for demo)

## Limitations

- **Slack interactivity:** Server must be publicly accessible (via ngrok or similar) to receive real Slack button clicks
- **Azure credentials:** Requires service principal or Azure CLI auth; managed identity only works on Azure VMs
- **Foundry dependency:** Diagnosis Agent degrades gracefully when Azure AI Foundry is unavailable
- **Demo-only:** Approval records are stored in-memory; production would need persistent storage

## Tech Stack

- **Backend:** Azure Functions (isolated worker, .NET 8)
- **Orchestration:** Durable Functions (fan-out/fan-in agent model)
- **Core:** C# library (`dotnet/src/IncidentWarRoom.Core`) with parsing/signatures/coordinator logic
- **Tests:** xUnit (`cd dotnet && dotnet test`)
- **Azure Services:**
  - Cost Management API
  - Resource Graph
  - Activity Logs
  - Azure AI Search (optional)
  - Cosmos DB (optional for History)
  - Azure Compute (remediation)
- **Integration:** Slack Incoming Webhooks + Interactive Buttons
- **AI:** Azure AI Foundry (Diagnosis Agent)

## Development

### Running Tests

```bash
cd dotnet
/home/ubuntu/.dotnet/dotnet test
```

### Project Structure

```
incident-war-room/
├── dotnet/               # .NET 8 Azure Functions + Core library + tests
├── demo/                 # Demo scenario and scripts
├── docs/                 # Architecture diagram (Mermaid + PNG)
├── .planning/            # GSD plans and state
└── .env.example          # Environment variables template
```

## License

MIT License — see LICENSE file for details.
