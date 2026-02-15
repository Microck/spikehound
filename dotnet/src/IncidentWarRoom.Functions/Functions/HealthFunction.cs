using System.Net;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;

namespace IncidentWarRoom.Functions.Functions;

public sealed class HealthFunction
{
    [Function("health")]
    public static HttpResponseData Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "health")] HttpRequestData req)
    {
        var res = req.CreateResponse(HttpStatusCode.OK);
        res.Headers.Add("Content-Type", "application/json");
        res.WriteString("{\"ok\":true}");
        return res;
    }
}
