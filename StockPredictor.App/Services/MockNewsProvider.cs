using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class MockNewsProvider : INewsProvider
{
    private static readonly IReadOnlyList<NewsItem> DemoItems =
    [
        new()
        {
            Id = "demo-market-context-1",
            Title = "Demo: Beispielhafte Marktmeldung für die Oberfläche",
            Source = "Lokaler Demo-Datensatz",
            PublishedAt = new DateTime(2026, 5, 7, 9, 0, 0, DateTimeKind.Local),
            Url = string.Empty,
            Category = "Demo",
            AffectedTickers = ["AAPL", "MSFT"],
            Summary = "Diese Meldung dient nur als klar markierter Demo-Platzhalter und verweist bewusst nicht auf einen echten Artikel.",
            IsDemo = true,
            IsExternal = false,
            LoadStatus = NewsLoadStatus.Demo,
        },
        new()
        {
            Id = "demo-market-context-2",
            Title = "Demo: Beispielhafte Watchlist-News ohne Originalquelle",
            Source = "Lokaler Demo-Datensatz",
            PublishedAt = new DateTime(2026, 5, 7, 8, 30, 0, DateTimeKind.Local),
            Url = string.Empty,
            Category = "Demo",
            AffectedTickers = ["TSLA"],
            Summary = "Demo-Modus bleibt lokal, ohne erfundene Mediennamen und ohne scheinbar echte Artikel-Links.",
            IsDemo = true,
            IsExternal = false,
            LoadStatus = NewsLoadStatus.Demo,
        },
    ];

    public string ProviderLabel => "Lokaler Demo-Datensatz";

    public bool IsDemoData => true;

    public Task<NewsProviderResult> GetNewsAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(new NewsProviderResult
        {
            ProviderLabel = ProviderLabel,
            IsDemoData = true,
            IsExternalData = false,
            LoadStatus = NewsLoadStatus.Demo,
            StatusNotice = "Demo-Modus ist aktiv. Diese Einträge sind keine echten Artikel.",
            Items = DemoItems.ToList(),
        });
    }
}
