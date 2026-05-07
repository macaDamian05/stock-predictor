using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public interface INewsProvider
{
    string ProviderLabel { get; }

    bool IsDemoData { get; }

    Task<NewsProviderResult> GetNewsAsync(CancellationToken cancellationToken = default);
}
