# TriageForge Demo Scenario

## Overview

This demo shows the complete **multi-agent investigation pipeline** for a staged Azure cost anomaly. A GPU VM is left running unnecessarily, causing a daily cost spike from \$12 to \$450.

## Prerequisites

- Azure CLI is authenticated: `az account show` confirms subscription access
- TriageForge server is running: `uvicorn web.app:app --app-dir src --port 8000`
- Slack app webhook URL and signing secret are configured in `.env`

## Staged Anomaly

**What happened:** A GPU training VM (`gpu-training-vm`) was left running for 72 hours after the training job completed.

**Baseline expectation:** \$12.50/day for GPU VM when used appropriately (short training jobs, auto-shutdown configured)

**Actual spend:** \$450.00/day (36x anomaly factor)

**Root cause:** No auto-shutdown policy was configured on the VM. The training job completed at 10:00 AM UTC but the VM continued running.

## Triggering the Investigation

### Option A: Real Azure Monitor Alert (if configured)

If you've configured an Azure Monitor cost alert rule, it will fire automatically when the anomaly threshold is breached. The webhook endpoint `/webhooks/alert` will receive the alert payload.

### Option B: Manual Webhook Trigger (reliable for demo)

Use this `curl` command to simulate a real Azure Monitor alert:

```bash
curl -X POST http://localhost:8000/webhooks/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "schemaId": "azureMonitorCommonAlertSchema",
    "data": {
      "essentials": {
        "alertId": "/subscriptions/495eb1d8-99ac-40d1-9eaf-082d28b8ac56/providers/Microsoft.AlertsManagement/alerts/demo-gpu-spike-001",
        "alertRule": "GPU VM Cost Spike",
        "severity": "Sev1",
        "signalType": "Metric",
        "monitorCondition": "Fired",
        "monitoringService": "Cost Management",
        "alertTargetIDs": [
          "/subscriptions/495eb1d8-99ac-40d1-9eaf-082d28b8ac56/resourceGroups/ai-dev-days-hackathon-eu/providers/Microsoft.Compute/virtualMachines/gpu-training-vm"
        ],
        "firedDateTime": "2026-02-11T10:00:00Z",
        "description": "Unexpected GPU VM running for 72 hours with \$450 daily spend"
      },
      "alertContext": {
        "ResourceId": "/subscriptions/495eb1d8-99ac-40d1-9eaf-082d28b8ac56/resourceGroups/ai-dev-days-hackathon-eu/providers/Microsoft.Compute/virtualMachines/gpu-training-vm",
        "costAnomaly": {
          "expectedDailyCost": 12.50,
          "actualDailyCost": 450.00,
          "anomalyFactor": 36.0
        }
      }
    }
  }'
```

## Expected Multi-Agent Outputs

### 1. Cost Analyst Agent

**Output:** Identifies the GPU VM as the top cost driver

```
Top cost driver: gpu-training-vm ($450.00/day)
Anomaly: 36x above baseline
```

### 2. Resource Agent

**Output:** Retrieves VM configuration and recent activity

```
Resource: gpu-training-vm
VM Size: Standard_NC6s_v3
Status: Running
Location: francecentral
Tags: demo=true
Last Modified: 2026-02-11T10:00:00Z (no changes since training ended)
```

### 3. History Agent

**Output:** Searches Azure AI Search for similar past incidents

```
Similar incidents: 0 (no historical matches)
Confidence: High (first occurrence pattern)
```

### 4. Diagnosis Agent

**Output:** Synthesizes findings into root cause hypothesis

```
Root Cause: GPU VM left running after training job completed 72 hours ago
Confidence: 85%
Explanation: Training job finished at 10:00 AM UTC but auto-shutdown was not configured. VM continued running at \$450/day.
```

### 5. Remediation Agent

**Output:** Suggests fix action with human approval requirement

```
Action Type: stop_vm
Target: /subscriptions/.../virtualMachines/gpu-training-vm
Description: Stop and deallocate GPU VM
Human Approval Required: Yes
Estimated Savings: ~$450/day
```

## Human Approval Flow

After diagnosis completes, a **Slack notification** appears with:

- **Alert ID:** `demo-gpu-spike-001`
- **Top Cost Driver:** gpu-training-vm ($450/day)
- **Confidence:** 85%
- **Root Cause:** GPU VM left running after training job completed 72 hours ago
- **First Remediation Action:** stop_vm on gpu-training-vm

### Slack Buttons

1. **Approve** (primary) — Queues the `stop_vm` action to execute
2. **Reject** (danger) — Records decision but does not execute any action
3. **Investigate More** — Records decision for manual follow-up

## Expected Remediation Outcome

After clicking **Approve**:

1. Server receives the Slack callback with verified HMAC signature
2. `ApprovalRecord` is created with decision `approve`
3. Background task executes `stop_vm` via Azure Compute API
4. VM status transitions: Running → Stopped → (optionally) Deallocated
5. Follow-up Slack message posts execution outcome

```
[12:00:15Z] ✅ Remediation completed
Action: stop_vm
Target: gpu-training-vm
Outcome: SUCCESS - VM stopped and deallocated
Estimated Savings: $450/day ongoing
```

## Cleanup

After the demo, run the cleanup script to reset the VM state:

```bash
bash demo/cleanup_demo.sh --vm-name gpu-training-vm --resource-group ai-dev-days-hackathon-eu
```

This will:
- Remove the `demo=true` tag
- Optionally start the VM again for the next demo run
