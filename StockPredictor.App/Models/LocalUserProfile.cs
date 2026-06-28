namespace StockPredictor.App.Models;

public sealed class LocalUserProfile
{
    public const int CurrentSchemaVersion = 1;

    public int SchemaVersion { get; set; } = CurrentSchemaVersion;

    public string ProfileName { get; set; } = "Mein Profil";

    public DateTime CreatedAt { get; set; } = DateTime.Now;

    public DateTime UpdatedAt { get; set; } = DateTime.Now;

    public List<WatchlistItem> Watchlist { get; set; } = [];

    public DashboardPreferences Dashboard { get; set; } = new();

    public ChartPreferences Chart { get; set; } = new();

    public ForecastPreferences Forecast { get; set; } = new();

    public NewsPreferences News { get; set; } = new();

    public NotificationPreferences Notifications { get; set; } = new();
}

public sealed class UserPreferences
{
    public DashboardPreferences Dashboard { get; set; } = new();

    public ChartPreferences Chart { get; set; } = new();

    public ForecastPreferences Forecast { get; set; } = new();

    public NewsPreferences News { get; set; } = new();

    public NotificationPreferences Notifications { get; set; } = new();
}

public sealed class WatchlistItem
{
    public string Symbol { get; set; } = string.Empty;

    public string? Name { get; set; }

    public string? AssetType { get; set; }

    public DateTime AddedAt { get; set; } = DateTime.Now;

    public string? Note { get; set; }

    public string? PreferredChartRange { get; set; }

    public bool? ShowForecastByDefault { get; set; }
}

public sealed class DashboardPreferences
{
    public List<string> PreferredDashboardAssets { get; set; } =
    [
        "AAPL",
        "MSFT",
        "NVDA",
        "TSLA",
        "SPY",
        "ENR.DE",
    ];
}

public sealed class ChartPreferences
{
    public string DefaultChartRange { get; set; } = "1M";
}

public sealed class ForecastPreferences
{
    public bool ShowForecastByDefault { get; set; }
}

public sealed class NewsPreferences
{
    public List<string> PreferredNewsCategories { get; set; } = [];
}

public sealed class NotificationPreferences
{
    public bool EnableBrowserNotifications { get; set; }

    public bool NotifyWhenForecastUpdated { get; set; } = true;

    public bool NotifyWhenPayloadIsStale { get; set; } = true;

    public bool NotifyWhenWatchlistAssetUpdated { get; set; } = true;

    public bool NotifyWhenBackgroundJobCompleted { get; set; } = true;

    public bool NotifyWhenBackgroundJobFailed { get; set; } = true;
}
