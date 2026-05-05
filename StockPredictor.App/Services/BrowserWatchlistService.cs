using Microsoft.JSInterop;

namespace StockPredictor.App.Services;

public sealed class BrowserWatchlistService(IJSRuntime jsRuntime)
{
    public async Task<IReadOnlyList<string>> GetAsync(CancellationToken cancellationToken = default)
    {
        var tickers = await jsRuntime.InvokeAsync<string[]>(
            "stockPredictorWatchlist.get",
            cancellationToken);

        return (tickers ?? [])
            .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
            .Select(ticker => ticker.Trim().ToUpperInvariant())
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }

    public async Task SaveAsync(IEnumerable<string> tickers, CancellationToken cancellationToken = default)
    {
        var normalizedTickers = tickers
            .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
            .Select(ticker => ticker.Trim().ToUpperInvariant())
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();

        await jsRuntime.InvokeVoidAsync(
            "stockPredictorWatchlist.set",
            cancellationToken,
            normalizedTickers);
    }
}
