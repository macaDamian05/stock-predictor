using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public interface INewsProvider
{
    string ProviderLabel { get; }

    bool IsDemoData { get; }

    Task<IReadOnlyList<NewsItem>> GetNewsAsync(CancellationToken cancellationToken = default);
}
