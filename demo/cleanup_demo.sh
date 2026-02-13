#!/bin/bash

# demo/cleanup_demo.sh
#
# Cleans up the demo VM state after a demo run.
# Usage: bash demo/cleanup_demo.sh --vm-name <name> --resource-group <name>
#
# This script stops the VM and removes demo tags to reset state.

set -euo pipefail

usage() {
  echo "Usage: bash demo/cleanup_demo.sh --vm-name <name> --resource-group <name>"
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
echo "Spikehound Demo: Cleanup"
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

# Stop the VM if running
if [[ "$VM_STATUS" == "VM running" ]]; then
  echo "Stopping VM..."
  run az vm deallocate \
    --name "$VM_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --no-wait

  echo "✓ VM deallocate command sent (async operation)"
  echo ""
  echo "Waiting for operation to initiate..."
  sleep 5
else
  echo "✓ VM is not running (status: $VM_STATUS)"
fi
echo ""

# Remove demo tags
echo "Removing demo tags..."
run az vm update \
  --name "$VM_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --remove tags.demo \
  --remove tags.demo_scenario \
  --remove tags.demo_date

echo "✓ Demo tags removed"
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
echo "Cleanup Complete"
echo "=========================================="
echo ""
echo "The VM has been stopped and demo tags removed."
echo "State reset for the next demo run."
