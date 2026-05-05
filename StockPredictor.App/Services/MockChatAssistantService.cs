using System.Globalization;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class MockChatAssistantService(
    DashboardDataService dashboardDataService,
    ExplanationService explanationService)
{
    private static readonly CultureInfo UiCulture = CultureInfo.GetCultureInfo("de-DE");

    private static readonly IReadOnlyList<string> SuggestedQuestions =
    [
        "Was zeigt das Dashboard?",
        "Wie aktuell sind die Daten im Export?",
        "Was bedeutet RMSE?",
        "Warum ist die Baseline wichtig?",
        "Was ist Walk-Forward-Validation?",
        "Welche Modelle vergleicht das Dashboard?"
    ];

    private static readonly IReadOnlyDictionary<string, IReadOnlyList<string>> TermKeywords =
        new Dictionary<string, IReadOnlyList<string>>(StringComparer.OrdinalIgnoreCase)
        {
            ["rmse"] = ["rmse", "wurzel", "fehler"],
            ["mae"] = ["mae", "mittlere absolute abweichung"],
            ["directional_accuracy"] = ["directional accuracy", "richtung", "richtungstreffer"],
            ["persistence_baseline"] = ["baseline", "persistence", "referenz"],
            ["rsi"] = ["rsi", "relative strength"],
            ["forecast"] = ["forecast", "prognose", "ausblick"],
            ["backtesting"] = ["backtesting", "backtest"],
            ["walk_forward_validation"] = ["walk-forward", "walk forward", "zeitfenster", "validierung"],
            ["feature_profile"] = ["feature-profil", "featureprofil", "features"],
            ["lag_features"] = ["lag", "lags", "lag-features"],
            ["random_forest"] = ["random forest", "wald"],
            ["decision_tree"] = ["decision tree", "entscheidungsbaum"],
            ["ridge_regression"] = ["ridge", "ridge regression", "ridge-regression"],
            ["lstm"] = ["lstm", "neurales netz"]
        };

    private static readonly IReadOnlyDictionary<string, IReadOnlyList<string>> FaqKeywords =
        new Dictionary<string, IReadOnlyList<string>>(StringComparer.OrdinalIgnoreCase)
        {
            ["dashboard"] = ["dashboard", "startseite", "zeigt"],
            ["uncertainty"] = ["unsicher", "unsicherheit", "sicher", "schwankt"],
            ["baseline"] = ["baseline", "referenz", "vergleich"],
            ["no_advice"] = ["anlageberatung", "beratung", "investieren", "kauf", "verkauf"],
            ["no_live_updates"] = ["live", "automatisch", "export", "aktualisiert", "datenstand"]
        };

    public Task<ChatAssistantAvailability> GetAvailabilityAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(new ChatAssistantAvailability
        {
            ActiveProvider = "FAQ-Fallback",
            ConfiguredMode = "mock",
            UsesFallback = true,
            StatusLabel = "Lokaler FAQ-Fallback",
            StatusMessage = "Ollama ist optional. Ohne lokales Modell beantwortet dieser Fallback einfache Fragen aus FAQ, Glossar und lokalem Dashboard-Export.",
            OllamaConfigured = false,
            OllamaReachable = false,
            OllamaModelAvailable = false
        });
    }

    public IReadOnlyList<string> GetSuggestedQuestions() => SuggestedQuestions;

    public async Task<ChatAssistantReply> AskAsync(
        IReadOnlyList<ChatAssistantMessage> conversation,
        CancellationToken cancellationToken = default)
    {
        var question = GetLatestUserQuestion(conversation);
        if (string.IsNullOrWhiteSpace(question))
        {
            return BuildReply(
                "Ich beantworte hier nur Fragen zum Dashboard, zu Kennzahlen, Modellen, Methoden und zum lokalen Forschungsstand der Bachelorarbeit.");
        }

        var snapshot = await dashboardDataService.GetLatestAsync(cancellationToken);
        var payload = snapshot.Payload;

        if (payload is not null && TryFindTicker(question, payload, out var ticker))
        {
            return BuildReply(BuildTickerSummary(payload, ticker));
        }

        if (TryFindExplanationTerm(question, out var term))
        {
            return BuildReply($"{term.Title}: {term.ShortText} {term.LongText}");
        }

        if (IsDataStatusQuestion(question))
        {
            return BuildReply(BuildDataStatusReply(snapshot));
        }

        if (IsModelComparisonQuestion(question))
        {
            return BuildReply(BuildModelOverviewReply(payload));
        }

        if (TryFindFaqItem(question, out var faqItem))
        {
            return BuildReply(faqItem.Answer);
        }

        return BuildReply(
            "Ich beantworte hier nur Fragen zum Dashboard, zu Kennzahlen, Modellen, Methoden und zum lokalen Exportstand. Gute Beispiele sind: Datenstand, RMSE, Baseline, Walk-Forward-Validation oder ein vorbereiteter Ticker wie AAPL.");
    }

    private ChatAssistantReply BuildReply(string content, string? statusMessage = null)
    {
        return new ChatAssistantReply
        {
            Content = content,
            ProviderLabel = "FAQ-Fallback",
            UsesFallback = true,
            StatusMessage = statusMessage
        };
    }

    private string BuildTickerSummary(DashboardPayload payload, FeaturedTicker ticker)
    {
        var selectedModel = !string.IsNullOrWhiteSpace(ticker.SelectedModel.ModelLabel)
            ? ticker.SelectedModel.ModelLabel
            : (!string.IsNullOrWhiteSpace(ticker.ForecastModelLabel) ? ticker.ForecastModelLabel : "nicht angegeben");

        var availableModels = ticker.AvailableModels.Count > 0
            ? string.Join(", ", ticker.AvailableModels.Select(model => model.ModelLabel))
            : "keine Modellliste im Export";

        var dataUntil = ticker.DataUntil ?? payload.DataUntil ?? ticker.LastCloseDate;
        var forecastGeneratedAt = ticker.ForecastGeneratedAt ?? payload.GeneratedAt;
        var rmseGap = ticker.WalkForwardBestRmse - ticker.WalkForwardBaselineRmse;
        var baselineText = ticker.BeatsBaselineRmse
            ? $"Das ausgewählte Modell liegt im Walk-Forward-RMSE um {FormatSignedValue(rmseGap)} unter der Baseline."
            : $"Die Baseline liegt im Walk-Forward-RMSE um {FormatAbsoluteValue(rmseGap)} vor dem ausgewählten Modell.";

        return
            $"Für {ticker.Ticker} liegen vorbereitete Dashboard-Daten vor. " +
            $"Letzter Schlusskurs: {FormatPrice(ticker.LastClose)} am {FormatDate(ticker.LastCloseDate)}. " +
            $"Datenstand: {FormatDate(dataUntil)}. Prognose erzeugt am: {FormatDateTime(forecastGeneratedAt)}. " +
            $"Prognosehorizont: {ticker.ForecastHorizonDays} Tage mit einer Forschungs-Schätzung von {FormatPercent(ticker.ForecastHorizonChangePct)}. " +
            $"Gewähltes Modell: {selectedModel}. Verfügbare Modelle: {availableModels}. " +
            $"{baselineText} Keine Anlageberatung.";
    }

    private string BuildDataStatusReply(DashboardDataSnapshot snapshot)
    {
        if (snapshot.Payload is null)
        {
            return
                $"Aktuell liegt auf diesem Rechner kein lesbarer Dashboard-Payload unter {snapshot.ResolvedPath} vor. " +
                "Dann zeigt die App nur den erklärenden Leerzustand. Für neue Daten muss zuerst der ML-Export lokal erzeugt werden.";
        }

        var payload = snapshot.Payload;
        var dataUntil = payload.DataUntil is null ? "nicht im Export angegeben" : FormatDate(payload.DataUntil.Value);
        var staleHint = payload.StaleAfterDays > 0
            ? $"Ab etwa {payload.StaleAfterDays} Tagen markiert die UI den Stand als älter."
            : "Für diesen Export ist keine explizite Verfallsgrenze gesetzt.";

        return
            $"Der aktuelle Dashboard-Export wurde am {FormatDateTime(payload.GeneratedAt)} geladen. " +
            $"Datenstand: {dataUntil}. {staleHint} Die App zeigt bewusst nur den zuletzt exportierten lokalen Stand und keinen garantierten Live-Datenstrom.";
    }

    private string BuildModelOverviewReply(DashboardPayload? payload)
    {
        if (payload is null)
        {
            return "Ohne lokalen Dashboard-Payload kann ich nur allgemein erklären: Das Dashboard vergleicht die Persistence-Baseline mit klassischen ML-Modellen wie Ridge Regression, Decision Tree und Random Forest sowie gegebenenfalls LSTM.";
        }

        var modelLabels = payload.FeaturedTickers
            .SelectMany(ticker => ticker.AvailableModels)
            .Select(model => model.ModelLabel)
            .Where(label => !string.IsNullOrWhiteSpace(label))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        if (modelLabels.Count == 0)
        {
            return "Im aktuellen Export ist keine Modellliste hinterlegt. Fachlich vergleicht das Dashboard aber mindestens die Baseline mit den trainierten Modellvarianten.";
        }

        var dominantModel = payload.SummaryCards.StarterBestExperiment.DominantBestModelLabel;
        var baselineBeaters = payload.SummaryCards.StarterTickersBeatingBaseline.Count;
        var total = payload.SummaryCards.StarterBestExperiment.TickerCount;

        return
            $"Im aktuellen Export tauchen diese Modellvarianten auf: {string.Join(", ", modelLabels)}. " +
            $"Als dominantes Modell im Starter-Korb ist {dominantModel} markiert. " +
            $"{baselineBeaters} von {total} Tickern schlagen dort im RMSE die Persistence-Baseline. " +
            "Die UI zeigt diese Werte als Modellvergleich und nicht als Handelssignal.";
    }

    private bool TryFindExplanationTerm(string question, out ExplanationTerm term)
    {
        foreach (var candidate in explanationService.GetAllTerms())
        {
            var keywords = TermKeywords.TryGetValue(candidate.Key, out var mappedKeywords)
                ? mappedKeywords
                : Array.Empty<string>();

            if (ContainsAny(question, keywords)
                || question.Contains(candidate.Title, StringComparison.OrdinalIgnoreCase))
            {
                term = candidate;
                return true;
            }
        }

        term = default!;
        return false;
    }

    private bool TryFindFaqItem(string question, out ExplanationFaqItem faqItem)
    {
        foreach (var candidate in explanationService.GetFaqItems())
        {
            var keywords = FaqKeywords.TryGetValue(candidate.Key, out var mappedKeywords)
                ? mappedKeywords
                : Array.Empty<string>();

            if (ContainsAny(question, keywords)
                || question.Contains(candidate.Question, StringComparison.OrdinalIgnoreCase))
            {
                faqItem = candidate;
                return true;
            }
        }

        faqItem = default!;
        return false;
    }

    private static string GetLatestUserQuestion(IReadOnlyList<ChatAssistantMessage> conversation)
    {
        return conversation
            .LastOrDefault(message => string.Equals(message.Role, "user", StringComparison.OrdinalIgnoreCase))
            ?.Content
            ?.Trim()
            ?? string.Empty;
    }

    private static bool IsDataStatusQuestion(string question)
    {
        return ContainsAny(question, ["datenstand", "aktuell", "export", "erzeugt", "generated", "veraltet", "stale"]);
    }

    private static bool IsModelComparisonQuestion(string question)
    {
        return ContainsAny(question, ["modellvergleich", "welche modelle", "modell", "benchmark", "baseline"]);
    }

    private static bool TryFindTicker(string question, DashboardPayload payload, out FeaturedTicker ticker)
    {
        ticker = payload.FeaturedTickers.FirstOrDefault(candidate =>
            question.Contains(candidate.Ticker, StringComparison.OrdinalIgnoreCase))!;

        return ticker is not null;
    }

    private static bool ContainsAny(string question, IReadOnlyList<string> keywords)
    {
        return keywords.Any(keyword => question.Contains(keyword, StringComparison.OrdinalIgnoreCase));
    }

    private static string FormatDate(DateOnly value) => value.ToString("dd. MMM yyyy", UiCulture);

    private static string FormatDateTime(DateTime value) => value.ToString("dd. MMM yyyy | HH:mm", UiCulture);

    private static string FormatPrice(double value) => value.ToString("N2", UiCulture);

    private static string FormatPercent(double value) => $"{(value >= 0 ? "+" : string.Empty)}{value.ToString("0.00", UiCulture)}%";

    private static string FormatSignedValue(double value) => $"{(value >= 0 ? "+" : "-")}{Math.Abs(value).ToString("0.000", UiCulture)}";

    private static string FormatAbsoluteValue(double value) => Math.Abs(value).ToString("0.000", UiCulture);
}
