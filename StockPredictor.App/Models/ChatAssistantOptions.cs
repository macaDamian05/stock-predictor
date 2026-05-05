namespace StockPredictor.App.Models;

public sealed class ChatAssistantOptions
{
    public const string SectionName = "ChatAssistant";

    public string Mode { get; set; } = "auto";

    public string OllamaBaseUrl { get; set; } = "http://127.0.0.1:11434/";

    public string OllamaModel { get; set; } = "llama3.2";

    public int RequestTimeoutSeconds { get; set; } = 20;

    public int MaxHistoryMessages { get; set; } = 8;
}
