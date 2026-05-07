using System.Collections.Concurrent;
using System.Diagnostics;
using Microsoft.Extensions.Options;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class ForecastJobService(
    LocalMlWorkspaceService workspaceService,
    DashboardDataService dashboardDataService,
    IOptions<ForecastAutomationOptions> options,
    ILogger<ForecastJobService> logger)
{
    private readonly ConcurrentDictionary<string, ForecastJobSnapshot> _jobs = new(StringComparer.OrdinalIgnoreCase);
    private readonly SemaphoreSlim _executionLock = new(1, 1);

    public event Action? JobsChanged;

    public IReadOnlyList<ForecastJobSnapshot> GetJobs()
    {
        return _jobs.Values
            .OrderByDescending(job => job.RequestedAt)
            .ToArray();
    }

    public ForecastJobSnapshot? GetJob(string ticker)
    {
        _jobs.TryGetValue(NormalizeTicker(ticker), out var snapshot);
        return snapshot;
    }

    public async Task<ForecastJobSnapshot> RequestForecastAsync(
        string ticker,
        ForecastJobTrigger trigger,
        DashboardPayload? currentPayload = null,
        CancellationToken cancellationToken = default)
    {
        var normalizedTicker = NormalizeTicker(ticker);
        if (string.IsNullOrWhiteSpace(normalizedTicker))
        {
            throw new ArgumentException("Ticker must not be empty.", nameof(ticker));
        }

        if (_jobs.TryGetValue(normalizedTicker, out var existingJob)
            && (existingJob.State == ForecastJobState.Pending || existingJob.State == ForecastJobState.Running))
        {
            return existingJob;
        }

        var job = new ForecastJobSnapshot
        {
            Ticker = normalizedTicker,
            State = ForecastJobState.Pending,
            Trigger = trigger,
            RequestedAt = DateTime.Now,
            Message = trigger == ForecastJobTrigger.AutomaticStaleRefresh
                ? "Veralteter Forecast wurde erkannt. Die Aktualisierung läuft lokal im Hintergrund."
                : "Lokaler Forecast-Lauf wurde vorbereitet.",
            SuggestedCommands = workspaceService.GetFallbackCommands(normalizedTicker).ToList(),
        };

        _jobs[normalizedTicker] = job;
        JobsChanged?.Invoke();

        _ = Task.Run(async () =>
        {
            await RunJobAsync(job, currentPayload, CancellationToken.None);
        });

        return job;
    }

    public async Task QueueAutomaticRefreshesAsync(
        DashboardPayload payload,
        IEnumerable<string> tickers,
        CancellationToken cancellationToken = default)
    {
        if (!options.Value.AutoRefreshEnabled)
        {
            return;
        }

        var normalizedTickers = tickers
            .Select(NormalizeTicker)
            .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();

        foreach (var ticker in normalizedTickers)
        {
            var featuredTicker = payload.FeaturedTickers.FirstOrDefault(entry =>
                string.Equals(entry.Ticker, ticker, StringComparison.OrdinalIgnoreCase));

            if (featuredTicker is null || !IsStale(payload, featuredTicker))
            {
                continue;
            }

            if (_jobs.TryGetValue(ticker, out var existingJob))
            {
                if (existingJob.State is ForecastJobState.Pending or ForecastJobState.Running)
                {
                    continue;
                }

                var cooldownMinutes = Math.Max(1, options.Value.AutoRefreshCooldownMinutes);
                if (existingJob.RequestedAt >= DateTime.Now.AddMinutes(-cooldownMinutes))
                {
                    continue;
                }
            }

            await RequestForecastAsync(
                ticker,
                ForecastJobTrigger.AutomaticStaleRefresh,
                payload,
                cancellationToken);
        }
    }

    private async Task RunJobAsync(
        ForecastJobSnapshot pendingJob,
        DashboardPayload? currentPayload,
        CancellationToken cancellationToken)
    {
        var normalizedTicker = pendingJob.Ticker;

        await UpdateJobAsync(normalizedTicker, job => job with
        {
            State = ForecastJobState.Running,
            StartedAt = DateTime.Now,
            Message = pendingJob.Trigger == ForecastJobTrigger.AutomaticStaleRefresh
                ? "Forecast-Daten werden im Hintergrund aktualisiert. Du kannst die App weiter benutzen. Dies kann einige Minuten dauern."
                : "Lokaler Forecast-Lauf wurde gestartet. Dies kann einige Minuten dauern.",
        });

        if (workspaceService.ResolveMlProjectPath() is null || workspaceService.ResolvePythonExecutable() is null)
        {
            await UpdateJobAsync(normalizedTicker, job => job with
            {
                State = ForecastJobState.Failed,
                CompletedAt = DateTime.Now,
                ErrorMessage = "Die lokale Python-Umgebung unter StockPredictor.ML/.venv wurde nicht gefunden.",
                Message = "Forecast-Lauf konnte nicht gestartet werden.",
            });
            return;
        }

        await _executionLock.WaitAsync(cancellationToken);
        try
        {
            var currentPayloadSnapshot = currentPayload is not null
                ? new DashboardDataSnapshot(currentPayload, string.Empty, DashboardDataState.Available, null, [])
                : await dashboardDataService.GetLatestAsync(cancellationToken);

            var exportTickers = currentPayloadSnapshot.Payload?.FeaturedTickers
                .Select(ticker => NormalizeTicker(ticker.Ticker))
                .Append(normalizedTicker)
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToArray()
                ?? [normalizedTicker];

            var pipelineResult = await RunPythonCommandAsync(
                [
                    "run_classical_pipeline.py",
                    normalizedTicker,
                ],
                cancellationToken);

            if (!pipelineResult.Success)
            {
                await UpdateJobAsync(normalizedTicker, job => job with
                {
                    State = ForecastJobState.Failed,
                    CompletedAt = DateTime.Now,
                    ErrorMessage = pipelineResult.ErrorMessage,
                    Message = "Der lokale Forecast-Lauf ist fehlgeschlagen.",
                });
                return;
            }

            var exportArgs = new List<string> { "export_dashboard_payload.py" };
            exportArgs.AddRange(exportTickers);
            var exportResult = await RunPythonCommandAsync(exportArgs, cancellationToken);
            if (!exportResult.Success)
            {
                await UpdateJobAsync(normalizedTicker, job => job with
                {
                    State = ForecastJobState.Failed,
                    CompletedAt = DateTime.Now,
                    ErrorMessage = exportResult.ErrorMessage,
                    Message = "Der Forecast wurde berechnet, aber der Dashboard-Export konnte nicht aktualisiert werden.",
                });
                return;
            }

            await UpdateJobAsync(normalizedTicker, job => job with
            {
                State = ForecastJobState.Completed,
                CompletedAt = DateTime.Now,
                ErrorMessage = null,
                Message = "Lokaler Forecast-Lauf und Dashboard-Export wurden erfolgreich abgeschlossen.",
            });
        }
        finally
        {
            _executionLock.Release();
        }
    }

    private async Task<(bool Success, string? ErrorMessage)> RunPythonCommandAsync(
        IReadOnlyList<string> arguments,
        CancellationToken cancellationToken)
    {
        var startInfo = workspaceService.CreatePythonProcessStartInfo(arguments);
        if (startInfo is null)
        {
            return (false, "Die lokale Python-Umgebung wurde nicht gefunden.");
        }

        using var process = new Process
        {
            StartInfo = startInfo,
        };

        process.Start();
        var stdOutTask = process.StandardOutput.ReadToEndAsync(cancellationToken);
        var stdErrTask = process.StandardError.ReadToEndAsync(cancellationToken);

        await process.WaitForExitAsync(cancellationToken);
        var stdOut = await stdOutTask;
        var stdErr = await stdErrTask;

        if (process.ExitCode == 0)
        {
            return (true, null);
        }

        var errorMessage = string.IsNullOrWhiteSpace(stdErr)
            ? stdOut.Trim()
            : stdErr.Trim();

        logger.LogWarning(
            "Python command failed: {Arguments} | ExitCode={ExitCode} | Error={Error}",
            string.Join(" ", arguments),
            process.ExitCode,
            errorMessage);

        return (false, errorMessage);
    }

    private async Task UpdateJobAsync(string ticker, Func<ForecastJobSnapshot, ForecastJobSnapshot> update)
    {
        if (_jobs.TryGetValue(ticker, out var currentJob))
        {
            _jobs[ticker] = update(currentJob);
            await Task.Yield();
            JobsChanged?.Invoke();
        }
    }

    private bool IsStale(DashboardPayload payload, FeaturedTicker ticker)
    {
        var staleAfterDays = Math.Max(1, options.Value.AutoRefreshStaleAfterDays);
        var today = DateOnly.FromDateTime(DateTime.Now);
        var dataUntil = ticker.DataUntil ?? payload.DataUntil ?? ticker.LastCloseDate;
        var dataAgeDays = today.DayNumber - dataUntil.DayNumber;
        var forecastGeneratedAt = ticker.ForecastGeneratedAt ?? payload.GeneratedAt;
        var forecastAgeDays = Math.Max(0, (DateTime.Now.Date - forecastGeneratedAt.Date).Days);
        return dataAgeDays > staleAfterDays || forecastAgeDays > staleAfterDays;
    }

    private static string NormalizeTicker(string ticker)
    {
        return (ticker ?? string.Empty).Trim().ToUpperInvariant();
    }
}
