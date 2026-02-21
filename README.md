# Spikehound

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Spikehound is a multi-agent incident workflow for Azure cost anomalies.

It ingests an alert payload, fans out to specialized investigators (cost, resource config, history), synthesizes a diagnosis, and proposes remediation with a human approval gate.

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

## Installation

Repo layout:
- Solution: `dotnet/IncidentWarRoom.sln`
- Function app: `dotnet/src/IncidentWarRoom.Functions/IncidentWarRoom.Functions.csproj`

TODO: document any optional prerequisites (Slack/Discord interactive callbacks, ngrok).

## Usage

Trigger an investigation using the demo payload in `demo/scenario.md`.

High-level flow:

```text
alert -> /api/webhooks/alert -> parallel agents -> diagnosis -> remediation plan
```

TODO: add one end-to-end example request + response (redact secrets).

## Configuration

Copy `.env.example` to `.env` and load it before running `func start`:

```bash
set -a; source .env; set +a
```

Key toggles:
- `INCIDENT_WR_USE_DURABLE=false` (inline) / `true` (durable scheduling)

TODO: document which env vars are required for each mode.

## API Reference

Local base URL (default): `http://localhost:7071`

- `POST /api/webhooks/alert`
- `GET /api/health`
- `POST /api/webhooks/slack/actions`
- `POST /api/webhooks/discord/interactions`

Behavior notes:
- Inline mode: returns `200` with an investigation report payload
- Durable mode: returns `202` after scheduling orchestration

## Architecture

![Spikehound Architecture](docs/architecture.png)

Diagram source:
- `docs/architecture.mmd`

## Development

```bash
cd dotnet
dotnet test
```

TODO: add formatting/linting and debugging notes.

## Testing

```bash
cd dotnet
dotnet test
```

## Contributing

Issues and pull requests are welcome.

## Support / Community

TODO: add Issues/Discussions links.

## Security

This project may execute remediation actions when enabled. Treat credentials and webhooks as sensitive.

TODO: document a demo-safe posture and how to disable remediation.

## License

Apache-2.0 (see `LICENSE`).

## Changelog / Releases

TODO: link to GitHub Releases or add `CHANGELOG.md`.

## Roadmap

- `.planning/ROADMAP.md`
