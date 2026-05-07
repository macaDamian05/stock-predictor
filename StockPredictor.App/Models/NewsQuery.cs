namespace StockPredictor.App.Models;

public sealed class NewsQuery
{
    public string? Category { get; init; }

    public string? Ticker { get; init; }

    public IReadOnlyList<string>? PreferredTickers { get; init; }

    public bool PreferTickerMatches { get; init; }

    public int? MaxItems { get; init; }
}
