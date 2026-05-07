using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class AssetCatalogService
{
    private static readonly IReadOnlyDictionary<string, KnownAssetInfo> KnownAssets =
        new Dictionary<string, KnownAssetInfo>(StringComparer.OrdinalIgnoreCase)
        {
            ["AAPL"] = new("Apple Inc.", "Aktie", ["apple", "apple inc"]),
            ["TSLA"] = new("Tesla, Inc.", "Aktie", ["tesla", "tesla motors"]),
            ["MSFT"] = new("Microsoft Corp.", "Aktie", ["microsoft", "microsoft corporation"]),
            ["NVDA"] = new("NVIDIA Corp.", "Aktie", ["nvidia", "nvidia corporation"]),
            ["JPM"] = new("JPMorgan Chase & Co.", "Aktie", ["jpmorgan", "jp morgan"]),
            ["XOM"] = new("Exxon Mobil Corp.", "Aktie", ["exxon", "exxon mobil"]),
            ["KO"] = new("The Coca-Cola Company", "Aktie", ["coca cola", "coke"]),
            ["PG"] = new("Procter & Gamble Co.", "Aktie", ["procter and gamble", "p&g"]),
            ["SAP.DE"] = new("SAP SE", "Aktie", ["sap"]),
            ["SIE.DE"] = new("Siemens AG", "Aktie", ["siemens"]),
            ["DOU.DE"] = new("Douglas AG", "Aktie", ["douglas"]),
            ["ENR.DE"] = new("Siemens Energy AG", "Aktie", ["siemens energy", "energy"]),
            ["DTE.DE"] = new("Deutsche Telekom AG", "Aktie", ["deutsche telekom", "telekom"]),
            ["SPY"] = new("SPDR S&P 500 ETF", "ETF", ["sp500", "s&p 500", "spdr s&p 500"]),
            ["QQQ"] = new("Invesco QQQ Trust", "ETF", ["nasdaq etf", "qqq etf"]),
            ["VTI"] = new("Vanguard Total Stock Market ETF", "ETF", ["vanguard total stock market"]),
            ["IWM"] = new("iShares Russell 2000 ETF", "ETF", ["russell 2000", "small cap etf"]),
            ["DIA"] = new("SPDR Dow Jones Industrial Average ETF", "ETF", ["dow etf", "dow jones etf"]),
            ["XLK"] = new("Technology Select Sector SPDR Fund", "ETF", ["tech etf", "technology etf"]),
            ["XLF"] = new("Financial Select Sector SPDR Fund", "ETF", ["financial etf", "finance etf"]),
            ["XLE"] = new("Energy Select Sector SPDR Fund", "ETF", ["energy etf"]),
            ["XLP"] = new("Consumer Staples Select Sector SPDR Fund", "ETF", ["consumer staples etf"]),
            ["XLV"] = new("Health Care Select Sector SPDR Fund", "ETF", ["health care etf", "healthcare etf"]),
        };

    public IReadOnlyList<AssetCatalogEntry> BuildEntries(DashboardPayload? payload)
    {
        var featuredTickers = payload?.FeaturedTickers ?? [];
        var companyRanking = payload?.CompanyRanking ?? [];
        var multiAssetSummaries = payload?.MultiAssetSummaries ?? [];

        var featuredOrder = featuredTickers
            .Select((ticker, index) => new { Ticker = NormalizeTicker(ticker.Ticker), Index = index })
            .ToDictionary(entry => entry.Ticker, entry => entry.Index, StringComparer.OrdinalIgnoreCase);
        var rankingOrder = companyRanking
            .Select((entry, index) => new { Ticker = NormalizeTicker(entry.Ticker), Index = index })
            .ToDictionary(entry => entry.Ticker, entry => entry.Index, StringComparer.OrdinalIgnoreCase);
        var featuredByTicker = featuredTickers.ToDictionary(
            ticker => NormalizeTicker(ticker.Ticker),
            StringComparer.OrdinalIgnoreCase);
        var rankingByTicker = companyRanking.ToDictionary(
            entry => NormalizeTicker(entry.Ticker),
            StringComparer.OrdinalIgnoreCase);
        var tickers = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var ticker in featuredTickers.Select(entry => entry.Ticker))
        {
            tickers.Add(NormalizeTicker(ticker));
        }

        foreach (var ticker in companyRanking.Select(entry => entry.Ticker))
        {
            tickers.Add(NormalizeTicker(ticker));
        }

        foreach (var ticker in multiAssetSummaries.SelectMany(summary => summary.Tickers))
        {
            tickers.Add(NormalizeTicker(ticker));
        }

        foreach (var ticker in KnownAssets.Keys)
        {
            tickers.Add(NormalizeTicker(ticker));
        }

        return tickers
            .Select(ticker =>
            {
                featuredByTicker.TryGetValue(ticker, out var featuredTicker);
                rankingByTicker.TryGetValue(ticker, out var rankingEntry);
                KnownAssets.TryGetValue(ticker, out var knownAsset);

                return new AssetCatalogEntry
                {
                    Ticker = ticker,
                    DisplayName = knownAsset?.DisplayName,
                    AssetType = knownAsset?.AssetType ?? InferAssetType(ticker),
                    LastClose = featuredTicker?.LastClose ?? rankingEntry?.LastClose,
                    LastCloseDate = featuredTicker?.LastCloseDate,
                    ForecastAvailable = featuredTicker?.ForecastPath.Count > 0,
                    ForecastHorizonChangePct = featuredTicker?.ForecastHorizonChangePct,
                    SearchKeywords = BuildSearchKeywords(ticker, knownAsset),
                    FeaturedTicker = featuredTicker,
                    RankingEntry = rankingEntry,
                };
            })
            .OrderBy(entry => featuredOrder.TryGetValue(entry.Ticker, out var index) ? index : int.MaxValue)
            .ThenBy(entry => rankingOrder.TryGetValue(entry.Ticker, out var index) ? index : int.MaxValue)
            .ThenByDescending(entry => entry.HasPreparedPayloadData)
            .ThenBy(entry => entry.Ticker, StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }

    public AssetCatalogEntry? FindEntry(DashboardPayload payload, string tickerSymbol)
    {
        var normalizedTicker = NormalizeTicker(tickerSymbol);
        return BuildEntries(payload).FirstOrDefault(entry =>
            string.Equals(entry.Ticker, normalizedTicker, StringComparison.OrdinalIgnoreCase));
    }

    public AssetCatalogEntry CreatePlaceholderEntry(string tickerSymbol)
    {
        var normalizedTicker = NormalizeTicker(tickerSymbol);
        KnownAssets.TryGetValue(normalizedTicker, out var knownAsset);

        return new AssetCatalogEntry
        {
            Ticker = normalizedTicker,
            DisplayName = knownAsset?.DisplayName,
            AssetType = knownAsset?.AssetType ?? InferAssetType(normalizedTicker),
            ForecastAvailable = false,
            SearchKeywords = BuildSearchKeywords(normalizedTicker, knownAsset),
        };
    }

    public IReadOnlyList<AssetCatalogEntry> Search(IReadOnlyList<AssetCatalogEntry> entries, string query)
    {
        if (string.IsNullOrWhiteSpace(query))
        {
            return entries.Take(8).ToArray();
        }

        var normalizedQuery = query.Trim();
        var normalizedTicker = NormalizeTicker(normalizedQuery);

        return entries
            .Where(entry =>
                entry.Ticker.Contains(normalizedTicker, StringComparison.OrdinalIgnoreCase)
                || (!string.IsNullOrWhiteSpace(entry.DisplayName)
                    && entry.DisplayName.Contains(normalizedQuery, StringComparison.OrdinalIgnoreCase))
                || (!string.IsNullOrWhiteSpace(entry.AssetType)
                    && entry.AssetType.Contains(normalizedQuery, StringComparison.OrdinalIgnoreCase))
                || entry.SearchKeywords.Any(keyword =>
                    keyword.Contains(normalizedQuery, StringComparison.OrdinalIgnoreCase)))
            .OrderByDescending(entry => entry.Ticker.Equals(normalizedTicker, StringComparison.OrdinalIgnoreCase))
            .ThenByDescending(entry => entry.SearchKeywords.Any(keyword =>
                keyword.Equals(normalizedQuery, StringComparison.OrdinalIgnoreCase)))
            .ThenByDescending(entry => string.Equals(entry.DisplayName, normalizedQuery, StringComparison.OrdinalIgnoreCase))
            .ThenByDescending(entry => entry.HasPreparedPayloadData)
            .ThenBy(entry => entry.Ticker, StringComparer.OrdinalIgnoreCase)
            .Take(12)
            .ToArray();
    }

    public string ResolveTicker(string query, IReadOnlyList<AssetCatalogEntry> entries)
    {
        var normalizedTicker = NormalizeTicker(query);
        var exactTicker = entries.FirstOrDefault(entry =>
            string.Equals(entry.Ticker, normalizedTicker, StringComparison.OrdinalIgnoreCase));

        if (exactTicker is not null)
        {
            return exactTicker.Ticker;
        }

        var exactAlias = entries.FirstOrDefault(entry =>
            entry.SearchKeywords.Any(keyword => string.Equals(keyword, query.Trim(), StringComparison.OrdinalIgnoreCase)));

        if (exactAlias is not null)
        {
            return exactAlias.Ticker;
        }

        return Search(entries, query).FirstOrDefault()?.Ticker ?? normalizedTicker;
    }

    public IReadOnlyList<string> InferTickersFromText(string? text)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return [];
        }

        return KnownAssets
            .Where(pair =>
                BuildSearchKeywords(pair.Key, pair.Value).Any(keyword =>
                    keyword.Length >= 3
                    && text.Contains(keyword, StringComparison.OrdinalIgnoreCase)))
            .Select(pair => pair.Key)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }

    public string NormalizeTicker(string tickerSymbol)
    {
        return (tickerSymbol ?? string.Empty).Trim().ToUpperInvariant();
    }

    private static string InferAssetType(string tickerSymbol)
    {
        if (KnownAssets.TryGetValue(tickerSymbol, out var knownAsset))
        {
            return knownAsset.AssetType;
        }

        if (tickerSymbol.EndsWith(".DE", StringComparison.OrdinalIgnoreCase))
        {
            return "Aktie";
        }

        return "Asset";
    }

    private static IReadOnlyList<string> BuildSearchKeywords(string ticker, KnownAssetInfo? knownAsset)
    {
        var keywords = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            ticker,
        };

        if (!string.IsNullOrWhiteSpace(knownAsset?.DisplayName))
        {
            keywords.Add(knownAsset.DisplayName);
        }

        if (knownAsset?.Aliases is not null)
        {
            foreach (var alias in knownAsset.Aliases)
            {
                if (!string.IsNullOrWhiteSpace(alias))
                {
                    keywords.Add(alias);
                }
            }
        }

        return keywords.ToArray();
    }

    private sealed record KnownAssetInfo(string DisplayName, string AssetType, IReadOnlyList<string> Aliases);
}
