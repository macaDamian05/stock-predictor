using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public interface IChatAssistantService
{
    Task<ChatAssistantAvailability> GetAvailabilityAsync(CancellationToken cancellationToken = default);

    Task<ChatAssistantReply> AskAsync(
        IReadOnlyList<ChatAssistantMessage> conversation,
        CancellationToken cancellationToken = default);

    IReadOnlyList<string> GetSuggestedQuestions();
}
