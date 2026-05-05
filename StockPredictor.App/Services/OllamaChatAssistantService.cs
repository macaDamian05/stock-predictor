using System.Globalization;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Options;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class OllamaChatAssistantService(
    HttpClient httpClient,
    IOptions<ChatAssistantOptions> optionsAccessor,
    DashboardDataService dashboardDataService,
    ExplanationService explanationService)
{
    private static readonly CultureInfo UiCulture = CultureInfo.GetCultureInfo("de-DE");

    public async Task<ChatAssistantAvailability> GetAvailabilityAsync(CancellationToken cancellationToken = default)
    {
        var options = NormalizeOptions(optionsAccessor.Value);
        if (!TryBuildBaseUri(options.OllamaBaseUrl, out var baseUri))
        {
            return new ChatAssistantAvailability
            {
                ActiveProvider = "FAQ-Fallback",
                ConfiguredMode = options.Mode,
                OllamaConfigured = false,
                OllamaReachable = false,
                OllamaModelAvailable = false,
                UsesFallback = true,
                OllamaBaseUrl = options.OllamaBaseUrl,
                OllamaModel = options.OllamaModel,
                StatusLabel = "Ollama-URL ungültig",
                StatusMessage = "Die konfigurierte Ollama-URL ist ungültig. Bis zur Korrektur bleibt der lokale FAQ-Fallback aktiv."
            };
        }

        using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        linkedCts.CancelAfter(TimeSpan.FromSeconds(Math.Clamp(options.RequestTimeoutSeconds, 5, 60)));

        try
        {
            var response = await httpClient.GetAsync(BuildEndpointUri(baseUri, "api/tags"), linkedCts.Token);
            if (!response.IsSuccessStatusCode)
            {
                return new ChatAssistantAvailability
                {
                    ActiveProvider = "FAQ-Fallback",
                    ConfiguredMode = options.Mode,
                    OllamaConfigured = true,
                    OllamaReachable = false,
                    OllamaModelAvailable = false,
                    UsesFallback = true,
                    OllamaBaseUrl = baseUri.ToString(),
                    OllamaModel = options.OllamaModel,
                    StatusLabel = "Ollama antwortet nicht sauber",
                    StatusMessage = $"Die lokale Ollama-Instanz unter {baseUri} antwortete mit HTTP {(int)response.StatusCode}. Die App nutzt deshalb vorerst den FAQ-Fallback."
                };
            }

            var tags = await response.Content.ReadFromJsonAsync<OllamaTagsResponse>(cancellationToken: linkedCts.Token)
                ?? new OllamaTagsResponse();

            var modelAvailable = tags.Models.Any(model =>
                string.Equals(model.Name, options.OllamaModel, StringComparison.OrdinalIgnoreCase)
                || string.Equals(model.Model, options.OllamaModel, StringComparison.OrdinalIgnoreCase));

            return new ChatAssistantAvailability
            {
                ActiveProvider = modelAvailable ? "Ollama" : "FAQ-Fallback",
                ConfiguredMode = options.Mode,
                OllamaConfigured = true,
                OllamaReachable = true,
                OllamaModelAvailable = modelAvailable,
                UsesFallback = !modelAvailable,
                OllamaBaseUrl = baseUri.ToString(),
                OllamaModel = options.OllamaModel,
                StatusLabel = modelAvailable ? "Ollama verbunden" : "Ollama läuft, Modell fehlt",
                StatusMessage = modelAvailable
                    ? $"Das lokale Modell {options.OllamaModel} ist unter {baseUri} erreichbar."
                    : $"Ollama läuft unter {baseUri}, aber das konfigurierte Modell {options.OllamaModel} ist dort noch nicht verfügbar. Die App nutzt deshalb den FAQ-Fallback."
            };
        }
        catch (Exception exception) when (exception is HttpRequestException or TaskCanceledException or OperationCanceledException)
        {
            return new ChatAssistantAvailability
            {
                ActiveProvider = "FAQ-Fallback",
                ConfiguredMode = options.Mode,
                OllamaConfigured = true,
                OllamaReachable = false,
                OllamaModelAvailable = false,
                UsesFallback = true,
                OllamaBaseUrl = baseUri.ToString(),
                OllamaModel = options.OllamaModel,
                StatusLabel = "Ollama nicht erreichbar",
                StatusMessage = $"Unter {baseUri} konnte kein lokaler Ollama-Dienst erreicht werden. Die App bleibt nutzbar und nutzt stattdessen den FAQ-Fallback."
            };
        }
    }

    public async Task<ChatAssistantReply> AskAsync(
        IReadOnlyList<ChatAssistantMessage> conversation,
        CancellationToken cancellationToken = default)
    {
        var options = NormalizeOptions(optionsAccessor.Value);
        if (!TryBuildBaseUri(options.OllamaBaseUrl, out var baseUri))
        {
            throw new InvalidOperationException("Die konfigurierte Ollama-URL ist ungültig.");
        }

        var snapshot = await dashboardDataService.GetLatestAsync(cancellationToken);
        var systemPrompt = BuildSystemPrompt(snapshot);
        var messages = BuildMessages(conversation, systemPrompt, options.MaxHistoryMessages);

        using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        linkedCts.CancelAfter(TimeSpan.FromSeconds(Math.Clamp(options.RequestTimeoutSeconds, 5, 60)));

        var response = await httpClient.PostAsJsonAsync(
            BuildEndpointUri(baseUri, "api/chat"),
            new OllamaChatRequest
            {
                Model = options.OllamaModel,
                Stream = false,
                Messages = messages
            },
            linkedCts.Token);

        response.EnsureSuccessStatusCode();

        var payload = await response.Content.ReadFromJsonAsync<OllamaChatResponse>(cancellationToken: linkedCts.Token);
        var content = payload?.Message?.Content?.Trim();

        if (string.IsNullOrWhiteSpace(content))
        {
            throw new InvalidOperationException("Ollama hat keine Chat-Antwort zurückgegeben.");
        }

        return new ChatAssistantReply
        {
            Content = content,
            ProviderLabel = $"Ollama · {options.OllamaModel}",
            UsesFallback = false,
            CreatedAt = payload?.CreatedAt?.LocalDateTime ?? DateTime.Now
        };
    }

    private IReadOnlyList<OllamaChatMessage> BuildMessages(
        IReadOnlyList<ChatAssistantMessage> conversation,
        string systemPrompt,
        int maxHistoryMessages)
    {
        var messages = new List<OllamaChatMessage>
        {
            new()
            {
                Role = "system",
                Content = systemPrompt
            }
        };

        foreach (var message in conversation
                     .Where(item => !item.IsStatus)
                     .Where(item =>
                         string.Equals(item.Role, "user", StringComparison.OrdinalIgnoreCase)
                         || string.Equals(item.Role, "assistant", StringComparison.OrdinalIgnoreCase))
                     .TakeLast(Math.Clamp(maxHistoryMessages, 2, 16)))
        {
            messages.Add(new OllamaChatMessage
            {
                Role = string.Equals(message.Role, "user", StringComparison.OrdinalIgnoreCase) ? "user" : "assistant",
                Content = message.Content
            });
        }

        return messages;
    }

    private string BuildSystemPrompt(DashboardDataSnapshot snapshot)
    {
        var builder = new StringBuilder();
        builder.AppendLine("Du bist ein lokaler FAQ- und Erklärassistent für die Blazor-App Stock Predictor im Rahmen einer Bachelorarbeit.");
        builder.AppendLine("Antworte immer auf Deutsch, kurz, sachlich und verständlich.");
        builder.AppendLine("Erlaubte Themen: Dashboard-Inhalte, Datenstand, Prognosehorizont, Kennzahlen, ML-Modelle, Backtesting, Walk-Forward-Validation, Feature-Profile, Watchlist, News-Kontext und Bachelorarbeitskontext.");
        builder.AppendLine("Nicht erlaubt: Anlageberatung, Kauf- oder Verkaufsempfehlungen, Kursziele, Portfolio-Umschichtungen oder Trading-Signale.");
        builder.AppendLine("Wenn eine Frage nicht zum Themenraum gehört oder auf Investmententscheidungen abzielt, lehne freundlich ab und verweise auf den Forschungscharakter.");
        builder.AppendLine("Wenn Informationen nicht im lokalen Export oder im FAQ-Kontext stehen, sage das klar statt etwas zu erfinden.");
        builder.AppendLine();
        builder.AppendLine("FAQ- und Glossarkontext:");

        foreach (var faqItem in explanationService.GetFaqItems())
        {
            builder.AppendLine($"- FAQ: {faqItem.Question} Antwort: {faqItem.Answer}");
        }

        foreach (var term in explanationService.GetAllTerms())
        {
            builder.AppendLine($"- Begriff {term.Title}: {term.ShortText} {term.LongText}");
        }

        builder.AppendLine();
        builder.AppendLine("Lokaler Dashboard-Kontext:");

        if (snapshot.Payload is null)
        {
            builder.AppendLine($"- Es liegt aktuell kein lesbarer Dashboard-Payload unter {snapshot.ResolvedPath} vor.");
            builder.AppendLine("- Ohne neuen ML-Export gibt es keine aktualisierten Prognosedaten in der UI.");
            return builder.ToString();
        }

        var payload = snapshot.Payload;
        builder.AppendLine($"- Export erzeugt am: {FormatDateTime(payload.GeneratedAt)}");
        builder.AppendLine($"- Datenstand: {(payload.DataUntil is null ? "nicht angegeben" : FormatDate(payload.DataUntil.Value))}");
        builder.AppendLine($"- Stale-Grenze in der UI: {payload.StaleAfterDays} Tage");
        builder.AppendLine($"- Beobachtete Ticker in der Startansicht: {payload.FeaturedTickers.Count}");

        foreach (var ticker in payload.FeaturedTickers.Take(8))
        {
            var selectedModel = !string.IsNullOrWhiteSpace(ticker.SelectedModel.ModelLabel)
                ? ticker.SelectedModel.ModelLabel
                : (!string.IsNullOrWhiteSpace(ticker.ForecastModelLabel) ? ticker.ForecastModelLabel : "nicht angegeben");

            var availableModels = ticker.AvailableModels.Count > 0
                ? string.Join(", ", ticker.AvailableModels.Select(model => model.ModelLabel))
                : "keine Modellliste";

            builder.AppendLine(
                $"- {ticker.Ticker}: letzter Schlusskurs {FormatPrice(ticker.LastClose)} am {FormatDate(ticker.LastCloseDate)}, Datenstand {(ticker.DataUntil is null ? "nicht angegeben" : FormatDate(ticker.DataUntil.Value))}, Prognose erzeugt am {FormatDateTime(ticker.ForecastGeneratedAt ?? payload.GeneratedAt)}, Prognosehorizont {ticker.ForecastHorizonDays} Tage, Horizontänderung {FormatPercent(ticker.ForecastHorizonChangePct)}, ausgewähltes Modell {selectedModel}, verfügbare Modelle {availableModels}, Walk-Forward-RMSE {ticker.WalkForwardBestRmse.ToString("0.000", UiCulture)}, Baseline-RMSE {ticker.WalkForwardBaselineRmse.ToString("0.000", UiCulture)}, Directional Accuracy {(ticker.WalkForwardBestDirectionalAccuracy * 100).ToString("0.00", UiCulture)}%");
        }

        if (payload.MultiAssetSummaries.Count > 0)
        {
            builder.AppendLine("Multi-Asset-Summaries:");
            foreach (var summary in payload.MultiAssetSummaries.Take(4))
            {
                builder.AppendLine(
                    $"- {summary.BasketLabel}: gemeinsames Modell {summary.SharedModelLabel}, RMSE {summary.SharedModelRmse.ToString("0.000", UiCulture)}, Baseline {summary.BaselineRmse.ToString("0.000", UiCulture)}, Gap {summary.SharedModelMinusBaselineRmse.ToString("0.000", UiCulture)}, Directional Accuracy {(summary.SharedModelDirectionalAccuracy * 100).ToString("0.00", UiCulture)}%");
            }
        }

        builder.AppendLine("- Die UI zeigt den zuletzt exportierten lokalen Forschungsstand und garantiert keine Live-Prognose.");
        builder.AppendLine("- News dienen aktuell nur als Kontext und fließen noch nicht in die Modellprognose ein.");
        return builder.ToString();
    }

    private static ChatAssistantOptions NormalizeOptions(ChatAssistantOptions rawOptions)
    {
        return new ChatAssistantOptions
        {
            Mode = string.IsNullOrWhiteSpace(rawOptions.Mode) ? "auto" : rawOptions.Mode.Trim().ToLowerInvariant(),
            OllamaBaseUrl = string.IsNullOrWhiteSpace(rawOptions.OllamaBaseUrl)
                ? "http://127.0.0.1:11434/"
                : rawOptions.OllamaBaseUrl.Trim(),
            OllamaModel = string.IsNullOrWhiteSpace(rawOptions.OllamaModel)
                ? "llama3.2"
                : rawOptions.OllamaModel.Trim(),
            RequestTimeoutSeconds = rawOptions.RequestTimeoutSeconds <= 0 ? 20 : rawOptions.RequestTimeoutSeconds,
            MaxHistoryMessages = rawOptions.MaxHistoryMessages <= 0 ? 8 : rawOptions.MaxHistoryMessages
        };
    }

    private static bool TryBuildBaseUri(string rawBaseUrl, out Uri baseUri)
    {
        return Uri.TryCreate(rawBaseUrl, UriKind.Absolute, out baseUri!);
    }

    private static Uri BuildEndpointUri(Uri baseUri, string relativePath)
    {
        return new(baseUri, relativePath);
    }

    private static string FormatDate(DateOnly value) => value.ToString("dd. MMM yyyy", UiCulture);

    private static string FormatDateTime(DateTime value) => value.ToString("dd. MMM yyyy | HH:mm", UiCulture);

    private static string FormatPrice(double value) => value.ToString("N2", UiCulture);

    private static string FormatPercent(double value) => $"{(value >= 0 ? "+" : string.Empty)}{value.ToString("0.00", UiCulture)}%";

    private sealed class OllamaChatRequest
    {
        [JsonPropertyName("model")]
        public string Model { get; init; } = string.Empty;

        [JsonPropertyName("stream")]
        public bool Stream { get; init; }

        [JsonPropertyName("messages")]
        public IReadOnlyList<OllamaChatMessage> Messages { get; init; } = [];
    }

    private sealed class OllamaChatMessage
    {
        [JsonPropertyName("role")]
        public string Role { get; init; } = string.Empty;

        [JsonPropertyName("content")]
        public string Content { get; init; } = string.Empty;
    }

    private sealed class OllamaChatResponse
    {
        [JsonPropertyName("created_at")]
        public DateTimeOffset? CreatedAt { get; init; }

        [JsonPropertyName("message")]
        public OllamaChatMessage? Message { get; init; }
    }

    private sealed class OllamaTagsResponse
    {
        [JsonPropertyName("models")]
        public List<OllamaModelInfo> Models { get; init; } = [];
    }

    private sealed class OllamaModelInfo
    {
        [JsonPropertyName("name")]
        public string Name { get; init; } = string.Empty;

        [JsonPropertyName("model")]
        public string Model { get; init; } = string.Empty;
    }
}
