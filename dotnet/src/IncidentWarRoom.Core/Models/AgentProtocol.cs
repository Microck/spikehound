using System;
using System.Collections.Generic;

namespace IncidentWarRoom.Core.Models;

public enum AgentName
{
    Cost,
    Resource,
    History,
    Diagnosis,
    Remediation,
}

public enum AgentStatus
{
    Ok,
    Degraded,
    Error,
}

public sealed record AgentResult<T>(
    AgentName Agent,
    AgentStatus Status,
    DateTimeOffset StartedAt,
    DateTimeOffset FinishedAt,
    T? Data,
    IReadOnlyList<string> Errors
)
{
    public static AgentResult<T> Ok(AgentName agent, DateTimeOffset startedAt, DateTimeOffset finishedAt, T data) =>
        new(agent, AgentStatus.Ok, startedAt, finishedAt, data, Array.Empty<string>());

    public static AgentResult<T> Degraded(AgentName agent, DateTimeOffset startedAt, DateTimeOffset finishedAt, T? data, params string[] errors) =>
        new(agent, AgentStatus.Degraded, startedAt, finishedAt, data, errors);

    public static AgentResult<T> Error(AgentName agent, DateTimeOffset startedAt, DateTimeOffset finishedAt, params string[] errors) =>
        new(agent, AgentStatus.Error, startedAt, finishedAt, default, errors);
}
