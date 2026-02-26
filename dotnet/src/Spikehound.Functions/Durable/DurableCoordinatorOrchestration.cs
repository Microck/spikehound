using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Extensions.DurableTask;
using Microsoft.DurableTask;

namespace Spikehound.Functions.Durable;

// Durable stubs: provide a fan-out/fan-in model for agent orchestration.
// The HTTP endpoints fall back to inline execution by default so local demos
// don't require a Durable backend/storage emulator.
public static class DurableCoordinatorOrchestration
{
    [Function("CoordinatorOrchestrator")]
    public static async Task<Dictionary<string, string>> Run(
        [OrchestrationTrigger] TaskOrchestrationContext context)
    {
        var payloadJson = context.GetInput<string>() ?? "{}";

        var costTask = context.CallActivityAsync<string>("CostAgentActivity", payloadJson);
        var resourceTask = context.CallActivityAsync<string>("ResourceAgentActivity", payloadJson);
        var historyTask = context.CallActivityAsync<string>("HistoryAgentActivity", payloadJson);

        await Task.WhenAll(costTask, resourceTask, historyTask);

        var diagnosis = await context.CallActivityAsync<string>("DiagnosisActivity", payloadJson);
        var remediation = await context.CallActivityAsync<string>("RemediationActivity", payloadJson);
        await context.CallActivityAsync<string>("NotificationActivity", payloadJson);

        return new Dictionary<string, string>
        {
            ["cost"] = costTask.Result,
            ["resource"] = resourceTask.Result,
            ["history"] = historyTask.Result,
            ["diagnosis"] = diagnosis,
            ["remediation"] = remediation,
        };
    }

    [Function("CostAgentActivity")]
    public static string CostAgentActivity([ActivityTrigger] string payloadJson) => "degraded";

    [Function("ResourceAgentActivity")]
    public static string ResourceAgentActivity([ActivityTrigger] string payloadJson) => "degraded";

    [Function("HistoryAgentActivity")]
    public static string HistoryAgentActivity([ActivityTrigger] string payloadJson) => "degraded";

    [Function("DiagnosisActivity")]
    public static string DiagnosisActivity([ActivityTrigger] string payloadJson) => "degraded";

    [Function("RemediationActivity")]
    public static string RemediationActivity([ActivityTrigger] string payloadJson) => "degraded";

    [Function("NotificationActivity")]
    public static string NotificationActivity([ActivityTrigger] string payloadJson) => "ok";
}
