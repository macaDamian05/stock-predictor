namespace StockPredictor.App.Models;

public sealed class NewsItem
{
    public string Id { get; init; } = string.Empty;

    public string Title { get; init; } = string.Empty;

    public string Source { get; init; } = string.Empty;

    public DateTime PublishedAt { get; init; }

    public string Link { get; init; } = string.Empty;

    public string Category { get; init; } = string.Empty;

    public List<string> AffectedTickers { get; init; } = [];

    public bool IsDemo { get; init; }
}
