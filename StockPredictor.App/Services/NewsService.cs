using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class NewsService
{
    public const string AllCategories = "Alle Kategorien";
    public const string AllTickers = "Alle Ticker";

    private readonly INewsProvider _provider;

    public NewsService(INewsProvider provider)
    {
        _provider = provider;
    }

    public async Task<NewsFeedSnapshot> GetSnapshotAsync(NewsQuery? query = null, CancellationToken cancellationToken = default)
    {
        var normalizedQuery = query ?? new NewsQuery();
        var requestedCategory = NormalizeFilter(normalizedQuery.Category, AllCategories);
        var requestedTicker = NormalizeFilter(normalizedQuery.Ticker, AllTickers);

        var allItems = (await _provider.GetNewsAsync(cancellationToken))
            .OrderByDescending(item => item.PublishedAt)
            .ToList();

        var categories = allItems
            .Select(item => item.Category)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(category => category)
            .Prepend(AllCategories)
            .ToList();

        var tickers = allItems
            .SelectMany(item => item.AffectedTickers)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(ticker => ticker)
            .Prepend(AllTickers)
            .ToList();

        var selectedCategory = categories.Contains(requestedCategory, StringComparer.OrdinalIgnoreCase)
            ? requestedCategory
            : AllCategories;

        var selectedTicker = tickers.Contains(requestedTicker, StringComparer.OrdinalIgnoreCase)
            ? requestedTicker
            : AllTickers;

        IEnumerable<NewsItem> filteredItems = allItems;

        if (!string.Equals(selectedCategory, AllCategories, StringComparison.OrdinalIgnoreCase))
        {
            filteredItems = filteredItems.Where(item =>
                string.Equals(item.Category, selectedCategory, StringComparison.OrdinalIgnoreCase));
        }

        if (!string.Equals(selectedTicker, AllTickers, StringComparison.OrdinalIgnoreCase))
        {
            filteredItems = filteredItems.Where(item =>
                item.AffectedTickers.Any(ticker =>
                    string.Equals(ticker, selectedTicker, StringComparison.OrdinalIgnoreCase)));
        }

        if (normalizedQuery.MaxItems is > 0)
        {
            filteredItems = filteredItems.Take(normalizedQuery.MaxItems.Value);
        }

        return new NewsFeedSnapshot
        {
            ProviderLabel = _provider.ProviderLabel,
            IsDemoData = _provider.IsDemoData,
            ContextNotice = _provider.IsDemoData
                ? "Aktuell werden Demo-News aus seriösen Quellenmustern gezeigt, damit die Oberfläche ohne API-Schlüssel funktioniert."
                : "Die News-Ansicht zeigt aktuell verfügbare Quellen als zusätzlichen Kontext.",
            ModelUsageNotice = "News dienen aktuell nur als Kontext und werden noch nicht im Modell verwendet.",
            SelectedCategory = selectedCategory,
            SelectedTicker = selectedTicker,
            AvailableCategories = categories,
            AvailableTickers = tickers,
            Items = filteredItems.ToList()
        };
    }

    private static string NormalizeFilter(string? value, string fallback)
    {
        return string.IsNullOrWhiteSpace(value) ? fallback : value.Trim();
    }
}
