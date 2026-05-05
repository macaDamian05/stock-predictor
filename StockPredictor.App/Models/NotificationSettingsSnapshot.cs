namespace StockPredictor.App.Models;

public sealed class NotificationSettingsSnapshot
{
    public bool IsEnabled { get; init; }

    public BrowserNotificationPermission Permission { get; init; }

    public NotificationBrowserEnvironment Environment { get; init; } = new();

    public bool IsSupported => Environment.NotificationApiSupported;

    public bool CanUseBrowserPopup =>
        Permission == BrowserNotificationPermission.Granted
        && Environment.NotificationApiSupported
        && Environment.IsSecureContext;

    public bool UsesServiceWorkerDelivery =>
        Environment.ServiceWorkerSupported && Environment.HasServiceWorkerRegistration;
}
