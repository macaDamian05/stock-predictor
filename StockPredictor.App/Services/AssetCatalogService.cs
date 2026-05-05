using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class AssetCatalogService
{
    private static readonly IReadOnlyDictionary<string, KnownAssetInfo> KnownAssets =
        new Dictionary<string, KnownAssetInfo>(StringComparer.OrdinalIgnoreCase)
        {
            ["AAPL"] = new("Apple Inc.", "Aktie"),
            ["TSLA"] = new("Tesla, Inc.", "Aktie"),
            ["MSFT"] = new("Microsoft Corp.", "Aktie"),
            ["NVDA"] = new("NVIDIA Corp.", "Aktie"),
            ["JPM"] = new("JPMorgan Chase & Co.", "Aktie"),
            ["XOM"] = new("Exxon Mobil Corp.", "Aktie"),
            ["KO"] = new("The Coca-Cola Company", "Aktie"),
            ["PG"] = new("Procter & Gamble Co.", "Aktie"),
            ["SAP.DE"] = new("SAP SE", "Aktie"),
            ["DOU.DE"] = new("Douglas AG", "Aktie"),
            ["ENR.DE"] = new("Siemens Energy AG", "Aktie"),
            ["DTE.DE"] = new("Deutsche Telekom AG", "Aktie"),
            ["SPY"] = new("SPDR S&P 500 ETF", "ETF"),
            ["QQQ"] = new("Invesco QQQ Trust", "ETF"),
            ["VTI"] = new("Vanguard Total Stock Market ETF", "ETF"),
            ["IWM"] = new("iShares Russell 2000 ETF", "ETF"),
            ["DIA"] = new("SPDR Dow Jones Industrial Average ETF", "ETF"),
            ["XLK"] = new("Technology Select Sector SPDR Fund", "ETF"),
            ["XLF"] = new("Financial Select Sector SPDR Fund", "ETF"),
            ["XLE"] = new("Energy Select Sector SPDR Fund", "ETF"),
            ["XLP"] = new("Consumer Staples Select Sector SPDR Fund", "ETF"),
            ["XLV"] = new("Health Care Select Sector SPDR Fund", "ETF"),
        };

    public IReadOnlyList<AssetCatalogEntry> BuildEntries(DashboardPayload payload)
    {
        var featuredOrder = payload.FeaturedTickers
            .Select((ticker, index) => new { Ticker = NormalizeTicker(ticker.Ticker), Index = index })
            .ToDictionary(entry => entry.Ticker, entry => entry.Index, StringComparer.OrdinalIgnoreCase);
        var rankingOrder = payload.CompanyRanking
            .Select((entry, index) => new { Ticker = NormalizeTicker(entry.Ticker), Index = index })
            .ToDictionary(entry => entry.Ticker, entry => entry.Index, StringComparer.OrdinalIgnoreCase);
        var featuredByTicker = payload.FeaturedTickers.ToDictionary(
            ticker => NormalizeTicker(ticker.Ticker),
            StringComparer.OrdinalIgnoreCase);
        var rankingByTicker = payload.CompanyRanking.ToDictionary(
            entry => NormalizeTicker(entry.Ticker),
            StringComparer.OrdinalIgnoreCase);
        var tickers = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var ticker in payload.FeaturedTickers.Select(entry => entry.Ticker))
        {
            tickers.Add(NormalizeTicker(ticker));
        }

        foreach (var ticker in payload.CompanyRanking.Select(entry => entry.Ticker))
        {
            tickers.Add(NormalizeTicker(ticker));
        }

        foreach (var ticker in payload.MultiAssetSummaries.SelectMany(summary => summary.Tickers))
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
        };
    }

    public IReadOnlyList<AssetCatalogEntry> Search(IReadOnlyList<AssetCatalogEntry> entries, string query)
    {
        if (string.IsNullOrWhiteSpace(query))
        {
            return entries.Take(8).ToArray();
        }

        var normalizedQuery = query.Trim();

        return entries
            .Where(entry =>
                entry.Ticker.Contains(normalizedQuery, StringComparison.OrdinalIgnoreCase)
                || (!string.IsNullOrWhiteSpace(entry.DisplayName)
                    && entry.DisplayName.Contains(normalizedQuery, StringComparison.OrdinalIgnoreCase))
                || (!string.IsNullOrWhiteSpace(entry.AssetType)
                    && entry.AssetType.Contains(normalizedQuery, StringComparison.OrdinalIgnoreCase)))
            .OrderByDescending(entry => entry.Ticker.Equals(normalizedQuery, StringComparison.OrdinalIgnoreCase))
            .ThenByDescending(entry => entry.HasPreparedPayloadData)
            .ThenBy(entry => entry.Ticker, StringComparer.OrdinalIgnoreCase)
            .Take(8)
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

    private sealed record KnownAssetInfo(string DisplayName, string AssetType);
}
