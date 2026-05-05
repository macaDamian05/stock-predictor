using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class ExplanationService
{
    private static readonly IReadOnlyList<string> CategoryOrder =
    [
        "Kennzahlen",
        "Methodik",
        "Modelle"
    ];

    private static readonly IReadOnlyList<ExplanationTerm> Terms =
    [
        new()
        {
            Key = "rmse",
            Title = "RMSE",
            Category = "Kennzahlen",
            ShortText = "Misst die typische Abweichung zwischen Prognose und echtem Wert. Kleinere Werte sind besser.",
            LongText = "RMSE gewichtet größere Fehler stärker als kleine Fehler. Deshalb ist der Wert besonders nützlich, wenn Ausreißer sichtbar werden sollen."
        },
        new()
        {
            Key = "mae",
            Title = "MAE",
            Category = "Kennzahlen",
            ShortText = "Zeigt die durchschnittliche absolute Abweichung. Kleinere Werte sind besser.",
            LongText = "MAE ist leichter direkt zu lesen als RMSE, weil alle Fehler gleich stark zählen und große Ausreißer nicht zusätzlich verstärkt werden."
        },
        new()
        {
            Key = "directional_accuracy",
            Title = "Directional Accuracy",
            Category = "Kennzahlen",
            ShortText = "Zeigt, wie oft das Modell die Richtung richtig trifft: aufwärts, abwärts oder seitwärts.",
            LongText = "Diese Kennzahl bewertet nicht den exakten Preis, sondern die richtige Bewegungsrichtung. Für Finanzzeitreihen ist das oft eine wichtige Ergänzung zu RMSE und MAE."
        },
        new()
        {
            Key = "rsi",
            Title = "RSI",
            Category = "Kennzahlen",
            ShortText = "Technischer Indikator zwischen 0 und 100, der überkaufte oder überverkaufte Phasen andeuten kann.",
            LongText = "Im Dashboard dient der RSI nur als zusätzliche Einordnung des Marktumfelds. Er ist hier kein Kauf- oder Verkaufssignal."
        },
        new()
        {
            Key = "forecast",
            Title = "Forecast",
            Category = "Methodik",
            ShortText = "Forschungsbasierte Schätzung zukünftiger Schlusskurse auf Basis des zuletzt exportierten Modells.",
            LongText = "Die App zeigt keinen Live-Algorithmus, sondern den zuletzt exportierten ML-Stand. Ohne neuen Export bleibt auch der Forecast unverändert."
        },
        new()
        {
            Key = "backtesting",
            Title = "Backtesting",
            Category = "Methodik",
            ShortText = "Test mit historischen Daten, um zu prüfen, wie ein Modell in früheren Marktphasen abgeschnitten hätte.",
            LongText = "Backtesting ersetzt keine echte Zukunft, hilft aber dabei, Modelle unter realistischeren zeitlichen Bedingungen zu vergleichen."
        },
        new()
        {
            Key = "walk_forward_validation",
            Title = "Walk-Forward-Validation",
            Category = "Methodik",
            ShortText = "Backtesting in zeitlicher Reihenfolge: trainieren, nächstes Zeitfenster testen und danach weiter nach vorn schieben.",
            LongText = "Diese Methode ist für Zeitreihen wichtig, weil sie die zeitliche Reihenfolge respektiert und keine zukünftigen Daten in frühere Trainingsphasen mischt."
        },
        new()
        {
            Key = "persistence_baseline",
            Title = "Persistence-Baseline",
            Category = "Methodik",
            ShortText = "Sehr einfache Referenz: Morgen ist ungefähr wie heute. Ein komplexeres Modell muss diese Hürde erst schlagen.",
            LongText = "Die Baseline ist wichtig, weil ein ML-Modell nur dann fachlich überzeugt, wenn es besser abschneidet als eine sehr einfache Vergleichsmethode."
        },
        new()
        {
            Key = "feature_profile",
            Title = "Feature-Profil",
            Category = "Methodik",
            ShortText = "Vordefinierte Auswahl von Eingabemerkmalen, zum Beispiel nur Lags oder zusätzliche technische Indikatoren.",
            LongText = "Verschiedene Feature-Profile erlauben einen sauberen Vergleich, welche Informationsmenge für ein Modell wirklich hilfreich ist."
        },
        new()
        {
            Key = "lag_features",
            Title = "Lag-Features",
            Category = "Methodik",
            ShortText = "Frühere Werte einer Zeitreihe, zum Beispiel Schlusskurse der letzten Tage, die als Eingabe für das Modell dienen.",
            LongText = "Lag-Features helfen dem Modell, Muster aus der Vergangenheit zu nutzen, ohne dass dafür sofort komplexe Zusatzdaten nötig sind."
        },
        new()
        {
            Key = "random_forest",
            Title = "Random Forest",
            Category = "Modelle",
            ShortText = "Modell aus vielen Entscheidungsbäumen. Oft robust, aber nicht automatisch das beste Modell für Zeitreihen.",
            LongText = "Random Forest kann nichtlineare Muster gut abbilden. Gleichzeitig bleibt die Baseline bei Finanzdaten oft überraschend stark."
        },
        new()
        {
            Key = "decision_tree",
            Title = "Decision Tree",
            Category = "Modelle",
            ShortText = "Baumförmiges Modell, das Entscheidungen schrittweise über Regeln trifft.",
            LongText = "Entscheidungsbäume sind leicht zu lesen, können aber bei Zeitreihen instabil werden, wenn sie zu stark auf einzelne Muster passen."
        },
        new()
        {
            Key = "ridge_regression",
            Title = "Ridge Regression",
            Category = "Modelle",
            ShortText = "Lineares Modell mit Regularisierung. Häufig stabil, wenn Zusammenhänge eher einfach bleiben.",
            LongText = "Ridge Regression bestraft zu große Koeffizienten und wirkt dadurch oft robuster als ein unreguliertes lineares Modell."
        },
        new()
        {
            Key = "lstm",
            Title = "LSTM",
            Category = "Modelle",
            ShortText = "Neuronales Netz für Reihenfolgen, das zeitliche Muster lernen kann, aber mehr Daten und Rechenaufwand braucht.",
            LongText = "LSTM ist für sequenzielle Daten interessant, muss aber in der Praxis sauber validiert werden. Mehr Komplexität bedeutet nicht automatisch bessere Prognosen."
        }
    ];

    private static readonly IReadOnlyList<ExplanationFaqItem> FaqItems =
    [
        new()
        {
            Key = "dashboard",
            Question = "Was zeigt das Dashboard?",
            Answer = "Das Dashboard zeigt den zuletzt exportierten Stand der Bachelorarbeit: vorbereitete Kurse, Forschungsprognosen, Modellvergleiche und kompakte Kennzahlen für ausgewählte Assets."
        },
        new()
        {
            Key = "uncertainty",
            Question = "Warum sind Prognosen unsicher?",
            Answer = "Finanzmärkte ändern sich ständig. Modelle lernen nur aus vergangenen Daten und können unerwartete Ereignisse, neue Marktphasen oder plötzliche Stimmungswechsel nicht sicher vorwegnehmen."
        },
        new()
        {
            Key = "baseline",
            Question = "Warum ist die Baseline wichtig?",
            Answer = "Die Baseline ist die Mindesthürde für ein komplexeres Modell. Wenn ein ML-Modell nicht besser ist als eine sehr einfache Referenz, ist sein Zusatznutzen fachlich schwach."
        },
        new()
        {
            Key = "no_advice",
            Question = "Was bedeutet \"keine Anlageberatung\"?",
            Answer = "Die App ist ein Forschungs- und Visualisierungssystem. Sie soll Modelle verständlich machen, aber keine Aufforderung zum Kaufen, Verkaufen oder Halten von Wertpapieren geben."
        },
        new()
        {
            Key = "no_live_updates",
            Question = "Warum ändern sich Prognosen nicht automatisch, wenn kein neuer Export erzeugt wurde?",
            Answer = "Die App liest lokal gespeicherte Exportdateien. Ohne neuen ML-Lauf und neuen Export bleibt der zuletzt erzeugte Stand sichtbar, auch wenn sich der Markt inzwischen weiterbewegt hat."
        }
    ];

    private readonly IReadOnlyDictionary<string, ExplanationTerm> _termsByKey =
        Terms.ToDictionary(term => term.Key, StringComparer.OrdinalIgnoreCase);

    public IReadOnlyList<string> GetCategories() => CategoryOrder;

    public IReadOnlyList<ExplanationTerm> GetAllTerms() => Terms;

    public IReadOnlyList<ExplanationTerm> GetTermsByCategory(string category)
    {
        return Terms
            .Where(term => string.Equals(term.Category, category, StringComparison.OrdinalIgnoreCase))
            .ToList();
    }

    public ExplanationTerm? GetTerm(string termKey)
    {
        if (string.IsNullOrWhiteSpace(termKey))
        {
            return null;
        }

        return _termsByKey.TryGetValue(termKey, out var term) ? term : null;
    }

    public IReadOnlyList<ExplanationFaqItem> GetFaqItems() => FaqItems;
}
