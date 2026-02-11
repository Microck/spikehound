#!/bin/bash

# demo/cleanup_demo.sh
#
# Cleans up the demo VM state after a demo run.
# Usage: bash demo/cleanup_demo.sh --vm-name <name> --resource-group <name>
#
# This script stops the VM and removes demo tags to reset state.

set -e

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --vm-name)
      VM_NAME="$2"
      shift 2
      ;;
    --resource-group)
      RESOURCE_GROUP="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: bash demo/cleanup_demo.sh --vm-name <name> --resource-group <name>"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [[ -z "$VM_NAME" || -z "$RESOURCE_GROUP" ]]; then
  echo "Error: Missing required arguments"
  echo "Usage: bash demo/cleanup_demo.sh --vm-name <name> --resource-group <name>"
  exit 1
fi

echo "=========================================="
echo "TriageForge Demo: Cleanup"
echo "=========================================="
echo "VM Name: $VM_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Check if Azure CLI is authenticated
echo "Checking Azure CLI authentication..."
if ! az account show &>/dev/null; then
  echo "Error: Azure CLI is not authenticated."
  echo "Run: az login"
  exit 1
fi
echo "✓ Authenticated as $(az account show --query user.name -o tsv)"
echo ""

# Get current VM status
echo "Checking current VM status..."
VM_STATUS=$(az vm show \
  --name "$VM_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query powerState \
  -o tsv 2>/dev/null || echo "unknown")

echo "Current status: $VM_STATUS"
echo ""

# Stop the VM if running
if [[ "$VM_STATUS" == "VM running" ]]; then
  echo "Stopping VM..."
  az vm deallocate \
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
az vm update \
  --name "$VM_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --remove tags.demo \
  --remove tags.demo-scenario \
  --remove tags.demo-date

echo "✓ Demo tags removed"
echo ""

# Show VM details for confirmation
echo "=========================================="
echo "VM Details"
echo "=========================================="
az vm show --name "$VM_NAME" --resource-group "$RESOURCE_GROUP" --query '[{name: name, size: hardwareProfile.vmSize, powerState: powerState, tags: tags}]' -o json
echo ""

echo "=========================================="
echo "Cleanup Complete"
echo "=========================================="
echo ""
echo "The VM has been stopped and demo tags removed."
echo "State reset for the next demo run."
