# Spikehound

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Spikehound is a multi-agent incident workflow for Azure cost anomalies.

It ingests an alert payload, fans out to specialized investigators (cost, resource config, history), synthesizes a diagnosis, and proposes remediation with a human approval gate.

## Features

- Parallel investigation pipeline with clear agent roles
- Webhook ingestion for alert payloads
- Optional human-in-the-loop notifications (Slack / Discord)
- Safe-by-default remediation: explicit approval required
- Runs as a .NET 8 Azure Functions app (isolated worker)

## Getting Started

Prereqs:
- .NET 8
- Azure Functions Core Tools v4 (`func`) for local hosting

1. Run tests:

```bash
cd dotnet
/home/ubuntu/.dotnet/dotnet test
```

2. Start the Functions host:

```bash
cd dotnet/src/IncidentWarRoom.Functions
func start
```

3. Confirm the service is up:

```bash
curl -sS http://localhost:7071/api/health
```

## Usage

Trigger an investigation using the demo payload in `demo/scenario.md`.

High-level flow:

```text
alert -> /api/webhooks/alert -> parallel agents -> diagnosis -> remediation plan
```

## API

Local base URL (default): `http://localhost:7071`

- `POST /api/webhooks/alert` (alert ingestion)
- `GET /api/health`
- `POST /api/webhooks/slack/actions`
- `POST /api/webhooks/discord/interactions`

Alert endpoint behavior:
- Inline mode (default): returns `200` with the investigation report payload.
- Durable mode (`INCIDENT_WR_USE_DURABLE=true`): returns `202` after scheduling orchestration.

## Configuration

Copy `.env.example` to `.env` and set what you need.

Notes:
- The demo is designed to run without Azure credentials by default (agents return structured degraded results).
- Real Slack interactive callbacks require a publicly reachable URL (ngrok or similar).

## Architecture

![Spikehound Architecture](docs/architecture.png)

Diagram sources:
- Mermaid: `docs/architecture.mmd`
- Rendered image: `docs/architecture.png`

## Development

```bash
cd dotnet
/home/ubuntu/.dotnet/dotnet test
```

## Security

This project may execute remediation actions when enabled. Treat credentials and webhooks as sensitive.

- Prefer running in a dedicated demo subscription.
- Do not point remediation at production resources.

## Contributing

Issues and pull requests are welcome.

## License

Apache-2.0 (see `LICENSE`).

## Origin

Spikehound was built during a hackathon and optimized for a reproducible demo, but the repository is structured as a normal OSS project.
