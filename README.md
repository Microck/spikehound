# Spikehound

Spikehound is a multi-agent system that investigates Azure cost anomalies and proposes safe-by-default remediation before humans join the call.

Built for: Microsoft AI Dev Days Hackathon 2026
Categories: Agentic DevOps, Best Multi-Agent System, Best Azure Integration
Demo video: <paste hosted link>

## What It Does

Spikehound receives an alert (Azure Monitor common schema payload) and runs a parallel investigation:

- Coordinator: receives the alert and orchestrates the run
- Cost Analyst: identifies top cost drivers via Azure Cost Management (optional live)
- Resource Agent: pulls resource details and recent changes (optional live)
- History Agent: searches for similar incidents (optional live)
- Diagnosis Agent: synthesizes findings into a root-cause hypothesis + confidence
- Remediation Agent: proposes actions that require human approval
- Human loop: posts to Slack (Approve/Reject/Investigate); approved actions can execute

## Architecture

![Spikehound Architecture](docs/architecture.png)

```text
Alert -> /api/webhooks/alert -> parallel agents -> diagnosis -> remediation plan
  -> Slack message (buttons) -> approved execution -> follow-up message
```

## Quickstart (Local)

This project uses a "perfect stack" .NET 8 Azure Functions app under `dotnet/`.

Prereqs:
- .NET 8
- Azure Functions Core Tools v4 (`func`) to run locally

1. Run unit tests (no external services):

```bash
cd dotnet
/home/ubuntu/.dotnet/dotnet test
```

2. Start the Functions app:

```bash
cd dotnet/src/IncidentWarRoom.Functions
func start
```

3. Confirm health:

```bash
curl -sS http://localhost:7071/api/health
```

4. Trigger the demo investigation:
- Follow `demo/scenario.md` (manual `curl` payload).

## Endpoints

Local base URL (default): `http://localhost:7071`

- `POST /api/webhooks/alert` (alert ingestion)
- `GET /api/health`
- `POST /api/webhooks/slack/actions`
- `POST /api/webhooks/discord/interactions`

Alert endpoint behavior:
- Inline mode (default): returns `200` with the investigation report payload.
- Durable mode (`INCIDENT_WR_USE_DURABLE=true`): returns `202` after scheduling orchestration.

## Configuration

See `.env.example`.

Notes:
- The demo is designed to run without Azure credentials by default (agents return structured degraded results).
- Real Slack button clicks require the Functions host to be publicly reachable (ngrok or similar).

## Verification

Automated:

```bash
cd dotnet
/home/ubuntu/.dotnet/dotnet test
```

Manual (live integrations):
- Start Functions (`func start`) and hit `/api/health`.
- Run the end-to-end scenario in `demo/scenario.md`.
- Click Slack buttons in a real Slack channel and confirm callbacks are verified + recorded.

## Safety

Safe-by-default invariants:
- Remediation actions require explicit human approval.
- Execution is gated behind runtime flags (even after approval).

Out of scope for v1:
- Production hardening and persistent approvals store

## Repo Layout

```text
incident-war-room/
  dotnet/    .NET 8 Azure Functions app + core library + tests
  demo/      demo scenario + staging/cleanup scripts
  docs/      architecture diagram source + rendered image
  .planning/ build plans and state
  .env.example
```

## License

Apache-2.0 (see `LICENSE`).
