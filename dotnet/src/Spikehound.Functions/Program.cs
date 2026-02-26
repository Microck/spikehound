using Azure.Identity;
using Azure.ResourceManager;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Spikehound.Functions;
using Spikehound.Core.Agents;
using Spikehound.Core.Execution;
using Spikehound.Core.Orchestration;
using Spikehound.Functions.Remediation;

var builder = FunctionsApplication.CreateBuilder(args);

builder.ConfigureFunctionsWebApplication();

builder.Services
    .AddApplicationInsightsTelemetryWorkerService()
    .ConfigureFunctionsApplicationInsights();

builder.Services.AddHttpClient();
builder.Services.AddSingleton(_ => new ArmClient(new DefaultAzureCredential()));

builder.Services.AddSingleton<InMemoryState>();
builder.Services.AddSingleton<INotificationSink, WebhookNotificationSink>();
builder.Services.AddSingleton<IRemediationActionExecutor, AzureRemediationActionExecutor>();
builder.Services.AddSingleton<ApprovalRemediationWorkflow>();
builder.Services.AddSingleton<CoordinatorPipeline>(sp =>
{
    var sink = sp.GetRequiredService<INotificationSink>();
    return new CoordinatorPipeline(
        costAgent: new FallbackCostAgent(),
        resourceAgent: new FallbackResourceAgent(),
        historyAgent: new FallbackHistoryAgent(),
        diagnosisAgent: new FallbackDiagnosisAgent(),
        remediationAgent: new FallbackRemediationAgent(),
        notificationSink: sink);
});

builder.Build().Run();
