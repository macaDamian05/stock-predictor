using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class MockNewsProvider : INewsProvider
{
    private static readonly IReadOnlyList<NewsItem> DemoItems =
    [
        new()
        {
            Id = "reuters-demo-rates-tech",
            Title = "Beispiel: Renditeanstieg bei Staatsanleihen belastet große Technologiewerte",
            Source = "Reuters (Demo)",
            PublishedAt = new DateTime(2026, 5, 5, 8, 30, 0, DateTimeKind.Local),
            Link = "https://www.reuters.com/markets/",
            Category = "Markt",
            AffectedTickers = ["AAPL", "QQQ", "NVDA"],
            IsDemo = true
        },
        new()
        {
            Id = "ft-demo-ecb-industry",
            Title = "Beispiel: Zinsausblick in Europa stützt Industrie- und Softwarewerte",
            Source = "Financial Times (Demo)",
            PublishedAt = new DateTime(2026, 5, 5, 7, 45, 0, DateTimeKind.Local),
            Link = "https://www.ft.com/markets",
            Category = "Wirtschaft",
            AffectedTickers = ["SAP.DE", "DOU.DE"],
            IsDemo = true
        },
        new()
        {
            Id = "bloomberg-demo-ai-capex",
            Title = "Beispiel: Neue KI-Infrastrukturinvestitionen beleben den Technologiesektor",
            Source = "Bloomberg (Demo)",
            PublishedAt = new DateTime(2026, 5, 4, 18, 15, 0, DateTimeKind.Local),
            Link = "https://www.bloomberg.com/technology",
            Category = "Technologie",
            AffectedTickers = ["AAPL", "MSFT", "NVDA"],
            IsDemo = true
        },
        new()
        {
            Id = "wsj-demo-red-sea",
            Title = "Beispiel: Lieferkettenrisiken im Welthandel bleiben Thema für Exportwerte",
            Source = "The Wall Street Journal (Demo)",
            PublishedAt = new DateTime(2026, 5, 4, 14, 10, 0, DateTimeKind.Local),
            Link = "https://www.wsj.com/news/world",
            Category = "Geopolitik",
            AffectedTickers = ["DOU.DE", "SAP.DE", "TSLA"],
            IsDemo = true
        },
        new()
        {
            Id = "reuters-demo-etf-flows",
            Title = "Beispiel: ETF-Zuflüsse deuten auf breitere Marktstabilität im US-Aktienmarkt hin",
            Source = "Reuters (Demo)",
            PublishedAt = new DateTime(2026, 5, 4, 12, 5, 0, DateTimeKind.Local),
            Link = "https://www.reuters.com/markets/us/",
            Category = "Markt",
            AffectedTickers = ["SPY", "QQQ", "AAPL"],
            IsDemo = true
        },
        new()
        {
            Id = "handelsblatt-demo-tech-regulation",
            Title = "Beispiel: Regulierung rund um KI und Plattformmärkte bleibt Belastungsfaktor",
            Source = "Handelsblatt (Demo)",
            PublishedAt = new DateTime(2026, 5, 3, 16, 20, 0, DateTimeKind.Local),
            Link = "https://www.handelsblatt.com/technik/",
            Category = "Technologie",
            AffectedTickers = ["AAPL", "TSLA"],
            IsDemo = true
        },
        new()
        {
            Id = "ft-demo-energy-outlook",
            Title = "Beispiel: Energiepreise und Konjunktursorgen prägen die europäische Berichtssaison",
            Source = "Financial Times (Demo)",
            PublishedAt = new DateTime(2026, 5, 3, 10, 0, 0, DateTimeKind.Local),
            Link = "https://www.ft.com/europe",
            Category = "Wirtschaft",
            AffectedTickers = ["DOU.DE", "SAP.DE"],
            IsDemo = true
        },
        new()
        {
            Id = "reuters-demo-trade-tariffs",
            Title = "Beispiel: Handelskonflikte und Zölle beeinflussen Auto- und Exporttitel",
            Source = "Reuters (Demo)",
            PublishedAt = new DateTime(2026, 5, 2, 15, 35, 0, DateTimeKind.Local),
            Link = "https://www.reuters.com/world/",
            Category = "Geopolitik",
            AffectedTickers = ["TSLA", "DOU.DE"],
            IsDemo = true
        }
    ];

    public string ProviderLabel => "Seriöse Demo-Quellen";

    public bool IsDemoData => true;

    public Task<IReadOnlyList<NewsItem>> GetNewsAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(DemoItems);
    }
}
