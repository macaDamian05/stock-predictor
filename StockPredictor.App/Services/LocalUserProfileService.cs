using System.Text.Json;
using Microsoft.JSInterop;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class LocalUserProfileService(IJSRuntime jsRuntime)
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true,
    };

    private static readonly HashSet<string> AllowedChartRanges =
    [
        "1T",
        "1W",
        "1M",
        "6M",
        "1J",
        "MAX",
    ];

    private static readonly string[] DefaultDashboardAssets =
    [
        "AAPL",
        "MSFT",
        "NVDA",
        "TSLA",
        "SPY",
        "ENR.DE",
    ];

    private LocalUserProfile? _cachedProfile;

    public event Action? ProfileChanged;

    public async Task<LocalUserProfileResult> LoadAsync(bool forceReload = false, CancellationToken cancellationToken = default)
    {
        if (!forceReload && _cachedProfile is not null)
        {
            return new LocalUserProfileResult(_cachedProfile, false, false, null);
        }

        try
        {
            var raw = await jsRuntime.InvokeAsync<string?>(
                "stockPredictorProfile.getRaw",
                cancellationToken);

            if (string.IsNullOrWhiteSpace(raw))
            {
                var fallback = await CreateFallbackProfileAsync(cancellationToken);
                _cachedProfile = fallback.Profile;
                await SaveProfileAsync(_cachedProfile, cancellationToken);
                return fallback;
            }

            var parsed = JsonSerializer.Deserialize<LocalUserProfile>(raw, JsonOptions);
            if (parsed is null)
            {
                var fallback = await CreateFallbackProfileAsync(cancellationToken);
                _cachedProfile = fallback.Profile;
                await SaveProfileAsync(_cachedProfile, cancellationToken);
                return fallback with { UsedFallback = true, Message = "Das lokale Profil war leer und wurde neu erzeugt." };
            }

            _cachedProfile = NormalizeProfile(parsed);
            if (_cachedProfile.UpdatedAt != parsed.UpdatedAt || _cachedProfile.SchemaVersion != parsed.SchemaVersion)
            {
                await SaveProfileAsync(_cachedProfile, cancellationToken);
            }

            return new LocalUserProfileResult(_cachedProfile, false, false, null);
        }
        catch (JsonException)
        {
            var fallback = await CreateFallbackProfileAsync(cancellationToken);
            _cachedProfile = fallback.Profile;
            await SaveProfileAsync(_cachedProfile, cancellationToken);
            return fallback with { UsedFallback = true, Message = "Das gespeicherte Profil war kein gültiges JSON. Es wurde ein lokales Fallback-Profil erzeugt." };
        }
        catch (InvalidOperationException)
        {
            var fallback = CreateFallbackProfile([]);
            _cachedProfile = fallback;
            return new LocalUserProfileResult(fallback, true, false, "LocalStorage ist aktuell nicht erreichbar. Die App nutzt temporäre Standardwerte.");
        }
        catch (JSDisconnectedException)
        {
            var fallback = CreateFallbackProfile([]);
            _cachedProfile = fallback;
            return new LocalUserProfileResult(fallback, true, false, "Die Browser-Verbindung wurde getrennt. Die App nutzt temporäre Standardwerte.");
        }
    }

    public async Task<LocalUserProfile> GetProfileAsync(bool forceReload = false, CancellationToken cancellationToken = default)
    {
        return (await LoadAsync(forceReload, cancellationToken)).Profile;
    }

    public async Task SaveProfileAsync(LocalUserProfile profile, CancellationToken cancellationToken = default)
    {
        var normalized = NormalizeProfile(profile);
        normalized.UpdatedAt = DateTime.Now;
        var raw = JsonSerializer.Serialize(normalized, JsonOptions);

        var saved = await jsRuntime.InvokeAsync<bool>(
            "stockPredictorProfile.setRaw",
            cancellationToken,
            raw);

        if (!saved)
        {
            throw new InvalidOperationException("Das lokale Profil konnte nicht im Browser gespeichert werden.");
        }

        _cachedProfile = normalized;
        ProfileChanged?.Invoke();
    }

    public async Task<LocalUserProfile> ResetAsync(CancellationToken cancellationToken = default)
    {
        var fallback = CreateFallbackProfile([]);
        await SaveProfileAsync(fallback, cancellationToken);
        return fallback;
    }

    public async Task<string> ExportJsonAsync(CancellationToken cancellationToken = default)
    {
        var profile = await GetProfileAsync(false, cancellationToken);
        return JsonSerializer.Serialize(NormalizeProfile(profile), JsonOptions);
    }

    public async Task<LocalUserProfileImportResult> ImportJsonAsync(string? json, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return new LocalUserProfileImportResult(false, null, "Bitte JSON einfügen, bevor das Profil importiert wird.");
        }

        try
        {
            var imported = JsonSerializer.Deserialize<LocalUserProfile>(json, JsonOptions);
            if (imported is null)
            {
                return new LocalUserProfileImportResult(false, null, "Das importierte Profil war leer.");
            }

            var normalized = NormalizeProfile(imported);
            await SaveProfileAsync(normalized, cancellationToken);
            return new LocalUserProfileImportResult(true, normalized, "Profil wurde importiert und lokal gespeichert.");
        }
        catch (JsonException)
        {
            return new LocalUserProfileImportResult(false, null, "Das importierte Profil ist kein gültiges JSON.");
        }
        catch (InvalidOperationException exception)
        {
            return new LocalUserProfileImportResult(false, null, exception.Message);
        }
    }

    public async Task<IReadOnlyList<WatchlistItem>> GetWatchlistAsync(CancellationToken cancellationToken = default)
    {
        var profile = await GetProfileAsync(false, cancellationToken);
        return profile.Watchlist.ToArray();
    }

    public async Task SaveWatchlistAsync(IEnumerable<WatchlistItem> items, CancellationToken cancellationToken = default)
    {
        var profile = await GetProfileAsync(false, cancellationToken);
        profile.Watchlist = NormalizeWatchlist(items);
        await SaveProfileAsync(profile, cancellationToken);
    }

    public async Task AddOrUpdateWatchlistItemAsync(WatchlistItem item, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(item.Symbol))
        {
            return;
        }

        var profile = await GetProfileAsync(false, cancellationToken);
        var normalizedSymbol = NormalizeTicker(item.Symbol);
        var existing = profile.Watchlist.FirstOrDefault(entry =>
            string.Equals(entry.Symbol, normalizedSymbol, StringComparison.OrdinalIgnoreCase));

        if (existing is null)
        {
            item.Symbol = normalizedSymbol;
            item.AddedAt = item.AddedAt == default ? DateTime.Now : item.AddedAt;
            profile.Watchlist.Add(item);
        }
        else
        {
            existing.Name = item.Name ?? existing.Name;
            existing.AssetType = item.AssetType ?? existing.AssetType;
            existing.Note = item.Note ?? existing.Note;
            existing.PreferredChartRange = NormalizeChartRange(item.PreferredChartRange ?? existing.PreferredChartRange);
            existing.ShowForecastByDefault = item.ShowForecastByDefault ?? existing.ShowForecastByDefault;
        }

        await SaveProfileAsync(profile, cancellationToken);
    }

    public async Task RemoveWatchlistItemAsync(string symbol, CancellationToken cancellationToken = default)
    {
        var normalizedSymbol = NormalizeTicker(symbol);
        var profile = await GetProfileAsync(false, cancellationToken);
        profile.Watchlist = profile.Watchlist
            .Where(item => !string.Equals(item.Symbol, normalizedSymbol, StringComparison.OrdinalIgnoreCase))
            .ToList();
        profile.Dashboard.PreferredDashboardAssets = profile.Dashboard.PreferredDashboardAssets
            .Where(item => !string.Equals(item, normalizedSymbol, StringComparison.OrdinalIgnoreCase))
            .ToList();
        await SaveProfileAsync(profile, cancellationToken);
    }

    public async Task<bool> CopyToClipboardAsync(string text, CancellationToken cancellationToken = default)
    {
        try
        {
            return await jsRuntime.InvokeAsync<bool>(
                "stockPredictorProfile.copyText",
                cancellationToken,
                text);
        }
        catch (InvalidOperationException)
        {
            return false;
        }
        catch (JSDisconnectedException)
        {
            return false;
        }
    }

    public static string NormalizeChartRange(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return "1M";
        }

        var normalized = value.Trim().ToUpperInvariant();
        return AllowedChartRanges.Contains(normalized) ? normalized : "1M";
    }

    public static MarketTimeRange ToMarketTimeRange(string? value)
    {
        return NormalizeChartRange(value) switch
        {
            "1T" => MarketTimeRange.OneDay,
            "1W" => MarketTimeRange.OneWeek,
            "6M" => MarketTimeRange.SixMonths,
            "1J" => MarketTimeRange.OneYear,
            "MAX" => MarketTimeRange.Max,
            _ => MarketTimeRange.OneMonth,
        };
    }

    public static string ToChartRangeLabel(MarketTimeRange range)
    {
        return range switch
        {
            MarketTimeRange.OneDay => "1T",
            MarketTimeRange.OneWeek => "1W",
            MarketTimeRange.OneMonth => "1M",
            MarketTimeRange.SixMonths => "6M",
            MarketTimeRange.OneYear => "1J",
            MarketTimeRange.Max => "MAX",
            _ => "1M",
        };
    }

    private async Task<LocalUserProfileResult> CreateFallbackProfileAsync(CancellationToken cancellationToken)
    {
        var legacyWatchlist = await TryLoadLegacyWatchlistAsync(cancellationToken);
        var fallback = CreateFallbackProfile(legacyWatchlist);
        return new LocalUserProfileResult(
            fallback,
            true,
            legacyWatchlist.Count > 0,
            legacyWatchlist.Count > 0
                ? "Alte Watchlist wurde in das neue lokale Profil übernommen."
                : "Es wurde ein lokales Standardprofil erzeugt.");
    }

    private static LocalUserProfile CreateFallbackProfile(IReadOnlyList<string> legacyWatchlist)
    {
        var now = DateTime.Now;
        var profile = new LocalUserProfile
        {
            SchemaVersion = LocalUserProfile.CurrentSchemaVersion,
            ProfileName = "Mein Profil",
            CreatedAt = now,
            UpdatedAt = now,
            Watchlist = legacyWatchlist
                .Select(ticker => new WatchlistItem
                {
                    Symbol = NormalizeTicker(ticker),
                    AddedAt = now,
                })
                .ToList(),
            Dashboard = new DashboardPreferences
            {
                PreferredDashboardAssets = legacyWatchlist.Count > 0
                    ? legacyWatchlist.Select(NormalizeTicker).Take(6).ToList()
                    : DefaultDashboardAssets.ToList(),
            },
        };

        return NormalizeProfile(profile);
    }

    private async Task<IReadOnlyList<string>> TryLoadLegacyWatchlistAsync(CancellationToken cancellationToken)
    {
        try
        {
            var tickers = await jsRuntime.InvokeAsync<string[]>(
                "stockPredictorWatchlist.get",
                cancellationToken);

            return (tickers ?? [])
                .Select(NormalizeTicker)
                .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToArray();
        }
        catch
        {
            return [];
        }
    }

    private static LocalUserProfile NormalizeProfile(LocalUserProfile profile)
    {
        var now = DateTime.Now;
        profile.SchemaVersion = LocalUserProfile.CurrentSchemaVersion;
        profile.ProfileName = string.IsNullOrWhiteSpace(profile.ProfileName)
            ? "Mein Profil"
            : profile.ProfileName.Trim();
        profile.CreatedAt = profile.CreatedAt == default ? now : profile.CreatedAt;
        profile.UpdatedAt = profile.UpdatedAt == default ? now : profile.UpdatedAt;
        profile.Watchlist = NormalizeWatchlist(profile.Watchlist);
        profile.Dashboard ??= new DashboardPreferences();
        profile.Chart ??= new ChartPreferences();
        profile.Forecast ??= new ForecastPreferences();
        profile.News ??= new NewsPreferences();
        profile.Notifications ??= new NotificationPreferences();
        profile.Chart.DefaultChartRange = NormalizeChartRange(profile.Chart.DefaultChartRange);
        profile.Dashboard.PreferredDashboardAssets = NormalizeTickerList(profile.Dashboard.PreferredDashboardAssets);
        if (profile.Dashboard.PreferredDashboardAssets.Count == 0)
        {
            profile.Dashboard.PreferredDashboardAssets = profile.Watchlist.Count > 0
                ? profile.Watchlist.Select(item => item.Symbol).Take(6).ToList()
                : DefaultDashboardAssets.ToList();
        }

        profile.News.PreferredNewsCategories = (profile.News.PreferredNewsCategories ?? [])
            .Where(category => !string.IsNullOrWhiteSpace(category))
            .Select(category => category.Trim())
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        return profile;
    }

    private static List<WatchlistItem> NormalizeWatchlist(IEnumerable<WatchlistItem>? items)
    {
        return (items ?? [])
            .Where(item => !string.IsNullOrWhiteSpace(item.Symbol))
            .Select(item =>
            {
                item.Symbol = NormalizeTicker(item.Symbol);
                item.Name = string.IsNullOrWhiteSpace(item.Name) ? null : item.Name.Trim();
                item.AssetType = string.IsNullOrWhiteSpace(item.AssetType) ? null : item.AssetType.Trim();
                item.Note = string.IsNullOrWhiteSpace(item.Note) ? null : item.Note.Trim();
                item.AddedAt = item.AddedAt == default ? DateTime.Now : item.AddedAt;
                item.PreferredChartRange = string.IsNullOrWhiteSpace(item.PreferredChartRange)
                    ? null
                    : NormalizeChartRange(item.PreferredChartRange);
                return item;
            })
            .GroupBy(item => item.Symbol, StringComparer.OrdinalIgnoreCase)
            .Select(group => group.OrderBy(item => item.AddedAt).First())
            .OrderBy(item => item.AddedAt)
            .ToList();
    }

    private static List<string> NormalizeTickerList(IEnumerable<string>? tickers)
    {
        return (tickers ?? [])
            .Select(NormalizeTicker)
            .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    private static string NormalizeTicker(string? ticker)
    {
        return (ticker ?? string.Empty).Trim().ToUpperInvariant();
    }
}
