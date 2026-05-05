using System.Text.Json.Serialization;

namespace StockPredictor.App.Models;

public sealed class NotificationBrowserEnvironment
{
    [JsonPropertyName("notificationApiSupported")]
    public bool NotificationApiSupported { get; init; }

    [JsonPropertyName("serviceWorkerSupported")]
    public bool ServiceWorkerSupported { get; init; }

    [JsonPropertyName("hasServiceWorkerRegistration")]
    public bool HasServiceWorkerRegistration { get; init; }

    [JsonPropertyName("isSecureContext")]
    public bool IsSecureContext { get; init; }
}
