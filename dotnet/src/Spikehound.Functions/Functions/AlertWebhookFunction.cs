using System;
using System.Net;
using System.Text.Json;
using System.Threading.Tasks;
using Spikehound.Core.Orchestration;
using Spikehound.Functions.Http;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.Functions.Worker.Extensions.DurableTask;
using Microsoft.Extensions.Logging;
using Microsoft.DurableTask.Client;

namespace Spikehound.Functions.Functions;

public sealed class AlertWebhookFunction
{
    private readonly CoordinatorPipeline _pipeline;
    private readonly InMemoryState _state;
    private readonly ILogger<AlertWebhookFunction> _logger;

    public AlertWebhookFunction(CoordinatorPipeline pipeline, InMemoryState state, ILogger<AlertWebhookFunction> logger)
    {
        _pipeline = pipeline;
        _state = state;
        _logger = logger;
    }

    [Function("webhooks_alert")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "webhooks/alert")] HttpRequestData req,
        [DurableClient] DurableTaskClient durableClient)
    {
        var ttlSecondsRaw = Environment.GetEnvironmentVariable("SPIKEHOUND_IDEMPOTENCY_TTL_SECONDS");
        var ttlSeconds = int.TryParse(ttlSecondsRaw, out var parsed) ? Math.Max(parsed, 0) : 600;
        var ttl = TimeSpan.FromSeconds(ttlSeconds);

        var now = DateTimeOffset.UtcNow;
        _state.PruneExpired(now, ttl);

        JsonElement payload;
        try
        {
            payload = await JsonSerializer.DeserializeAsync<JsonElement>(req.Body);
        }
        catch (JsonException)
        {
            var bad = req.CreateResponse(HttpStatusCode.BadRequest);
            await HttpUtils.WritePlainTextAsync(bad, "invalid json");
            return bad;
        }

        var normalized = Spikehound.Core.Parsing.AlertNormalizer.Normalize(payload);
        var investigationId = normalized.AlertId;

        if (_state.TryGetCachedReport(investigationId, now, ttl, out var cached))
        {
            _logger.LogInformation("webhook_duplicate_returning_cached_report: {investigationId}", investigationId);
            var cachedRes = req.CreateResponse(HttpStatusCode.OK);
            await cachedRes.WriteAsJsonAsync(cached);
            return cachedRes;
        }

        if (ShouldUseDurableOrchestration())
        {
            var instanceId = await durableClient.ScheduleNewOrchestrationInstanceAsync(
                "CoordinatorOrchestrator",
                payload.GetRawText());

            _logger.LogInformation(
                "durable_orchestration_scheduled: {investigationId} -> {instanceId}",
                investigationId,
                instanceId);

            var accepted = req.CreateResponse(HttpStatusCode.Accepted);
            await accepted.WriteAsJsonAsync(new
            {
                mode = "durable",
                accepted = true,
                investigationId,
                instanceId,
            });
            return accepted;
        }

        var report = await _pipeline.HandleAlertAsync(payload);
        _state.StoreReport(investigationId, now, report);

        var res = req.CreateResponse(HttpStatusCode.OK);
        await res.WriteAsJsonAsync(report);
        return res;
    }

    private static bool ShouldUseDurableOrchestration() =>
        string.Equals(
            Environment.GetEnvironmentVariable("SPIKEHOUND_USE_DURABLE"),
            "true",
            StringComparison.OrdinalIgnoreCase);
}
