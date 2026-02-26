using System;
using System.Threading;
using System.Threading.Tasks;
using Spikehound.Functions.Remediation;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Extensions.DurableTask;
using Microsoft.DurableTask;

namespace Spikehound.Functions.Durable;

public static class RemediationExecutionOrchestration
{
    [Function("RemediationExecutionOrchestrator")]
    public static Task<RemediationExecutionSummary> Run(
        [OrchestrationTrigger] TaskOrchestrationContext context)
    {
        var request = context.GetInput<RemediationExecutionRequest>();
        if (request is null)
        {
            throw new InvalidOperationException("Missing remediation execution request payload.");
        }

        return context.CallActivityAsync<RemediationExecutionSummary>("ExecuteRemediationActivity", request);
    }
}

public sealed class RemediationExecutionActivities
{
    private readonly ApprovalRemediationWorkflow _workflow;

    public RemediationExecutionActivities(ApprovalRemediationWorkflow workflow)
    {
        _workflow = workflow;
    }

    [Function("ExecuteRemediationActivity")]
    public Task<RemediationExecutionSummary> Execute(
        [ActivityTrigger] RemediationExecutionRequest request)
    {
        return _workflow.ExecuteQueuedRequestAsync(request, CancellationToken.None);
    }
}
