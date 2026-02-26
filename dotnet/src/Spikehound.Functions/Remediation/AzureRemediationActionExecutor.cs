using System;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.ResourceManager;
using Azure.ResourceManager.Compute;
using Spikehound.Core.Execution;
using Spikehound.Core.Models;
using Microsoft.Extensions.Logging;

namespace Spikehound.Functions.Remediation;

public sealed class AzureRemediationActionExecutor : IRemediationActionExecutor
{
    private static readonly Regex VmResourceIdPattern = new(
        "^/subscriptions/(?<subscription>[^/]+)/resourceGroups/(?<resourceGroup>[^/]+)/providers/Microsoft\\.Compute/virtualMachines/(?<vmName>[^/]+)$",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    private readonly ArmClient _armClient;
    private readonly ILogger<AzureRemediationActionExecutor> _logger;

    public AzureRemediationActionExecutor(ArmClient armClient, ILogger<AzureRemediationActionExecutor> logger)
    {
        _armClient = armClient;
        _logger = logger;
    }

    public async Task<RemediationExecutionOutcome> ExecuteAsync(RemediationAction action, CancellationToken cancellationToken)
    {
        return action.Type switch
        {
            RemediationActionType.StopVm => await ExecuteStopVmAsync(action, cancellationToken),
            RemediationActionType.ResizeVm => BuildOutcome(action, RemediationExecutionStatus.Degraded, "VM resize execution is not implemented yet."),
            RemediationActionType.AddAutoShutdown => BuildOutcome(action, RemediationExecutionStatus.Degraded, "Auto-shutdown execution is not implemented yet."),
            RemediationActionType.NotifyOwner => BuildOutcome(action, RemediationExecutionStatus.Skipped, "Manual owner notification action; no automated executor is configured."),
            RemediationActionType.OpenTicket => BuildOutcome(action, RemediationExecutionStatus.Skipped, "Manual ticket action; no automated executor is configured."),
            _ => BuildOutcome(action, RemediationExecutionStatus.Degraded, "Unsupported remediation action type."),
        };
    }

    private async Task<RemediationExecutionOutcome> ExecuteStopVmAsync(RemediationAction action, CancellationToken cancellationToken)
    {
        if (!TryParseVmResourceId(action.TargetResourceId, out var subscriptionId, out var resourceGroup, out var vmName))
        {
            return BuildOutcome(action, RemediationExecutionStatus.Error, "Target resource ID is not a valid Azure VM resource ID.");
        }

        try
        {
            var vmId = VirtualMachineResource.CreateResourceIdentifier(subscriptionId, resourceGroup, vmName);
            var vm = _armClient.GetVirtualMachineResource(vmId);
            await vm.DeallocateAsync(WaitUntil.Started, hibernate: null, cancellationToken: cancellationToken);

            _logger.LogInformation(
                "remediation_stop_vm_requested: {subscriptionId} {resourceGroup} {vmName}",
                subscriptionId,
                resourceGroup,
                vmName);

            return BuildOutcome(action, RemediationExecutionStatus.Ok, "Azure VM deallocate request submitted.");
        }
        catch (RequestFailedException ex)
        {
            var reason = string.IsNullOrWhiteSpace(ex.ErrorCode)
                ? ex.Message
                : $"{ex.ErrorCode}: {ex.Message}";
            return BuildOutcome(action, RemediationExecutionStatus.Error, reason);
        }
        catch (Exception ex)
        {
            return BuildOutcome(action, RemediationExecutionStatus.Error, ex.Message);
        }
    }

    private static bool TryParseVmResourceId(
        string resourceId,
        out string subscriptionId,
        out string resourceGroup,
        out string vmName)
    {
        subscriptionId = string.Empty;
        resourceGroup = string.Empty;
        vmName = string.Empty;

        var match = VmResourceIdPattern.Match(resourceId);
        if (!match.Success)
        {
            return false;
        }

        subscriptionId = match.Groups["subscription"].Value;
        resourceGroup = match.Groups["resourceGroup"].Value;
        vmName = match.Groups["vmName"].Value;
        return !string.IsNullOrWhiteSpace(subscriptionId)
            && !string.IsNullOrWhiteSpace(resourceGroup)
            && !string.IsNullOrWhiteSpace(vmName);
    }

    private static RemediationExecutionOutcome BuildOutcome(
        RemediationAction action,
        RemediationExecutionStatus status,
        string message)
    {
        var now = DateTimeOffset.UtcNow;
        return new RemediationExecutionOutcome(
            ActionType: action.Type,
            TargetResourceId: action.TargetResourceId,
            Status: status,
            Message: message,
            StartedAt: now,
            FinishedAt: now);
    }
}
