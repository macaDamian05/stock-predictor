namespace StockPredictor.App.Models;

public sealed class ForecastAutomationOptions
{
    public const string SectionName = "ForecastAutomation";

    public bool AutoRefreshEnabled { get; init; } = true;

    public int AutoRefreshStaleAfterDays { get; init; } = 1;

    public int AutoRefreshCooldownMinutes { get; init; } = 90;
}
