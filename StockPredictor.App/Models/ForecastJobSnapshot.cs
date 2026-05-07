namespace StockPredictor.App.Models;

public sealed record ForecastJobSnapshot
{
    public string Ticker { get; init; } = string.Empty;

    public ForecastJobState State { get; init; }

    public ForecastJobTrigger Trigger { get; init; }

    public DateTime RequestedAt { get; init; } = DateTime.Now;

    public DateTime? StartedAt { get; init; }

    public DateTime? CompletedAt { get; init; }

    public string? Message { get; init; }

    public string? ErrorMessage { get; init; }

    public List<string> SuggestedCommands { get; init; } = [];
}

public enum ForecastJobState
{
    Pending,
    Running,
    Completed,
    Failed,
}

public enum ForecastJobTrigger
{
    ManualCreate,
    ManualRefresh,
    AutomaticStaleRefresh,
}
