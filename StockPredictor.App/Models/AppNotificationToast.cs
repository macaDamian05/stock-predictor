namespace StockPredictor.App.Models;

public sealed class AppNotificationToast
{
    public string Id { get; init; } = string.Empty;

    public string Title { get; init; } = string.Empty;

    public string Message { get; init; } = string.Empty;

    public string Tone { get; init; } = "info";

    public DateTime CreatedAt { get; init; }
}
