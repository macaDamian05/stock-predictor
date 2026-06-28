using Microsoft.JSInterop;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class NotificationService(
    IJSRuntime jsRuntime,
    LocalUserProfileService profileService)
{
    private readonly List<AppNotificationToast> _toasts = [];
    private readonly HashSet<string> _publishedJobNotifications = new(StringComparer.OrdinalIgnoreCase);

    public event Action? ToastsChanged;

    public IReadOnlyList<AppNotificationToast> Toasts => _toasts.AsReadOnly();

    public async Task<NotificationSettingsSnapshot> GetSettingsAsync(CancellationToken cancellationToken = default)
    {
        var enabled = await jsRuntime.InvokeAsync<bool>(
            "stockPredictorNotifications.getEnabled",
            cancellationToken);

        var permissionRaw = await jsRuntime.InvokeAsync<string>(
            "stockPredictorNotifications.getPermissionStatus",
            cancellationToken);

        var environment = await jsRuntime.InvokeAsync<NotificationBrowserEnvironment>(
            "stockPredictorNotifications.getEnvironmentStatus",
            cancellationToken);

        var profile = await profileService.GetProfileAsync(false, cancellationToken);

        return new NotificationSettingsSnapshot
        {
            IsEnabled = enabled && profile.Notifications.EnableBrowserNotifications,
            Permission = MapPermission(permissionRaw),
            Environment = environment ?? new NotificationBrowserEnvironment()
        };
    }

    public async Task<NotificationSettingsSnapshot> RequestPermissionAsync(CancellationToken cancellationToken = default)
    {
        var permissionRaw = await jsRuntime.InvokeAsync<string>(
            "stockPredictorNotifications.requestPermission",
            cancellationToken);

        if (MapPermission(permissionRaw) == BrowserNotificationPermission.Granted)
        {
            await SetEnabledAsync(true, cancellationToken);
        }

        return await GetSettingsAsync(cancellationToken);
    }

    public async Task SetEnabledAsync(bool isEnabled, CancellationToken cancellationToken = default)
    {
        await jsRuntime.InvokeVoidAsync(
            "stockPredictorNotifications.setEnabled",
            cancellationToken,
            isEnabled);

        var profile = await profileService.GetProfileAsync(false, cancellationToken);
        profile.Notifications.EnableBrowserNotifications = isEnabled;
        await profileService.SaveProfileAsync(profile, cancellationToken);
    }

    public async Task SendTestNotificationAsync(CancellationToken cancellationToken = default)
    {
        AddToast(
            "Testbenachrichtigung",
            "Die Testbenachrichtigung wurde lokal ausgelöst. Falls kein separates Browser-Popup erscheint, bleibt dieser In-App-Hinweis als sichtbarer Fallback bestehen.",
            "info");

        await Task.CompletedTask;
    }

    public async Task CheckForPayloadUpdatesAsync(
        DashboardPayload payload,
        IReadOnlyList<string> watchlistTickers,
        CancellationToken cancellationToken = default)
    {
        var persistedState = await GetPersistenceStateAsync(cancellationToken);
        var currentState = BuildCurrentState(payload, watchlistTickers);

        var shouldNotifyAboutPayload = persistedState.LastPayloadGeneratedAt is not null
            && payload.GeneratedAt > persistedState.LastPayloadGeneratedAt.Value;

        if (shouldNotifyAboutPayload)
        {
            await PublishAsync(
                "Neuer Dashboard-Payload verfügbar",
                $"Ein neuer lokaler Export vom {FormatDateTime(payload.GeneratedAt)} wurde geladen.",
                "payload",
                cancellationToken);

            if (payload.FeaturedTickers.Count > 0)
            {
                await PublishAsync(
                    "Prognosedaten aktualisiert",
                    "Der zuletzt exportierte Forschungsstand mit Prognosedaten wurde aktualisiert.",
                    "forecast",
                    cancellationToken);
            }
        }

        if (HasStaleForecast(payload)
            && persistedState.LastStalePayloadGeneratedAt != payload.GeneratedAt)
        {
            await PublishAsync(
                "Forecast-Daten veraltet",
                "Mindestens ein lokaler Forecast basiert auf einem älteren Export. Eine Aktualisierung kann im Hintergrund laufen.",
                "payload-stale",
                cancellationToken);
        }

        var changedWatchlistTickers = GetChangedWatchlistTickers(persistedState, currentState);
        if (changedWatchlistTickers.Count > 0)
        {
            var label = changedWatchlistTickers.Count == 1
                ? changedWatchlistTickers[0]
                : $"{changedWatchlistTickers.Count} Watchlist-Assets";

            await PublishAsync(
                "Watchlist-Asset hat neue Daten",
                $"{label} wurde mit neuem lokalem Datenstand erkannt.",
                "watchlist",
                cancellationToken);
        }

        await SetPersistenceStateAsync(currentState, cancellationToken);
    }

    public async Task NotifyForecastJobChangedAsync(ForecastJobSnapshot job, CancellationToken cancellationToken = default)
    {
        if (job.State is not (ForecastJobState.Completed or ForecastJobState.Failed))
        {
            return;
        }

        var marker = $"{job.Ticker}|{job.State}|{job.CompletedAt:O}";
        if (!_publishedJobNotifications.Add(marker))
        {
            return;
        }

        if (job.State == ForecastJobState.Completed)
        {
            await PublishAsync(
                "Hintergrundjob abgeschlossen",
                $"Der lokale Forecast-Job für {job.Ticker} wurde abgeschlossen.",
                "job-completed",
                cancellationToken);
            return;
        }

        await PublishAsync(
            "Hintergrundjob fehlgeschlagen",
            $"Der lokale Forecast-Job für {job.Ticker} ist fehlgeschlagen. Der alte Stand bleibt nutzbar.",
            "job-failed",
            cancellationToken);
    }

    public void DismissToast(string toastId)
    {
        if (string.IsNullOrWhiteSpace(toastId))
        {
            return;
        }

        var removed = _toasts.RemoveAll(toast => string.Equals(toast.Id, toastId, StringComparison.Ordinal)) > 0;
        if (removed)
        {
            ToastsChanged?.Invoke();
        }
    }

    private async Task PublishAsync(
        string title,
        string message,
        string tag,
        CancellationToken cancellationToken,
        bool ignoreEnabled = false,
        bool suppressToastFallback = false)
    {
        var settings = await GetSettingsAsync(cancellationToken);
        var profile = await profileService.GetProfileAsync(false, cancellationToken);
        if (!ignoreEnabled && (!settings.IsEnabled || !IsNotificationTypeEnabled(profile.Notifications, tag)))
        {
            return;
        }

        var shouldUseBrowserNotification = settings.IsEnabled
            && settings.Permission == BrowserNotificationPermission.Granted;

        if (shouldUseBrowserNotification || (ignoreEnabled && settings.Permission == BrowserNotificationPermission.Granted))
        {
            var delivered = await jsRuntime.InvokeAsync<bool>(
                "stockPredictorNotifications.show",
                cancellationToken,
                title,
                new
                {
                    body = message,
                    tag,
                    requireInteraction = string.Equals(tag, "test", StringComparison.OrdinalIgnoreCase)
                });

            if (delivered)
            {
                return;
            }
        }

        if (!suppressToastFallback)
        {
            AddToast(title, message, settings.Permission == BrowserNotificationPermission.Blocked ? "warning" : "info");
        }
    }

    private void AddToast(string title, string message, string tone)
    {
        var toast = new AppNotificationToast
        {
            Id = Guid.NewGuid().ToString("N"),
            Title = title,
            Message = message,
            Tone = tone,
            CreatedAt = DateTime.Now
        };

        _toasts.Add(toast);
        ToastsChanged?.Invoke();
        _ = RemoveToastLaterAsync(toast.Id);
    }

    private async Task RemoveToastLaterAsync(string toastId)
    {
        await Task.Delay(TimeSpan.FromSeconds(6));
        DismissToast(toastId);
    }

    private async Task<NotificationPersistenceState> GetPersistenceStateAsync(CancellationToken cancellationToken)
    {
        var state = await jsRuntime.InvokeAsync<NotificationPersistenceState>(
            "stockPredictorNotifications.getState",
            cancellationToken);

        return state ?? new NotificationPersistenceState();
    }

    private async Task SetPersistenceStateAsync(NotificationPersistenceState state, CancellationToken cancellationToken)
    {
        await jsRuntime.InvokeVoidAsync(
            "stockPredictorNotifications.setState",
            cancellationToken,
            state);
    }

    private static NotificationPersistenceState BuildCurrentState(
        DashboardPayload payload,
        IReadOnlyList<string> watchlistTickers)
    {
        var watchlistMarkers = payload.FeaturedTickers
            .Where(ticker => watchlistTickers.Any(watchlistTicker =>
                string.Equals(watchlistTicker, ticker.Ticker, StringComparison.OrdinalIgnoreCase)))
            .ToDictionary(
                ticker => ticker.Ticker,
                ticker => BuildTickerMarker(ticker),
                StringComparer.OrdinalIgnoreCase);

        return new NotificationPersistenceState
        {
            LastPayloadGeneratedAt = payload.GeneratedAt,
            LastStalePayloadGeneratedAt = HasStaleForecast(payload) ? payload.GeneratedAt : null,
            WatchlistDataMarkers = watchlistMarkers
        };
    }

    private static List<string> GetChangedWatchlistTickers(
        NotificationPersistenceState previousState,
        NotificationPersistenceState currentState)
    {
        var changed = new List<string>();

        foreach (var (ticker, currentMarker) in currentState.WatchlistDataMarkers)
        {
            if (!previousState.WatchlistDataMarkers.TryGetValue(ticker, out var previousMarker))
            {
                continue;
            }

            if (!string.Equals(previousMarker, currentMarker, StringComparison.Ordinal))
            {
                changed.Add(ticker);
            }
        }

        return changed;
    }

    private static string BuildTickerMarker(FeaturedTicker ticker)
    {
        var dataUntil = ticker.DataUntil?.ToString("yyyy-MM-dd") ?? ticker.LastCloseDate.ToString("yyyy-MM-dd");
        var forecastGeneratedAt = ticker.ForecastGeneratedAt?.ToString("O") ?? string.Empty;
        return $"{dataUntil}|{forecastGeneratedAt}";
    }

    private static bool HasStaleForecast(DashboardPayload payload)
    {
        var staleAfterDays = payload.StaleAfterDays > 0 ? payload.StaleAfterDays : 3;
        var today = DateOnly.FromDateTime(DateTime.Now);

        return payload.FeaturedTickers.Any(ticker =>
        {
            var dataUntil = ticker.DataUntil ?? payload.DataUntil ?? ticker.LastCloseDate;
            var dataAgeDays = today.DayNumber - dataUntil.DayNumber;
            var forecastGeneratedAt = ticker.ForecastGeneratedAt ?? payload.GeneratedAt;
            var forecastAgeDays = Math.Max(0, (DateTime.Now.Date - forecastGeneratedAt.Date).Days);
            return dataAgeDays > staleAfterDays || forecastAgeDays > staleAfterDays;
        });
    }

    private static bool IsNotificationTypeEnabled(NotificationPreferences preferences, string tag)
    {
        return tag switch
        {
            "payload" => preferences.NotifyWhenForecastUpdated,
            "forecast" => preferences.NotifyWhenForecastUpdated,
            "payload-stale" => preferences.NotifyWhenPayloadIsStale,
            "watchlist" => preferences.NotifyWhenWatchlistAssetUpdated,
            "job-completed" => preferences.NotifyWhenBackgroundJobCompleted,
            "job-failed" => preferences.NotifyWhenBackgroundJobFailed,
            _ => true,
        };
    }

    private static BrowserNotificationPermission MapPermission(string? permissionRaw)
    {
        return permissionRaw?.Trim().ToLowerInvariant() switch
        {
            "granted" => BrowserNotificationPermission.Granted,
            "denied" => BrowserNotificationPermission.Blocked,
            "default" => BrowserNotificationPermission.NotAsked,
            _ => BrowserNotificationPermission.Unsupported
        };
    }

    private static string FormatDateTime(DateTime value)
    {
        return value.ToString("dd. MMM yyyy | HH:mm", System.Globalization.CultureInfo.GetCultureInfo("de-DE"));
    }
}
