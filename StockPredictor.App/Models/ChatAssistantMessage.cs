namespace StockPredictor.App.Models;

public sealed class ChatAssistantMessage
{
    public string Id { get; init; } = Guid.NewGuid().ToString("N");

    public string Role { get; init; } = "assistant";

    public string SourceLabel { get; init; } = string.Empty;

    public string Content { get; init; } = string.Empty;

    public DateTime CreatedAt { get; init; } = DateTime.Now;

    public bool IsStatus { get; init; }
}
