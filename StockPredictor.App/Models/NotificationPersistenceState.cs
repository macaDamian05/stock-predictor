namespace StockPredictor.App.Models;

public sealed class NotificationPersistenceState
{
    public DateTime? LastPayloadGeneratedAt { get; init; }

    public Dictionary<string, string> WatchlistDataMarkers { get; init; } = [];
}
