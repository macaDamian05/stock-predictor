namespace StockPredictor.App.Models;

public sealed class ChatAssistantReply
{
    public string Content { get; init; } = string.Empty;

    public string ProviderLabel { get; init; } = string.Empty;

    public bool UsesFallback { get; init; }

    public bool IsBlocked { get; init; }

    public string? StatusMessage { get; init; }

    public DateTime CreatedAt { get; init; } = DateTime.Now;
}
