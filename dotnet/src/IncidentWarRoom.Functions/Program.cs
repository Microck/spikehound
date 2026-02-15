using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using IncidentWarRoom.Functions;
using IncidentWarRoom.Core.Agents;
using IncidentWarRoom.Core.Orchestration;

var builder = FunctionsApplication.CreateBuilder(args);

builder.ConfigureFunctionsWebApplication();

builder.Services
    .AddApplicationInsightsTelemetryWorkerService()
    .ConfigureFunctionsApplicationInsights();

builder.Services.AddHttpClient();

builder.Services.AddSingleton<InMemoryState>();
builder.Services.AddSingleton<INotificationSink, WebhookNotificationSink>();
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
