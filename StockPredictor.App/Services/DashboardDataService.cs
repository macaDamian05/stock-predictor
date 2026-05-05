using System.Text.Json;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class DashboardDataService(IWebHostEnvironment environment, ILogger<DashboardDataService> logger)
{
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    public async Task<DashboardDataSnapshot> GetLatestAsync(CancellationToken cancellationToken = default)
    {
        var candidatePaths = GetCandidatePaths();

        foreach (var candidatePath in candidatePaths)
        {
            if (!File.Exists(candidatePath))
            {
                continue;
            }

            try
            {
                await using var stream = File.OpenRead(candidatePath);
                var payload = await JsonSerializer.DeserializeAsync<DashboardPayload>(
                    stream,
                    SerializerOptions,
                    cancellationToken);

                if (payload is not null)
                {
                    return new DashboardDataSnapshot(
                        payload,
                        candidatePath,
                        DashboardDataState.Available,
                        null,
                        candidatePaths);
                }

                return new DashboardDataSnapshot(
                    null,
                    candidatePath,
                    DashboardDataState.InvalidPayload,
                    "Die Datei wurde gefunden, enth\u00e4lt aber keinen g\u00fcltigen Dashboard-Payload.",
                    candidatePaths);
            }
            catch (Exception exception)
            {
                logger.LogWarning(exception, "Failed to load dashboard payload from {Path}", candidatePath);
                return new DashboardDataSnapshot(
                    null,
                    candidatePath,
                    DashboardDataState.InvalidPayload,
                    "Die Datei wurde gefunden, aber das JSON konnte nicht gelesen werden. Erzeuge den Export erneut.",
                    candidatePaths);
            }
        }

        return new DashboardDataSnapshot(
            null,
            candidatePaths.First(),
            DashboardDataState.Missing,
            "Kein Dashboard-Payload gefunden.",
            candidatePaths);
    }

    private IReadOnlyList<string> GetCandidatePaths()
    {
        var candidatePaths = new[]
        {
            Path.GetFullPath(Path.Combine(
                environment.ContentRootPath,
                "..",
                "StockPredictor.ML",
                "storage",
                "dashboard",
                "LATEST",
                "dashboard_payload.json")),
            Path.GetFullPath(Path.Combine(
                AppContext.BaseDirectory,
                "..",
                "..",
                "..",
                "..",
                "StockPredictor.ML",
                "storage",
                "dashboard",
                "LATEST",
                "dashboard_payload.json")),
        };

        return candidatePaths
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }
}

public sealed record DashboardDataSnapshot(
    DashboardPayload? Payload,
    string ResolvedPath,
    DashboardDataState State,
    string? ErrorMessage,
    IReadOnlyList<string> CheckedPaths)
{
    public bool IsMissing => State == DashboardDataState.Missing;

    public bool IsInvalidPayload => State == DashboardDataState.InvalidPayload;
}

public enum DashboardDataState
{
    Available,
    Missing,
    InvalidPayload,
}
