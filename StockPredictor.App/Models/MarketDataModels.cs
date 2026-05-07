using System.Text.Json.Serialization;

namespace StockPredictor.App.Models;

public sealed class MarketDataBatchPayload
{
    [JsonPropertyName("generated_at")]
    public DateTime GeneratedAt { get; init; }

    [JsonPropertyName("result_count")]
    public int ResultCount { get; init; }

    [JsonPropertyName("results")]
    public List<MarketAssetSnapshot> Results { get; init; } = [];
}

public sealed class MarketAssetSnapshot
{
    [JsonPropertyName("ticker")]
    public string Ticker { get; init; } = string.Empty;

    [JsonPropertyName("generated_at")]
    public DateTime GeneratedAt { get; init; }

    [JsonPropertyName("status")]
    public string Status { get; init; } = string.Empty;

    [JsonPropertyName("warning")]
    public string? Warning { get; init; }

    [JsonPropertyName("error")]
    public string? Error { get; init; }

    [JsonPropertyName("daily_data_until")]
    public DateTime? DailyDataUntil { get; init; }

    [JsonPropertyName("intraday_data_until")]
    public DateTime? IntradayDataUntil { get; init; }

    [JsonPropertyName("daily_points")]
    public List<MarketPricePoint> DailyPoints { get; init; } = [];

    [JsonPropertyName("intraday_points")]
    public List<MarketPricePoint> IntradayPoints { get; init; } = [];

    public DateTime LoadedAt { get; set; } = DateTime.Now;

    public bool HasData => DailyPoints.Count > 0 || IntradayPoints.Count > 0;

    public bool HasError => string.Equals(Status, "error", StringComparison.OrdinalIgnoreCase);

    public bool UsesCachedData =>
        string.Equals(Status, "cached", StringComparison.OrdinalIgnoreCase)
        || string.Equals(Status, "cached_error_fallback", StringComparison.OrdinalIgnoreCase);

    public MarketPricePoint? LastPoint =>
        IntradayPoints.OrderBy(point => point.Timestamp).LastOrDefault()
        ?? DailyPoints.OrderBy(point => point.Timestamp).LastOrDefault();
}

public sealed class MarketPricePoint
{
    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; init; }

    [JsonPropertyName("open")]
    public double? Open { get; init; }

    [JsonPropertyName("high")]
    public double? High { get; init; }

    [JsonPropertyName("low")]
    public double? Low { get; init; }

    [JsonPropertyName("close")]
    public double? Close { get; init; }

    [JsonPropertyName("volume")]
    public double? Volume { get; init; }
}

public sealed class MarketRangeChange
{
    public MarketTimeRange Range { get; init; }

    public double? StartClose { get; init; }

    public double? EndClose { get; init; }

    public double AbsoluteChange { get; init; }

    public double PercentChange { get; init; }
}

public enum MarketTimeRange
{
    OneDay,
    OneWeek,
    OneMonth,
    SixMonths,
    OneYear,
    Max,
}
