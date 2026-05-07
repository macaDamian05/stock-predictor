namespace StockPredictor.App.Models;

public sealed class NewsProviderResult
{
    public string ProviderLabel { get; init; } = string.Empty;

    public bool IsDemoData { get; init; }

    public bool IsExternalData { get; init; }

    public NewsLoadStatus LoadStatus { get; init; } = NewsLoadStatus.NoItems;

    public string StatusNotice { get; init; } = string.Empty;

    public List<string> SourceWarnings { get; init; } = [];

    public List<NewsItem> Items { get; init; } = [];
}
