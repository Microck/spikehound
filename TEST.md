# Spikehound - Verification and Showcase Guide

Goal: run a complete local verification (unit + E2E + edge cases), then run an optional real Azure side-effect demo.

Use this guide from the repo root (`incident-war-room`).

## 0) Repo sanity

```bash
cd projects/incident-war-room
git status --porcelain
```

Expected: clean output for tracked files.

## 1) Tooling sanity

```bash
dotnet --version
func --version
azurite --version
az --version || true
curl --version
```

Expected: all commands return versions.

## 2) Configure environment

```bash
cd projects/incident-war-room
cp .env.example .env
set -a; source .env; set +a
```

For inline mode, ensure `.env` has:
- `SPIKEHOUND_USE_DURABLE=false`

For safe local validation, ensure `.env` has:
- `SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION=false`

For Slack + Discord interactive callbacks, configure:
- `SLACK_WEBHOOK_URL`
- `SLACK_SIGNING_SECRET`
- `DISCORD_INTERACTIONS_PUBLIC_KEY`
- Either:
  - `DISCORD_BOT_TOKEN` + `DISCORD_CHANNEL_ID` (recommended, reliable Discord buttons)
  - or `DISCORD_WEBHOOK_URL` (notification-only fallback; interactive Discord callbacks may not fire)

## 2.1) One-time Slack + Discord app setup

Slack:
1. Create Slack app in your workspace.
2. Enable Incoming Webhooks and copy webhook URL into `SLACK_WEBHOOK_URL`.
3. Copy App Signing Secret into `SLACK_SIGNING_SECRET`.
4. Enable Interactivity (Request URL added in Section 4 after ngrok starts).

Discord:
1. Create Discord application in Developer Portal.
2. Copy Public Key into `DISCORD_INTERACTIONS_PUBLIC_KEY`.
3. Recommended: create a bot, install it to your server, and set:
   - `DISCORD_BOT_TOKEN`
   - `DISCORD_CHANNEL_ID` (target text channel id)
4. Optional fallback: set `DISCORD_WEBHOOK_URL` for non-interactive notification delivery.

## 3) Automated tests (.NET)

```bash
cd projects/incident-war-room/dotnet
dotnet test
```

Expected: all tests pass.

## 3.1) Fast pass/fail command (optional)

If you want one quick confidence check before recording:

```bash
cd dotnet
dotnet build Spikehound.sln -nologo -clp:Summary && dotnet test Spikehound.sln
```

Expected: build success and all tests passing.

## 4) Start local dependencies

Terminal 1 (storage emulator):

```bash
mkdir -p /tmp/azurite
azurite --silent --location /tmp/azurite --debug /tmp/azurite/debug.log
```

Terminal 2 (Functions host in inline mode):

```bash
cd projects/incident-war-room
set -a; source .env; set +a

cd dotnet/src/Spikehound.Functions
func start
```

If port 7071 is already busy, stop old `func` processes first.

Terminal 3 (public callback tunnel for Slack/Discord):

```bash
ngrok http 7071
```

Copy the HTTPS forwarding URL (example: `https://abc123.ngrok-free.app`).

Set callback URLs in platform consoles:
- Slack Interactivity Request URL:
  - `https://abc123.ngrok-free.app/api/webhooks/slack/actions`
- Discord Interactions Endpoint URL:
  - `https://abc123.ngrok-free.app/api/webhooks/discord/interactions`

Expected:
- Slack accepts/saves the Request URL.
- Discord validates endpoint and saves it (Functions responds to `type=1` ping with `type=1`).

## 5) Local E2E smoke (inline mode)

Terminal 3:

```bash
curl -sS http://localhost:7071/api/health
```

Expected: `{"ok":true}`.

Run the inline alert flow (replace `<your-subscription-id>`):

