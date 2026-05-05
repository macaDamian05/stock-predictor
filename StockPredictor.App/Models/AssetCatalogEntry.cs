namespace StockPredictor.App.Models;

public sealed class AssetCatalogEntry
{
    public string Ticker { get; init; } = string.Empty;

    public string? DisplayName { get; init; }

    public string? AssetType { get; init; }

    public double? LastClose { get; init; }

    public DateOnly? LastCloseDate { get; init; }

    public bool ForecastAvailable { get; init; }

    public double? ForecastHorizonChangePct { get; init; }

    public FeaturedTicker? FeaturedTicker { get; init; }

    public CompanyRankingEntry? RankingEntry { get; init; }

    public bool HasPreparedPayloadData => FeaturedTicker is not null;
}
