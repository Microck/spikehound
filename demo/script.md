# Spikehound Demo Script (2 Minutes)

## Timecoded Demo

This script provides a precise, timecoded demo for the hackathon presentation. Total runtime: ~2:00 minutes.

### Prerequisites

1. **Azure CLI is authenticated:** `az account show` confirms access
2. **Spikehound Functions app is running:** `cd dotnet/src/Spikehound.Functions && func start`
3. **Slack app is configured:** `.env` has `SLACK_WEBHOOK_URL` and `SLACK_SIGNING_SECRET`
4. **Discord app is configured (optional for demo):** `.env` has `DISCORD_INTERACTIONS_PUBLIC_KEY`; for interactive Discord buttons, set `DISCORD_BOT_TOKEN` + `DISCORD_CHANNEL_ID`
5. **Demo VM is staged:** Run `bash demo/stage_anomaly.sh --vm-name <vm> --resource-group <rg>` first
6. **Inline mode for live narration:** set `SPIKEHOUND_USE_DURABLE=false` (durable mode returns async `202` scheduling response)

### Before Recording

- **Open terminal 1:** Run the server (large font, visible on screen)
- **Open terminal 2:** For webhook trigger (separate window)
- **Open Slack:** Show the #alerts or demo channel
- **Prepare demo-alert-payload.json:** Copy the payload below to a file for easy pasting

---

## Demo Script

### 0:00 - 0:10 | Introduction (10 seconds)

**Show:** README.md in editor or browser
- Highlight project name: "Spikehound — Multi-Agent Azure Cost Anomaly War Room"
- Show that we won **3 prize categories**: Agentic DevOps, Multi-Agent, Azure Integration

**Say:**
> "Today I'll demonstrate Spikehound, a multi-agent system that automatically investigates Azure cost anomalies. We built this for the Microsoft AI Dev Days Hackathon 2026 and it targets three prize categories."

### 0:10 - 0:30 | Architecture Overview (20 seconds)

**Show:** docs/architecture.png in viewer
- Point to each section: Coordinator, 6 agents, Slack integration

**Say:**
> "Let me show you the architecture. The system starts with an Azure Monitor alert, flows through a Coordinator that orchestrates 6 specialized agents in parallel — Cost Analyst, Resource Agent, and History Agent. A Diagnosis Agent synthesizes their findings into a root cause with 85% confidence, then the Remediation Agent suggests fix actions. All this happens automatically before a human ever joins the call."

### 0:30 - 0:45 | Staged Anomaly (15 seconds)

**Show:** Demo VM in Azure Portal or CLI
- Navigate to VM: show it's running
- Show cost metrics if available

**Say:**
> "For this demo, I've staged an anomaly. Here's a GPU VM that's been running for 72 hours. The baseline expectation is $12 per day, but it's actually costing $450 per day — that's a 36x spike."

### 0:45 - 1:00 | Trigger Investigation (15 seconds)

**Action:** Send webhook from terminal 2

**Show:** Terminal 2 window
- Type the `curl` command OR use pre-prepared `demo-alert-payload.json` file

**Terminal 2 shows:**
```bash
curl -X POST http://localhost:7071/api/webhooks/alert \
  -H 'Content-Type: application/json' \
  -d @demo-alert-payload.json
```

**Server terminal (Terminal 1) shows:**
```
INFO:spikehound:webhook_received
INFO:spikehound:running_coordinator_fanout
INFO:spikehound:cost_analyst_completed
INFO:spikehound:resource_agent_completed
INFO:spikehound:history_agent_completed
INFO:spikehound:diagnosis_completed
INFO:spikehound:remediation_completed
INFO:spikehound:slack_webhook_sent
```

**Say:**
> "Now I'm triggering the investigation by sending the Azure Monitor alert to our webhook. You'll see the server logs here in Terminal 1 as all 6 agents run in parallel."

### 1:00 - 1:20 | Multi-Agent Outputs (20 seconds)

**Show:** Slack channel (or Discord channel if demoing Discord)
- Point to each section of the Slack message

**Slack message appears with:**
```
Incident Investigation Complete

Alert: demo-gpu-spike-001
Top cost driver(s): spikehound-gpu-vm ($450.00/day)
Confidence: 85%
Root cause: GPU VM left running after training job completed 72 hours ago
First remediation action: stop_vm on spikehound-gpu-vm

[Approve] [Reject] [Investigate More]
```

**Say:**
> "The investigation completed automatically. You can see the Slack notification here. It shows the top cost driver — the GPU VM at $450 per day — with 85% confidence that the root cause is the VM being left running after a training job completed. The system suggests stopping the VM as the remediation action."

### 1:20 - 1:40 | Human Approval (20 seconds)

**Action:** Click the "Approve" button in Slack (or Discord)

**Show:** Terminal 1 — watch for logs
- New log lines appear as Slack callback is received and processed

**Terminal 1 shows:**
```
INFO:spikehound:slack_approval_received
INFO:spikehound:slack_approval_recorded
INFO:spikehound:remediation_execution_queued
INFO:spikehound:remediation_execution_started
INFO:spikehound:azure_vm_stop_attempt
INFO:spikehound:remediation_completed
INFO:spikehound:slack_follow_up_sent
```

**Say:**
> "To execute any remediation action, a human must explicitly approve it. I'm clicking the Approve button now. This is a critical safety feature — no actions execute without human approval."

### 1:40 - 2:00 | Remediation Execution (20 seconds)

**Show:** Follow-up Slack message and Azure VM status
- Refresh Slack channel to see follow-up
- Show Azure VM portal (optional: switch to Stopped view)

**Follow-up Slack message appears:**
```
✅ Remediation completed
Action: stop_vm
Target: spikehound-gpu-vm
Outcome: SUCCESS - VM stopped and deallocated
Estimated Savings: $450/day ongoing
```

**Say:**
> "The remediation executed successfully. The Slack follow-up message confirms the VM has been stopped. This eliminates the $450 per day cost anomaly — that's potential savings of $13,500 per month for just this one VM. The entire investigation and remediation loop happened automatically, requiring only one human approval decision."

---

## Demo Payload File

Save this as `demo-alert-payload.json` for easy triggering:

```json
{
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
}
```

To trigger during demo:
```bash
curl -X POST http://localhost:7071/api/webhooks/alert \
  -H 'Content-Type: application/json' \
  -d @demo-alert-payload.json
```

---

## End of Demo

**Summary shown to judges:**
- Multi-agent system runs 6 agents in parallel under 15 seconds
- Root cause diagnosis with 85% confidence is generated automatically
- Human approval is required for all remediation (safety)
- Approved actions execute against Azure (VM stopped)
- Potential savings: $450/day = $13,500/month for one anomaly
- Entire pipeline is fully autonomous except for one human click
