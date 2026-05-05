namespace StockPredictor.App.Models;

public sealed class ChatAssistantAvailability
{
    public string ActiveProvider { get; init; } = "FAQ-Fallback";

    public string ConfiguredMode { get; init; } = "auto";

    public bool OllamaConfigured { get; init; }

    public bool OllamaReachable { get; init; }

    public bool OllamaModelAvailable { get; init; }

    public bool UsesFallback { get; init; }

    public string StatusLabel { get; init; } = string.Empty;

    public string StatusMessage { get; init; } = string.Empty;

    public string OllamaBaseUrl { get; init; } = string.Empty;

    public string OllamaModel { get; init; } = string.Empty;
}
