namespace StockPredictor.App.Models;

public sealed class MarketDataOptions
{
    public const string SectionName = "MarketData";

    public int CacheFreshMinutes { get; init; } = 30;

    public int InMemoryFreshMinutes { get; init; } = 5;

    public string StartDate { get; init; } = "1990-01-01";

    public string IntradayPeriod { get; init; } = "5d";

    public string IntradayInterval { get; init; } = "15m";
}
