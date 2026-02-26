<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/brand/logo-horizontal-dark.svg">
  <img alt="Spikehound" src="docs/brand/logo-horizontal.svg" width="640">
</picture>

# Spikehound

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Spikehound is a multi-agent incident workflow for Azure cost anomalies.

It ingests an alert payload, fans out to specialized investigators (cost, resource config, history), synthesizes a diagnosis, and proposes remediation with a human approval gate.

## Quickstart (local)

Prereqs:
- .NET 8 SDK
- Azure Functions Core Tools v4 (`func`)
- Azurite (`azurite`) for local `AzureWebJobsStorage=UseDevelopmentStorage=true`

```bash
cp .env.example .env
set -a; source .env; set +a

mkdir -p /tmp/azurite
azurite --silent --location /tmp/azurite --debug /tmp/azurite/debug.log

cd dotnet
dotnet test
cd src/Spikehound.Functions
func start
```

```bash
curl -sS http://localhost:7071/api/health
```

## Installation

Repo layout:
- Solution: `dotnet/Spikehound.sln`
- Function app: `dotnet/src/Spikehound.Functions/Spikehound.Functions.csproj`

Optional integration prerequisites:
- ngrok (or equivalent tunnel) for Slack/Discord callback endpoints in local development
- Slack app with Incoming Webhook + Interactivity enabled
- Discord application with Interactions Endpoint URL configured
- Discord bot token + channel id (recommended for interactive Discord buttons)

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
- `SPIKEHOUND_USE_DURABLE=false` (inline) / `true` (durable scheduling)
- `SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION=false` (safe default) / `true` (execute approved remediation actions)

When execution is disabled, approvals are still recorded and queued through Durable orchestration, but outcomes are marked as skipped by configuration.

Interactive callback configuration:
- Slack callbacks: set `SLACK_SIGNING_SECRET` and configure Slack Interactivity Request URL to `/api/webhooks/slack/actions`
- Discord callbacks: set `DISCORD_INTERACTIONS_PUBLIC_KEY` and configure Discord Interactions Endpoint URL to `/api/webhooks/discord/interactions`
- For reliable Discord interactive buttons, configure `DISCORD_BOT_TOKEN` + `DISCORD_CHANNEL_ID` (webhook-only Discord mode sends plain notifications and may not deliver interactive button callbacks)

## API Reference

Local base URL (default): `http://localhost:7071`

- `POST /api/webhooks/alert`
- `GET /api/health`
- `POST /api/webhooks/slack/actions`
- `POST /api/webhooks/discord/interactions`

Behavior notes:
- Inline mode: returns `200` with an investigation report payload
- Durable mode: returns `202` after scheduling orchestration
- Approved Slack/Discord decisions schedule `RemediationExecutionOrchestrator` for remediation execution
- Duplicate approve decisions for the same investigation are deduplicated (no second orchestration instance)
- Slack notifications include interactive Approve/Reject/Investigate buttons
- Discord notifications include interactive buttons when bot mode is configured (`DISCORD_BOT_TOKEN` + `DISCORD_CHANNEL_ID`)

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

## CI/CD

GitHub Actions workflow: `.github/workflows/ci-cd.yml`

- `Build And Unit Tests`: builds `dotnet/Spikehound.sln` and runs tests.
- `Local E2E And Edge Cases`: boots Azurite + Functions host and verifies:
  - inline mode success path and idempotent duplicate path
  - invalid JSON (`400`)
  - unsigned Slack/Discord callbacks (`401`)
  - durable mode scheduling response (`202` with `instanceId`)
- `Deploy Azure Function App`: runs on pushes to `main` only when deployment settings are configured.

To enable deployment, configure these repository settings:

- Repository variable: `SPIKEHOUND_FUNCTIONAPP_NAME`
- Repository secret: `SPIKEHOUND_FUNCTIONAPP_PUBLISH_PROFILE`

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
