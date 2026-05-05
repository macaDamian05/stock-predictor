namespace StockPredictor.App.Models;

public sealed class ExplanationTerm
{
    public string Key { get; init; } = string.Empty;

    public string Title { get; init; } = string.Empty;

    public string Category { get; init; } = string.Empty;

    public string ShortText { get; init; } = string.Empty;

    public string LongText { get; init; } = string.Empty;
}
