namespace StockPredictor.App.Models;

public sealed class NewsFeedSnapshot
{
    public string ProviderLabel { get; init; } = string.Empty;

    public bool IsDemoData { get; init; }

    public bool IsExternalData { get; init; }

    public NewsLoadStatus LoadStatus { get; init; } = NewsLoadStatus.NoItems;

    public string ContextNotice { get; init; } = string.Empty;

    public string ModelUsageNotice { get; init; } = string.Empty;

    public string StatusNotice { get; init; } = string.Empty;

    public string SelectedCategory { get; init; } = string.Empty;

    public string SelectedTicker { get; init; } = string.Empty;

    public List<string> AvailableCategories { get; init; } = [];

    public List<string> AvailableTickers { get; init; } = [];

    public List<NewsItem> Items { get; init; } = [];

    public List<string> SourceWarnings { get; init; } = [];
}