```bash
curl -sS -X POST http://localhost:7071/api/webhooks/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "schemaId": "azureMonitorCommonAlertSchema",
    "data": {
      "essentials": {
        "alertId": "/subscriptions/<your-subscription-id>/providers/Microsoft.AlertsManagement/alerts/demo-gpu-spike-001",
        "alertRule": "GPU VM Cost Spike",
        "severity": "Sev1",
        "signalType": "Metric",
        "monitorCondition": "Fired",
        "monitoringService": "Cost Management",
        "alertTargetIDs": [
          "/subscriptions/<your-subscription-id>/resourceGroups/spikehound-demo-rg/providers/Microsoft.Compute/virtualMachines/spikehound-gpu-vm"
        ],
        "firedDateTime": "2026-02-11T10:00:00Z",
        "description": "Unexpected GPU VM running for 72 hours with $450 daily spend"
      },
      "alertContext": {
        "ResourceId": "/subscriptions/<your-subscription-id>/resourceGroups/spikehound-demo-rg/providers/Microsoft.Compute/virtualMachines/spikehound-gpu-vm",
        "costAnomaly": {
          "expectedDailyCost": 12.50,
          "actualDailyCost": 450.00,
          "anomalyFactor": 36.0
        }
      }
    }
  }'
```

Expected:
- HTTP `200`
- JSON payload with `UnifiedFindings`, `DiagnosisResult`, `RemediationResult`

Idempotency check (send the same payload again):
- Expected: HTTP `200` and a valid report payload again (cached path).

## 6) Edge-case checks

Invalid JSON should fail cleanly:

```bash
curl -i -sS -X POST http://localhost:7071/api/webhooks/alert \
  -H 'Content-Type: application/json' \
  -d '{not json}'
```

Expected:
- HTTP `400`
- body: `invalid json`

Unsigned callbacks should be rejected:

```bash
curl -i -sS -X POST http://localhost:7071/api/webhooks/slack/actions \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'payload={}'

curl -i -sS -X POST http://localhost:7071/api/webhooks/discord/interactions \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Expected: both return HTTP `401`.

## 6.1) Slack interactive approve (safe execution toggle OFF)

This validates the human-loop callback wiring without allowing real remediation side effects.

```bash
export SLACK_SIGNING_SECRET="dev-secret"
export SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION=false
```

After you send an alert once (Section 5), run:

```bash
export SUBSCRIPTION_ID="<your-subscription-id>"
```

Then run:

```bash
python3 - <<'PY'
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request

subscription_id = os.environ["SUBSCRIPTION_ID"]
investigation_id = f"/subscriptions/{subscription_id}/providers/Microsoft.AlertsManagement/alerts/demo-gpu-spike-001"

payload = {
    "actions": [{
        "action_id": "approve_remediation",
        "value": investigation_id
    }],
    "user": {"username": "local-tester"},
}

body = "payload=" + urllib.parse.quote(json.dumps(payload, separators=(",", ":")))
ts = str(int(time.time()))
signed = f"v0:{ts}:{body}".encode()
signature = "v0=" + hmac.new(b"dev-secret", signed, hashlib.sha256).hexdigest()

req = urllib.request.Request(
    "http://localhost:7071/api/webhooks/slack/actions",
    data=body.encode(),
    method="POST",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Slack-Request-Timestamp": ts,
        "X-Slack-Signature": signature,
    },
)

with urllib.request.urlopen(req, timeout=10) as resp:
    print(resp.getcode())
    print(resp.read().decode())
