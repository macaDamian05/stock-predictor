using System.Diagnostics;
using System.Text.Json;
using Microsoft.Extensions.Options;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class MarketDataService(
    LocalMlWorkspaceService workspaceService,
    IOptions<MarketDataOptions> options,
    ILogger<MarketDataService> logger)
{
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    private readonly Dictionary<string, MarketAssetSnapshot> _memoryCache = new(StringComparer.OrdinalIgnoreCase);
    private readonly SemaphoreSlim _loadLock = new(1, 1);

    public async Task<MarketAssetSnapshot> GetSnapshotAsync(
        string ticker,
        bool forceRefresh = false,
        CancellationToken cancellationToken = default)
    {
        var snapshots = await GetSnapshotsAsync([ticker], forceRefresh, cancellationToken);
        return snapshots[ticker.Trim().ToUpperInvariant()];
    }

    public async Task<IReadOnlyDictionary<string, MarketAssetSnapshot>> GetSnapshotsAsync(
        IEnumerable<string> tickers,
        bool forceRefresh = false,
        CancellationToken cancellationToken = default)
    {
        var normalizedTickers = tickers
            .Select(NormalizeTicker)
            .Where(ticker => !string.IsNullOrWhiteSpace(ticker))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();

        if (normalizedTickers.Length == 0)
        {
            return new Dictionary<string, MarketAssetSnapshot>(StringComparer.OrdinalIgnoreCase);
        }

        var results = new Dictionary<string, MarketAssetSnapshot>(StringComparer.OrdinalIgnoreCase);
        var tickersToLoad = new List<string>();

        foreach (var ticker in normalizedTickers)
        {
            if (!forceRefresh && _memoryCache.TryGetValue(ticker, out var cachedSnapshot) && !ShouldRefresh(cachedSnapshot))
            {
                results[ticker] = cachedSnapshot;
            }
            else
            {
                tickersToLoad.Add(ticker);
            }
        }

        if (tickersToLoad.Count > 0)
        {
            await _loadLock.WaitAsync(cancellationToken);
            try
            {
                foreach (var ticker in tickersToLoad.ToArray())
                {
                    if (!forceRefresh && _memoryCache.TryGetValue(ticker, out var cachedSnapshot) && !ShouldRefresh(cachedSnapshot))
                    {
                        results[ticker] = cachedSnapshot;
                        tickersToLoad.Remove(ticker);
                    }
                }

                if (tickersToLoad.Count > 0)
                {
                    var loadedSnapshots = await LoadSnapshotsFromPythonAsync(tickersToLoad, cancellationToken);
                    foreach (var (ticker, snapshot) in loadedSnapshots)
                    {
                        _memoryCache[ticker] = snapshot;
                        results[ticker] = snapshot;
                    }
                }
            }
            finally
            {
                _loadLock.Release();
            }
        }

        foreach (var ticker in normalizedTickers)
        {
            if (!results.ContainsKey(ticker))
            {
                results[ticker] = BuildUnavailableSnapshot(
                    ticker,
                    "Für dieses Asset konnten lokal keine Marktdaten geladen werden.");
            }
        }

        return results;
    }

    public IReadOnlyList<MarketPricePoint> GetRangePoints(MarketAssetSnapshot snapshot, MarketTimeRange range)
    {
        if (!snapshot.HasData)
        {
            return [];
        }

        if (range == MarketTimeRange.OneDay)
        {
            if (snapshot.IntradayPoints.Count > 0)
            {
                return snapshot.IntradayPoints
                    .OrderBy(point => point.Timestamp)
                    .ToArray();
            }

            return snapshot.DailyPoints
                .OrderBy(point => point.Timestamp)
                .TakeLast(2)
                .ToArray();
        }

        var orderedDailyPoints = snapshot.DailyPoints
            .OrderBy(point => point.Timestamp)
            .ToArray();

        if (range == MarketTimeRange.Max)
        {
            return orderedDailyPoints;
        }

        if (orderedDailyPoints.Length == 0)
        {
            return [];
        }

        var lastTimestamp = orderedDailyPoints[^1].Timestamp;
        var threshold = range switch
        {
            MarketTimeRange.OneWeek => lastTimestamp.AddDays(-7),
            MarketTimeRange.OneMonth => lastTimestamp.AddMonths(-1),
            MarketTimeRange.SixMonths => lastTimestamp.AddMonths(-6),
            MarketTimeRange.OneYear => lastTimestamp.AddYears(-1),
            _ => orderedDailyPoints[0].Timestamp,
        };

        var filtered = orderedDailyPoints
            .Where(point => point.Timestamp >= threshold)
            .ToArray();

        return filtered.Length > 0 ? filtered : orderedDailyPoints;
    }

    public IReadOnlyDictionary<MarketTimeRange, MarketRangeChange> GetRangeChanges(MarketAssetSnapshot snapshot)
    {
        var ranges = Enum.GetValues<MarketTimeRange>();
        var result = new Dictionary<MarketTimeRange, MarketRangeChange>();

        foreach (var range in ranges)
        {
            result[range] = BuildRangeChange(snapshot, range);
        }

        return result;
    }

    private async Task<IReadOnlyDictionary<string, MarketAssetSnapshot>> LoadSnapshotsFromPythonAsync(
        IReadOnlyList<string> tickers,
        CancellationToken cancellationToken)
    {
        var startInfo = workspaceService.CreatePythonProcessStartInfo(BuildMarketDataArguments(tickers));
        if (startInfo is null)
        {
            return tickers.ToDictionary(
                ticker => ticker,
                ticker => BuildUnavailableSnapshot(
                    ticker,
                    "Die lokale Python-Umgebung unter StockPredictor.ML/.venv wurde nicht gefunden. Marktdaten können erst geladen werden, wenn die virtuelle Umgebung vorhanden ist."),
                StringComparer.OrdinalIgnoreCase);
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

        if (process.ExitCode != 0)
        {
            logger.LogWarning(
                "Market data export failed for {Tickers}. Exit code {ExitCode}. stderr: {StdErr}",
                string.Join(", ", tickers),
                process.ExitCode,
                stdErr);

            return tickers.ToDictionary(
                ticker => ticker,
                ticker => BuildUnavailableSnapshot(
                    ticker,
                    string.IsNullOrWhiteSpace(stdErr)
                        ? "Lokale Marktdaten konnten nicht geladen werden. Prüfe yfinance, Netzwerkzugriff und die Python-Umgebung."
                        : stdErr.Trim()),
                StringComparer.OrdinalIgnoreCase);
        }

        var payload = JsonSerializer.Deserialize<MarketDataBatchPayload>(stdOut, SerializerOptions);
        if (payload is null)
        {
            return tickers.ToDictionary(
                ticker => ticker,
                ticker => BuildUnavailableSnapshot(
                    ticker,
                    "Die lokale Markt-Datenausgabe konnte nicht gelesen werden."),
                StringComparer.OrdinalIgnoreCase);
        }

        var snapshots = payload.Results
            .Select(snapshot =>
            {
                snapshot.LoadedAt = DateTime.Now;
                return snapshot;
            })
            .ToDictionary(snapshot => NormalizeTicker(snapshot.Ticker), StringComparer.OrdinalIgnoreCase);

        foreach (var ticker in tickers)
        {
            if (!snapshots.ContainsKey(ticker))
            {
                snapshots[ticker] = BuildUnavailableSnapshot(
                    ticker,
                    "Für dieses Asset wurde kein Markt-Snapshot zurückgegeben.");
            }
        }

        return snapshots;
    }

    private IEnumerable<string> BuildMarketDataArguments(IReadOnlyList<string> tickers)
    {
        yield return "export_market_data.py";
        foreach (var ticker in tickers)
        {
            yield return ticker;
        }

        yield return "--start-date";
        yield return options.Value.StartDate;
        yield return "--intraday-period";
        yield return options.Value.IntradayPeriod;
        yield return "--intraday-interval";
        yield return options.Value.IntradayInterval;
        yield return "--use-cache-if-fresh-minutes";
        yield return Math.Max(0, options.Value.CacheFreshMinutes).ToString();
    }

    private bool ShouldRefresh(MarketAssetSnapshot snapshot)
    {
        var freshnessWindow = TimeSpan.FromMinutes(Math.Max(1, options.Value.InMemoryFreshMinutes));
        return snapshot.LoadedAt < DateTime.Now - freshnessWindow;
    }

    private static MarketAssetSnapshot BuildUnavailableSnapshot(string ticker, string errorMessage)
    {
        return new MarketAssetSnapshot
        {
            Ticker = ticker,
            GeneratedAt = DateTime.Now,
            LoadedAt = DateTime.Now,
            Status = "error",
            Error = errorMessage,
        };
    }

    private MarketRangeChange BuildRangeChange(MarketAssetSnapshot snapshot, MarketTimeRange range)
    {
        var points = GetRangePoints(snapshot, range)
            .Where(point => point.Close is not null)
            .ToArray();

        if (points.Length < 2)
        {
            return new MarketRangeChange
            {
                Range = range,
                StartClose = points.FirstOrDefault()?.Close,
                EndClose = points.LastOrDefault()?.Close,
                AbsoluteChange = 0,
                PercentChange = 0,
            };
        }

        var startClose = points[0].Close ?? 0;
        var endClose = points[^1].Close ?? 0;
        var absoluteChange = endClose - startClose;
        var percentChange = Math.Abs(startClose) < double.Epsilon
            ? 0
            : (absoluteChange / startClose) * 100.0;

        return new MarketRangeChange
        {
            Range = range,
            StartClose = startClose,
            EndClose = endClose,
            AbsoluteChange = absoluteChange,
            PercentChange = percentChange,
        };
    }

    private static string NormalizeTicker(string ticker)
    {
        return (ticker ?? string.Empty).Trim().ToUpperInvariant();
    }
}
