# Spikehound

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Spikehound is a multi-agent incident workflow for Azure cost anomalies.

It ingests an alert payload, fans out to specialized investigators (cost, resource config, history), synthesizes a diagnosis, and proposes remediation with a human approval gate.

<!-- top-readme: begin -->
## Installation

- [`dotnet/IncidentWarRoom.sln`](dotnet/IncidentWarRoom.sln)
- [`dotnet/src/IncidentWarRoom.Functions/IncidentWarRoom.Functions.csproj`](dotnet/src/IncidentWarRoom.Functions/IncidentWarRoom.Functions.csproj)

## Testing

- [`dotnet/tests/IncidentWarRoom.Core.Tests/IncidentWarRoom.Core.Tests.csproj`](dotnet/tests/IncidentWarRoom.Core.Tests/IncidentWarRoom.Core.Tests.csproj)

## Support / Community

## Changelog / Releases

## Roadmap

- [`.planning/ROADMAP.md`](.planning/ROADMAP.md)
<!-- top-readme: end -->

## Features

- Parallel investigation pipeline with clear agent roles
- Webhook ingestion for alert payloads
- Optional human-in-the-loop notifications (Slack / Discord)
- Safe-by-default remediation: explicit approval required
- Runs as a .NET 8 Azure Functions app (isolated worker)

## Quickstart (local)

Prereqs:
- .NET 8 SDK
- Azure Functions Core Tools v4 (`func`)

```bash
cp .env.example .env
set -a; source .env; set +a

cd dotnet
dotnet test
cd src/IncidentWarRoom.Functions
func start
```

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

Copy `.env.example` to `.env` and set what you need (the Functions host reads standard process environment variables).

If you keep config in `.env`, load it into your shell before `func start`:

```bash
set -a; source .env; set +a
```

Notes:
- The demo is designed to run without Azure credentials by default (agents return structured degraded results).
- Real Slack interactive callbacks require a publicly reachable URL (ngrok or similar).
- Do not commit `.env` (it is gitignored). If you ever paste real webhook URLs or keys into git, rotate them.

## Architecture

![Spikehound Architecture](docs/architecture.png)

Diagram sources:
- Mermaid: `docs/architecture.mmd`
- Rendered image: `docs/architecture.png`

## Development

```bash
cd dotnet
dotnet test
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
