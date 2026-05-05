using Microsoft.Extensions.Options;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class ChatAssistantRouterService(
    OllamaChatAssistantService ollamaChatAssistantService,
    MockChatAssistantService mockChatAssistantService,
    DashboardDataService dashboardDataService,
    IOptions<ChatAssistantOptions> optionsAccessor) : IChatAssistantService
{
    private static readonly IReadOnlyList<string> InvestmentAdviceKeywords =
    [
        "kaufen",
        "verkaufen",
        "investieren",
        "einsteigen",
        "aussteigen",
        "traden",
        "trade",
        "kursziel",
        "all-in",
        "portfolio",
        "chance",
        "rendite",
        "soll ich",
        "buy",
        "sell"
    ];

    private static readonly IReadOnlyList<string> ScopeKeywords =
    [
        "dashboard",
        "datenstand",
        "payload",
        "export",
        "kurs",
        "ticker",
        "watchlist",
        "asset",
        "aktie",
        "etf",
        "forecast",
        "prognose",
        "forschungs",
        "modell",
        "methode",
        "benchmark",
        "baseline",
        "rmse",
        "mae",
        "directional",
        "accuracy",
        "rsi",
        "backtest",
        "backtesting",
        "walk-forward",
        "feature",
        "lag",
        "random forest",
        "decision tree",
        "ridge",
        "lstm",
        "news",
        "bachelorarbeit",
        "methodik",
        "kennzahl"
    ];

    public IReadOnlyList<string> GetSuggestedQuestions() => mockChatAssistantService.GetSuggestedQuestions();

    public async Task<ChatAssistantAvailability> GetAvailabilityAsync(CancellationToken cancellationToken = default)
    {
        var options = optionsAccessor.Value;
        var mode = NormalizeMode(options.Mode);

        if (string.Equals(mode, "mock", StringComparison.Ordinal))
        {
            return new ChatAssistantAvailability
            {
                ActiveProvider = "FAQ-Fallback",
                ConfiguredMode = mode,
                OllamaConfigured = !string.IsNullOrWhiteSpace(options.OllamaBaseUrl),
                OllamaReachable = false,
                OllamaModelAvailable = false,
                UsesFallback = true,
                OllamaBaseUrl = options.OllamaBaseUrl,
                OllamaModel = options.OllamaModel,
                StatusLabel = "FAQ-Fallback aktiv",
                StatusMessage = "Die App ist aktuell auf den lokalen FAQ-Fallback gestellt. Ollama wird in diesem Modus nicht angefragt."
            };
        }

        var ollamaAvailability = await ollamaChatAssistantService.GetAvailabilityAsync(cancellationToken);
        if (ollamaAvailability.OllamaReachable && ollamaAvailability.OllamaModelAvailable)
        {
            return ollamaAvailability;
        }

        return new ChatAssistantAvailability
        {
            ActiveProvider = "FAQ-Fallback",
            ConfiguredMode = mode,
            OllamaConfigured = ollamaAvailability.OllamaConfigured,
            OllamaReachable = ollamaAvailability.OllamaReachable,
            OllamaModelAvailable = ollamaAvailability.OllamaModelAvailable,
            UsesFallback = true,
            OllamaBaseUrl = ollamaAvailability.OllamaBaseUrl,
            OllamaModel = ollamaAvailability.OllamaModel,
            StatusLabel = ollamaAvailability.StatusLabel,
            StatusMessage = ollamaAvailability.StatusMessage
        };
    }

    public async Task<ChatAssistantReply> AskAsync(
        IReadOnlyList<ChatAssistantMessage> conversation,
        CancellationToken cancellationToken = default)
    {
        var latestQuestion = GetLatestUserQuestion(conversation);
        if (string.IsNullOrWhiteSpace(latestQuestion))
        {
            return BuildGuardReply(
                "Ich beantworte hier nur Fragen zum Dashboard, zu Kennzahlen, Modellen, Methoden und zum lokalen Forschungsstand der Bachelorarbeit.");
        }

        if (ContainsAny(latestQuestion, InvestmentAdviceKeywords))
        {
            return BuildGuardReply(
                "Ich gebe keine Kauf-, Verkaufs- oder Investmentempfehlungen. Ich kann aber erklären, wie Dashboard, Kennzahlen, Modelle und der aktuelle Forschungsstand zu lesen sind.",
                isBlocked: true);
        }

        if (!await IsRelevantQuestionAsync(latestQuestion, cancellationToken))
        {
            return BuildGuardReply(
                "Ich beantworte hier nur Fragen zum Stock-Predictor-Dashboard, zu Kennzahlen, Modellen, Methoden und zum lokalen Exportstand der Bachelorarbeit.",
                isBlocked: true);
        }

        var mode = NormalizeMode(optionsAccessor.Value.Mode);
        if (string.Equals(mode, "mock", StringComparison.Ordinal))
        {
            return await mockChatAssistantService.AskAsync(conversation, cancellationToken);
        }

        try
        {
            var availability = await ollamaChatAssistantService.GetAvailabilityAsync(cancellationToken);
            if (availability.OllamaReachable && availability.OllamaModelAvailable)
            {
                return await ollamaChatAssistantService.AskAsync(conversation, cancellationToken);
            }

            var fallbackReply = await mockChatAssistantService.AskAsync(conversation, cancellationToken);
            return BuildFallbackReply(fallbackReply, availability.StatusMessage);
        }
        catch (Exception)
        {
            var fallbackReply = await mockChatAssistantService.AskAsync(conversation, cancellationToken);
            return BuildFallbackReply(
                fallbackReply,
                "Ollama konnte für diese Anfrage nicht sauber erreicht werden. Deshalb kommt die Antwort aus dem lokalen FAQ-Fallback.");
        }
    }

    private async Task<bool> IsRelevantQuestionAsync(string question, CancellationToken cancellationToken)
    {
        if (ContainsAny(question, ScopeKeywords))
        {
            return true;
        }

        var snapshot = await dashboardDataService.GetLatestAsync(cancellationToken);
        if (snapshot.Payload is null)
        {
            return false;
        }

        if (snapshot.Payload.FeaturedTickers.Any(ticker =>
                question.Contains(ticker.Ticker, StringComparison.OrdinalIgnoreCase)))
        {
            return true;
        }

        if (snapshot.Payload.CompanyRanking.Any(entry =>
                question.Contains(entry.Ticker, StringComparison.OrdinalIgnoreCase)))
        {
            return true;
        }

        return false;
    }

    private static ChatAssistantReply BuildGuardReply(string content, bool isBlocked = false)
    {
        return new ChatAssistantReply
        {
            Content = content,
            ProviderLabel = "Sicherheitsregel",
            UsesFallback = true,
            IsBlocked = isBlocked
        };
    }

    private static ChatAssistantReply BuildFallbackReply(ChatAssistantReply fallbackReply, string statusMessage)
    {
        return new ChatAssistantReply
        {
            Content = fallbackReply.Content,
            ProviderLabel = fallbackReply.ProviderLabel,
            UsesFallback = true,
            IsBlocked = fallbackReply.IsBlocked,
            CreatedAt = fallbackReply.CreatedAt,
            StatusMessage = statusMessage
        };
    }

    private static bool ContainsAny(string question, IReadOnlyList<string> keywords)
    {
        return keywords.Any(keyword => question.Contains(keyword, StringComparison.OrdinalIgnoreCase));
    }

    private static string GetLatestUserQuestion(IReadOnlyList<ChatAssistantMessage> conversation)
    {
        return conversation
            .LastOrDefault(message => string.Equals(message.Role, "user", StringComparison.OrdinalIgnoreCase))
            ?.Content
            ?.Trim()
            ?? string.Empty;
    }

    private static string NormalizeMode(string? rawMode)
    {
        var normalized = rawMode?.Trim().ToLowerInvariant();
        return normalized switch
        {
            "ollama" => "ollama",
            "mock" => "mock",
            _ => "auto"
        };
    }
}
