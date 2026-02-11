# TriageForge

Multi-agent system that automatically investigates and remediates Azure cost anomalies before humans join the call.

**Built for:** Microsoft AI Dev Days Hackathon 2026

## What It Does

TriageForge receives Azure Monitor cost alerts and runs a parallel investigation pipeline:

1. **Coordinator Agent** receives the alert and orchestrates the investigation
2. **Cost Analyst** queries Azure Cost Management API to identify top cost drivers
3. **Resource Agent** queries Azure Resource Graph and Activity Logs to find resource details and recent changes
4. **History Agent** searches Azure AI Search (RAG) for similar past incidents
5. **Diagnosis Agent** synthesizes all findings into a root cause hypothesis with confidence score
6. **Remediation Agent** suggests fix actions (e.g., stop VM) with human approval requirement
7. **Human Loop** receives a Slack notification with Approve/Reject/Investigate buttons; approved actions execute automatically

## Architecture

```
Azure Monitor Alert
       ↓
Coordinator Webhook (/webhooks/alert)
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

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# App
APP_ENV=dev
LOG_LEVEL=INFO

# Azure
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_AI_PROJECT_ENDPOINT=<your-foundry-endpoint>

# Slack
SLACK_WEBHOOK_URL=<your-incoming-webhook-url>
SLACK_SIGNING_SECRET=<your-signing-secret>
```

**Where to get values:**
- `AZURE_SUBSCRIPTION_ID`: Azure Portal → Subscriptions → Subscription ID
- `AZURE_AI_PROJECT_ENDPOINT`: Azure AI Foundry → Project endpoint
- `SLACK_WEBHOOK_URL`: Slack App → Incoming Webhooks → Webhook URL
- `SLACK_SIGNING_SECRET`: Slack App → Basic Information → Signing Secret

### 3. Run the Server

```bash
uvicorn web.app:app --app-dir src --host 0.0.0.0 --port 8000
```

The server will listen on:
- Webhook: `POST /webhooks/alert` — receives Azure Monitor alerts
- Health: `GET /health` — checks if server is running
- Slack actions: `POST /webhooks/slack/actions` — handles button clicks

### 4. Trigger a Demo Investigation

Send a realistic Azure Monitor alert payload to the webhook:

```bash
curl -X POST http://localhost:8000/webhooks/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "schemaId": "azureMonitorCommonAlertSchema",
    "data": {
      "essentials": {
        "alertId": "/subscriptions/.../alerts/demo-gpu-spike",
        "alertRule": "GPU VM Cost Spike",
        "severity": "Sev1",
        "signalType": "Metric",
        "monitorCondition": "Fired",
        "monitoringService": "Cost Management",
        "alertTargetIDs": [
          "/subscriptions/.../virtualMachines/gpu-training-vm"
        ],
        "firedDateTime": "2026-02-11T10:00:00Z",
        "description": "GPU VM running for 72 hours"
      },
      "alertContext": {
        "ResourceId": "/subscriptions/.../virtualMachines/gpu-training-vm",
        "costAnomaly": {
          "expectedDailyCost": 12.50,
          "actualDailyCost": 450.00,
          "anomalyFactor": 36.0
        }
      }
    }
  }'
```

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

- **Backend:** FastAPI (Python)
- **Agents:** Async Python with Azure SDK
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
# All tests
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Project Structure

```
incident-war-room/
├── src/
│   ├── agents/           # Coordinator, Cost, Resource, History, Diagnosis, Remediation
│   ├── azure/            # Azure SDK helpers (auth, compute, foundry)
│   ├── execution/        # Remediation execution engine
│   ├── integrations/      # Slack webhook, message formatting
│   ├── models/           # Pydantic models (findings, diagnosis, remediation, approval)
│   ├── storage/           # Cosmos DB, Azure AI Search (History)
│   └── web/              # FastAPI routes, idempotency, settings
├── tests/                # pytest test suite
├── demo/                 # Demo scenario and scripts
├── docs/                 # Architecture diagram (Mermaid + PNG)
├── .planning/            # GSD plans and state
├── requirements.txt        # Python dependencies
└── .env.example          # Environment variables template
```

## License

MIT License — see LICENSE file for details.
