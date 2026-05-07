using System.Text.RegularExpressions;
using System.Xml.Linq;
using Microsoft.Extensions.Options;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class RssNewsProvider(
    HttpClient httpClient,
    IOptions<NewsOptions> options,
    AssetCatalogService assetCatalogService,
    ILogger<RssNewsProvider> logger) : INewsProvider
{
    private static readonly Regex HtmlTagRegex = new("<.*?>", RegexOptions.Compiled);
    private static readonly string[] GenericSectionSegments =
    [
        "markets",
        "market",
        "business",
        "technology",
        "world",
        "economy",
        "news",
        "latest",
        "feed",
        "rss",
    ];

    public string ProviderLabel => "Externe RSS-/Atom-Feeds";

    public bool IsDemoData => false;

    public async Task<NewsProviderResult> GetNewsAsync(CancellationToken cancellationToken = default)
    {
        var enabledSources = options.Value.Sources
            .Where(source => source.Enabled && !string.IsNullOrWhiteSpace(source.FeedUrl))
            .ToArray();

        if (enabledSources.Length == 0)
        {
            return new NewsProviderResult
            {
                ProviderLabel = ProviderLabel,
                IsDemoData = false,
                IsExternalData = true,
                LoadStatus = NewsLoadStatus.NoItems,
                StatusNotice = "Es sind aktuell keine News-Quellen konfiguriert.",
            };
        }

        var items = new List<NewsItem>();
        var warnings = new List<string>();
        var successfulSources = 0;

        foreach (var source in enabledSources)
        {
            try
            {
                using var response = await httpClient.GetAsync(source.FeedUrl, cancellationToken);
                response.EnsureSuccessStatusCode();

                var xml = await response.Content.ReadAsStringAsync(cancellationToken);
                var sourceItems = ParseFeed(source, xml)
                    .Take(Math.Max(1, options.Value.MaxItemsPerSource))
                    .ToArray();

                items.AddRange(sourceItems);
                successfulSources++;
            }
            catch (Exception exception)
            {
                logger.LogWarning(exception, "Failed to load news source {Source} from {Url}", source.Name, source.FeedUrl);
                warnings.Add($"{source.Name}: Quelle nicht erreichbar");
            }
        }

        items = items
            .Where(item => !string.IsNullOrWhiteSpace(item.Title))
            .GroupBy(item => string.IsNullOrWhiteSpace(item.Url) ? item.Title : item.Url, StringComparer.OrdinalIgnoreCase)
            .Select(group => group.OrderByDescending(item => item.PublishedAt).First())
            .OrderByDescending(item => item.PublishedAt)
            .ToList();

        var loadStatus = items.Count > 0
            ? NewsLoadStatus.Loaded
            : successfulSources == 0
                ? NewsLoadStatus.SourceUnavailable
                : NewsLoadStatus.NoItems;

        var statusNotice = loadStatus switch
        {
            NewsLoadStatus.Loaded when warnings.Count > 0 => "Einige Quellen konnten nicht geladen werden. Die verfügbaren Artikel werden trotzdem angezeigt.",
            NewsLoadStatus.Loaded => "Echte News-Artikel aus konfigurierten Quellen wurden geladen.",
            NewsLoadStatus.SourceUnavailable => "Zurzeit konnten keine externen News-Quellen erreicht werden.",
            _ => "Die konfigurierten Quellen lieferten aktuell keine verwertbaren Artikel.",
        };

        return new NewsProviderResult
        {
            ProviderLabel = ProviderLabel,
            IsDemoData = false,
            IsExternalData = true,
            LoadStatus = loadStatus,
            StatusNotice = statusNotice,
            SourceWarnings = warnings,
            Items = items,
        };
    }

    private IEnumerable<NewsItem> ParseFeed(NewsSourceDefinition source, string xml)
    {
        var document = XDocument.Parse(xml, LoadOptions.PreserveWhitespace);

        if (document.Root is null)
        {
            yield break;
        }

        if (string.Equals(document.Root.Name.LocalName, "feed", StringComparison.OrdinalIgnoreCase))
        {
            foreach (var item in ParseAtomFeed(source, document.Root))
            {
                yield return item;
            }

            yield break;
        }

        foreach (var item in document.Descendants().Where(node => string.Equals(node.Name.LocalName, "item", StringComparison.OrdinalIgnoreCase)))
        {
            var title = item.Elements().FirstOrDefault(node => node.Name.LocalName == "title")?.Value?.Trim() ?? string.Empty;
            var link = item.Elements().FirstOrDefault(node => node.Name.LocalName == "link")?.Value?.Trim() ?? string.Empty;
            var publishedRaw = item.Elements().FirstOrDefault(node => node.Name.LocalName is "pubDate" or "published" or "updated")?.Value;
            var summary = item.Elements().FirstOrDefault(node => node.Name.LocalName is "description" or "summary")?.Value;
            var category = item.Elements().FirstOrDefault(node => node.Name.LocalName == "category")?.Value?.Trim();

            if (!LooksLikeConcreteArticleUrl(link))
            {
                continue;
            }

            yield return BuildNewsItem(
                source,
                title,
                link,
                publishedRaw,
                summary,
                category);
        }
    }

    private IEnumerable<NewsItem> ParseAtomFeed(NewsSourceDefinition source, XElement root)
    {
        foreach (var entry in root.Elements().Where(node => string.Equals(node.Name.LocalName, "entry", StringComparison.OrdinalIgnoreCase)))
        {
            var title = entry.Elements().FirstOrDefault(node => node.Name.LocalName == "title")?.Value?.Trim() ?? string.Empty;
            var link = entry.Elements()
                .FirstOrDefault(node =>
                    node.Name.LocalName == "link"
                    && string.Equals(node.Attribute("rel")?.Value ?? "alternate", "alternate", StringComparison.OrdinalIgnoreCase))
                ?.Attribute("href")?.Value?.Trim()
                ?? entry.Elements().FirstOrDefault(node => node.Name.LocalName == "link")?.Attribute("href")?.Value?.Trim()
                ?? string.Empty;
            var publishedRaw = entry.Elements().FirstOrDefault(node => node.Name.LocalName is "updated" or "published")?.Value;
            var summary = entry.Elements().FirstOrDefault(node => node.Name.LocalName is "summary" or "content")?.Value;
            var category = entry.Elements().FirstOrDefault(node => node.Name.LocalName == "category")?.Attribute("term")?.Value?.Trim();

            if (!LooksLikeConcreteArticleUrl(link))
            {
                continue;
            }

            yield return BuildNewsItem(
                source,
                title,
                link,
                publishedRaw,
                summary,
                category);
        }
    }

    private NewsItem BuildNewsItem(
        NewsSourceDefinition source,
        string title,
        string link,
        string? publishedRaw,
        string? summary,
        string? category)
    {
        var cleanSummary = StripHtml(summary);
        var publishedAt = DateTime.TryParse(publishedRaw, out var parsedPublishedAt)
            ? parsedPublishedAt.ToLocalTime()
            : DateTime.Now;
        var textForTickerInference = string.Join(" ", [title, cleanSummary]);

        return new NewsItem
        {
            Id = $"{source.Name}:{link}".ToLowerInvariant(),
            Title = title,
            Source = source.Name,
            PublishedAt = publishedAt,
            Url = link,
            Category = string.IsNullOrWhiteSpace(category) ? source.Category : category.Trim(),
            AffectedTickers = assetCatalogService.InferTickersFromText(textForTickerInference).ToList(),
            Summary = cleanSummary,
            IsDemo = false,
            IsExternal = true,
            LoadStatus = NewsLoadStatus.Loaded,
        };
    }

    private static string StripHtml(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return string.Empty;
        }

        var cleaned = HtmlTagRegex.Replace(value, " ");
        return System.Net.WebUtility.HtmlDecode(cleaned).Trim();
    }

    private static bool LooksLikeConcreteArticleUrl(string? value)
    {
        if (!Uri.TryCreate(value, UriKind.Absolute, out var uri))
        {
            return false;
        }

        if (!string.Equals(uri.Scheme, Uri.UriSchemeHttp, StringComparison.OrdinalIgnoreCase)
            && !string.Equals(uri.Scheme, Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        var trimmedPath = uri.AbsolutePath.Trim('/');
        if (string.IsNullOrWhiteSpace(trimmedPath))
        {
            return false;
        }

        var segments = trimmedPath
            .Split('/', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

        if (segments.Length == 1
            && GenericSectionSegments.Contains(segments[0], StringComparer.OrdinalIgnoreCase))
        {
            return false;
        }

        return true;
    }
}