PY
```

Expected:
- HTTP `200`
- response text confirms the approve decision was recorded
- response text includes: `Execution is currently disabled by configuration.`

Run the same script a second time right away.

Expected on second run:
- HTTP `200`
- response text includes: `Remediation execution has already been queued.`

Optional real-click check in Slack:
- Trigger alert (Section 5), open the Slack notification, click **Approve**.
- Expected: callback succeeds with a recorded decision and queue/disabled status.

## 6.2) Discord interactive approve (safe execution toggle OFF)

Recommended mode: `DISCORD_BOT_TOKEN` + `DISCORD_CHANNEL_ID` configured.

1. Trigger alert once (Section 5).
2. Open the Discord notification message and click **Approve**.

Expected:
- The interaction callback hits `/api/webhooks/discord/interactions`.
- Functions returns a Discord ephemeral confirmation message:
  - recorded approve decision
  - `Execution is currently disabled by configuration.` (safe mode)

Duplicate-click check:
- Click **Approve** again on the same message.

Expected on second click:
- response confirms decision recorded
- response includes: `Remediation execution has already been queued.`

Troubleshooting:
- If no buttons appear: ensure bot mode is configured (token + channel id) and bot can send messages in target channel.
- If Discord endpoint save fails: verify ngrok URL, Functions host running, and `DISCORD_INTERACTIONS_PUBLIC_KEY` value.
- If clicks return unauthorized: public key mismatch between `.env` and Discord app.

## 7) Durable mode smoke

Stop the inline host and start Functions with durable mode enabled:

```bash
cd projects/incident-war-room
set -a; source .env; set +a

cd dotnet/src/Spikehound.Functions
SPIKEHOUND_USE_DURABLE=true func start
```

Then send the same alert payload again.

Expected:
- HTTP `202`
- JSON with `mode: "durable"`, `accepted: true`, and `instanceId`

For visibility during demo narration, you can also keep an eye on host logs in Terminal 2 and mention the orchestration schedule log line.

## 8) Optional real Azure side-effect demo (Slack approval)

Use this only if you have a safe demo VM and RG.

Before starting the Functions host for this flow, set:

```bash
export SPIKEHOUND_ENABLE_REMEDIATION_EXECUTION=true
```

### 8.1) One-time bootstrap (if demo infra does not exist yet)

Register providers (safe to run multiple times):

```bash
az provider register --namespace Microsoft.Compute --wait
az provider register --namespace Microsoft.Network --wait
```

Create demo resource group + VM (example uses Poland Central and a low-core SKU that works in this subscription policy setup):

```bash
az group create \
  --name spikehound-demo-rg \
  --location polandcentral \
  --tags app=spikehound purpose=demo

az vm create \
  --resource-group spikehound-demo-rg \
  --name spikehound-gpu-vm \
  --location polandcentral \
  --image Ubuntu2204 \
  --size Standard_D2s_v3 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-address "" \
  --nsg-rule NONE \
  --tags app=spikehound purpose=demo
```

If your subscription policy or quota differs, list allowed regions/SKUs first and substitute accordingly.

Preflight:

```bash
az account show --query "{name:name,id:id,user:user.name}" -o table
az vm list -d --query "[].{name:name,rg:resourceGroup,powerState:powerState}" -o table
```

Set demo target:

```bash
export DEMO_VM_NAME="<existing-vm-name>"
export DEMO_RESOURCE_GROUP="<existing-resource-group>"
```

If you want to use the default Spikehound naming:

```bash
export DEMO_VM_NAME="spikehound-gpu-vm"
export DEMO_RESOURCE_GROUP="spikehound-demo-rg"
```

Stage:

```bash
cd projects/incident-war-room
bash demo/stage_anomaly.sh --vm-name "$DEMO_VM_NAME" --resource-group "$DEMO_RESOURCE_GROUP"
```

Expose local host publicly (example: ngrok) and configure Slack interactivity callback:
- `https://<public-host>/api/webhooks/slack/actions`

Trigger alert (with your subscription id and VM resource id), click Approve in Slack, then verify VM state:

```bash
az vm show -d --resource-group "$DEMO_RESOURCE_GROUP" --name "$DEMO_VM_NAME" --query powerState -o tsv
```

Cleanup:

```bash
cd projects/incident-war-room
bash demo/cleanup_demo.sh --vm-name "$DEMO_VM_NAME" --resource-group "$DEMO_RESOURCE_GROUP"
```

## 9) Submission artifacts

- Architecture diagram: `docs/architecture.png`
- Recording checklist: `demo/recording_checklist.md`
- Script: `demo/script.md`
- Optional local video artifact: `demo/video.mp4`
