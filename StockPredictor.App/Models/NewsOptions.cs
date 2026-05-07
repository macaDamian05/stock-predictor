namespace StockPredictor.App.Models;

public sealed class NewsOptions
{
    public const string SectionName = "News";

    public string Mode { get; init; } = "external";

    public int TimeoutSeconds { get; init; } = 12;

    public int MaxItemsPerSource { get; init; } = 8;

    public List<NewsSourceDefinition> Sources { get; init; } = [];
}

public sealed class NewsSourceDefinition
{
    public string Name { get; init; } = string.Empty;

    public string FeedUrl { get; init; } = string.Empty;

    public string Category { get; init; } = "Markt";

    public bool Enabled { get; init; } = true;
}
