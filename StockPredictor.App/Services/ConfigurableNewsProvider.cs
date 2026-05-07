using Microsoft.Extensions.Options;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class ConfigurableNewsProvider(
    IOptions<NewsOptions> options,
    RssNewsProvider rssNewsProvider,
    MockNewsProvider mockNewsProvider) : INewsProvider
{
    public string ProviderLabel => ResolveProvider().ProviderLabel;

    public bool IsDemoData => ResolveProvider().IsDemoData;

    public Task<NewsProviderResult> GetNewsAsync(CancellationToken cancellationToken = default)
    {
        return ResolveProvider().GetNewsAsync(cancellationToken);
    }

    private INewsProvider ResolveProvider()
    {
        return options.Value.Mode.Trim().ToLowerInvariant() switch
        {
            "demo" => mockNewsProvider,
            _ => rssNewsProvider,
        };
    }
}
