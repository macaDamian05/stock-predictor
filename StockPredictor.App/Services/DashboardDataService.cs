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
        foreach (var candidatePath in GetCandidatePaths())
        {
            if (!File.Exists(candidatePath))
            {
                continue;
            }

            try
            {
                await using var stream = File.OpenRead(candidatePath);
                var payload = await JsonSerializer.DeserializeAsync<DashboardPayload>(stream, SerializerOptions, cancellationToken);

                if (payload is not null)
                {
                    return new DashboardDataSnapshot(payload, candidatePath, null);
                }
            }
            catch (Exception exception)
            {
                logger.LogWarning(exception, "Failed to load dashboard payload from {Path}", candidatePath);
                return new DashboardDataSnapshot(
                    null,
                    candidatePath,
                    "The dashboard export exists, but the JSON could not be parsed.");
            }
        }

        return new DashboardDataSnapshot(
            null,
            GetCandidatePaths().First(),
            "Dashboard payload not found. Run export_dashboard_payload.py to generate the UI data export.");
    }

    private IReadOnlyList<string> GetCandidatePaths()
    {
        return
        [
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
        ];
    }
}

public sealed record DashboardDataSnapshot(
    DashboardPayload? Payload,
    string ResolvedPath,
    string? ErrorMessage);
