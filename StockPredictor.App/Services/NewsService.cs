using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class NewsService(INewsProvider provider)
{
    public const string AllCategories = "Alle Kategorien";
    public const string AllTickers = "Alle Ticker";

    public async Task<NewsFeedSnapshot> GetSnapshotAsync(NewsQuery? query = null, CancellationToken cancellationToken = default)
    {
        var normalizedQuery = query ?? new NewsQuery();
        var requestedCategory = NormalizeFilter(normalizedQuery.Category, AllCategories);
        var requestedTicker = NormalizeFilter(normalizedQuery.Ticker, AllTickers);
        var preferredTickers = (normalizedQuery.PreferredTickers ?? [])
            .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
            .Select(ticker => ticker.Trim().ToUpperInvariant())
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();

        var providerResult = await provider.GetNewsAsync(cancellationToken);
        var allItems = providerResult.Items
            .OrderByDescending(item => item.PublishedAt)
            .ToList();

        var categories = allItems
            .Select(item => item.Category)
            .Where(category => !string.IsNullOrWhiteSpace(category))
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
        else if (normalizedQuery.PreferTickerMatches && preferredTickers.Length > 0)
        {
            filteredItems = filteredItems
                .OrderByDescending(item => item.AffectedTickers.Any(ticker =>
                    preferredTickers.Contains(ticker, StringComparer.OrdinalIgnoreCase)))
                .ThenByDescending(item => item.PublishedAt);
        }

        if (normalizedQuery.MaxItems is > 0)
        {
            filteredItems = filteredItems.Take(normalizedQuery.MaxItems.Value);
        }

        return new NewsFeedSnapshot
        {
            ProviderLabel = providerResult.ProviderLabel,
            IsDemoData = providerResult.IsDemoData,
            IsExternalData = providerResult.IsExternalData,
            LoadStatus = providerResult.LoadStatus,
            ContextNotice = BuildContextNotice(providerResult),
            ModelUsageNotice = "News dienen aktuell nur als Kontext und werden noch nicht automatisch in die Modellprognose übernommen.",
            StatusNotice = providerResult.StatusNotice,
            SelectedCategory = selectedCategory,
            SelectedTicker = selectedTicker,
            AvailableCategories = categories,
            AvailableTickers = tickers,
            Items = filteredItems.ToList(),
            SourceWarnings = providerResult.SourceWarnings,
        };
    }

    private static string BuildContextNotice(NewsProviderResult result)
    {
        return result.LoadStatus switch
        {
            NewsLoadStatus.Demo => "Demo-Modus ist aktiv. Diese Einträge sind klar als Demo markiert und keine echten Artikel.",
            NewsLoadStatus.SourceUnavailable => "Externe Quellen konnten aktuell nicht erreicht werden. Die App bleibt nutzbar und zeigt keinen erfundenen Ersatz an.",
            NewsLoadStatus.NoItems => "Es wurden aktuell keine verwertbaren News-Artikel geladen.",
            _ => "Die News-Ansicht zeigt aktuell verfügbare externe Quellen als zusätzlichen Kontext.",
        };
    }

    private static string NormalizeFilter(string? value, string fallback)
    {
        return string.IsNullOrWhiteSpace(value) ? fallback : value.Trim();
    }
}
