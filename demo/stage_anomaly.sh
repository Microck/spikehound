#!/bin/bash

# demo/stage_anomaly.sh
#
# Stages a GPU VM cost anomaly for demo purposes.
# Usage: bash demo/stage_anomaly.sh --vm-name <name> --resource-group <name>
#
# This script ensures the demo VM is running and tags it for identification.
# It does NOT create expensive resources; it works with existing VMs.

set -euo pipefail

usage() {
  echo "Usage: bash demo/stage_anomaly.sh --vm-name <name> --resource-group <name>"
}

run() {
  echo "+ $*"
  "$@"
}

VM_NAME=""
RESOURCE_GROUP=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --vm-name)
      VM_NAME="${2:-}"
      shift 2
      ;;
    --resource-group)
      RESOURCE_GROUP="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# Validate required arguments
if [[ -z "$VM_NAME" || -z "$RESOURCE_GROUP" ]]; then
  echo "Error: Missing required arguments"
  usage
  exit 1
fi

echo "=========================================="
echo "Spikehound Demo: Staging Anomaly"
echo "=========================================="
echo "VM Name: $VM_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Check if Azure CLI is authenticated
echo "Checking Azure CLI authentication..."
if ! command -v az &>/dev/null; then
  echo "Error: az (Azure CLI) not found on PATH. Install Azure CLI first."
  exit 1
fi

if ! az account show &>/dev/null; then
  echo "Error: Azure CLI is not authenticated."
  echo "Run: az login"
  exit 1
fi
echo "✓ Azure CLI authenticated"
echo ""

POWER_STATE_CMD=(az vm show -d --name "$VM_NAME" --resource-group "$RESOURCE_GROUP" --query powerState -o tsv)
echo "+ ${POWER_STATE_CMD[*]}"

get_power_state() {
  local status
  status=$("${POWER_STATE_CMD[@]}" 2>/dev/null || true)
  if [[ -z "$status" ]]; then
    status="unknown"
  fi
  echo "$status"
}

# Get current VM status
echo "Checking current VM status..."
VM_STATUS=$(get_power_state)

echo "Current status: $VM_STATUS"
echo ""

# Ensure VM is running
if [[ "$VM_STATUS" != "VM running" ]]; then
  echo "VM is not running. Starting it..."
  run az vm start \
    --name "$VM_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --no-wait
  echo "✓ VM start command sent (async operation)"
  echo ""
  echo "Waiting for VM to be running..."
  for _ in {1..12}; do
    sleep 5
    VM_STATUS=$(get_power_state)
    echo "Current status: $VM_STATUS"
    if [[ "$VM_STATUS" == "VM running" ]]; then
      break
    fi
  done
else
  echo "✓ VM is already running"
fi
echo ""

# Tag VM for demo identification
echo "Tagging VM for demo identification..."
DEMO_DATE=$(date -u +%Y-%m-%d)
run az vm update \
  --name "$VM_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --set tags.demo=true \
  --set tags.demo_scenario=gpu-vm-cost-spike \
  --set tags.demo_date="$DEMO_DATE"

echo "✓ Tags added: demo=true, demo_scenario=gpu-vm-cost-spike"
echo ""

# Show VM details for confirmation
echo "=========================================="
echo "VM Details"
echo "=========================================="
run az vm show -d \
  --name "$VM_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query '[{name: name, size: hardwareProfile.vmSize, powerState: powerState, tags: tags}]' \
  -o json
echo ""

echo "=========================================="
echo "Staging Complete"
echo "=========================================="
echo ""
echo "The VM is now tagged and running."
echo "The demo scenario is ready to trigger via webhook."
echo ""
echo "To trigger the demo alert, run:"
echo "  curl -X POST http://localhost:8000/webhooks/alert -H 'Content-Type: application/json' -d @demo-alert-payload.json"
echo ""
echo "To clean up after the demo, run:"
echo "  bash demo/cleanup_demo.sh --vm-name $VM_NAME --resource-group $RESOURCE_GROUP"
