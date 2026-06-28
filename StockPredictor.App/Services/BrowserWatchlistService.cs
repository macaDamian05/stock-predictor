using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class BrowserWatchlistService(
    LocalUserProfileService profileService,
    AssetCatalogService assetCatalogService)
{
    public async Task<IReadOnlyList<string>> GetAsync(CancellationToken cancellationToken = default)
    {
        var profile = await profileService.GetProfileAsync(false, cancellationToken);
        return profile.Watchlist
            .Select(item => NormalizeTicker(item.Symbol))
            .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }

    public async Task SaveAsync(IEnumerable<string> tickers, CancellationToken cancellationToken = default)
    {
        var profile = await profileService.GetProfileAsync(false, cancellationToken);
        var existingItems = profile.Watchlist.ToDictionary(
            item => NormalizeTicker(item.Symbol),
            StringComparer.OrdinalIgnoreCase);

        profile.Watchlist = tickers
            .Select(NormalizeTicker)
            .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Select(ticker =>
            {
                if (existingItems.TryGetValue(ticker, out var existingItem))
                {
                    return existingItem;
                }

                var entry = assetCatalogService.CreatePlaceholderEntry(ticker);
                return new WatchlistItem
                {
                    Symbol = ticker,
                    Name = entry.DisplayName,
                    AssetType = entry.AssetType,
                    AddedAt = DateTime.Now,
                };
            })
            .ToList();

        await profileService.SaveProfileAsync(profile, cancellationToken);
    }

    public async Task<IReadOnlyList<WatchlistItem>> GetItemsAsync(CancellationToken cancellationToken = default)
    {
        return await profileService.GetWatchlistAsync(cancellationToken);
    }

    public async Task AddOrUpdateAsync(AssetCatalogEntry asset, CancellationToken cancellationToken = default)
    {
        await profileService.AddOrUpdateWatchlistItemAsync(new WatchlistItem
        {
            Symbol = asset.Ticker,
            Name = asset.DisplayName,
            AssetType = asset.AssetType,
            AddedAt = DateTime.Now,
        }, cancellationToken);
    }

    public async Task RemoveAsync(string ticker, CancellationToken cancellationToken = default)
    {
        await profileService.RemoveWatchlistItemAsync(ticker, cancellationToken);
    }

    private static string NormalizeTicker(string ticker)
    {
        return (ticker ?? string.Empty).Trim().ToUpperInvariant();
    }
}
