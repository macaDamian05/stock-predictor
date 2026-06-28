namespace StockPredictor.App.Models;

public sealed record LocalUserProfileResult(
    LocalUserProfile Profile,
    bool UsedFallback,
    bool MigratedLegacyWatchlist,
    string? Message);

public sealed record LocalUserProfileImportResult(
    bool Success,
    LocalUserProfile? Profile,
    string Message);
