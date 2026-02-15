using System.Collections.Generic;

namespace IncidentWarRoom.Core.Models;

public sealed record RootCauseHypothesis(
    string Title,
    string Explanation,
    IReadOnlyList<string> Evidence
);

public sealed record Diagnosis(
    RootCauseHypothesis Hypothesis,
    int Confidence,
    IReadOnlyList<string> Alternatives,
    IReadOnlyList<string> Risks
);
