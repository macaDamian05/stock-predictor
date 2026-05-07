using System.Diagnostics;
using StockPredictor.App.Models;

namespace StockPredictor.App.Services;

public sealed class LocalMlWorkspaceService(IWebHostEnvironment environment)
{
    public string MlProjectRelativePath => "StockPredictor.ML";

    public string? ResolveMlProjectPath()
    {
        return GetMlProjectCandidates()
            .FirstOrDefault(Directory.Exists);
    }

    public string? ResolvePythonExecutable()
    {
        var mlProjectPath = ResolveMlProjectPath();
        if (mlProjectPath is null)
        {
            return null;
        }

        var candidates = new[]
        {
            Path.Combine(mlProjectPath, ".venv", "Scripts", "python.exe"),
            Path.Combine(mlProjectPath, ".venv", "bin", "python"),
        };

        return candidates.FirstOrDefault(File.Exists);
    }

    public IReadOnlyList<string> GetFallbackCommands(string ticker)
    {
        var normalizedTicker = ticker.Trim().ToUpperInvariant();
        return
        [
            "cd StockPredictor.ML",
            $".\\.venv\\Scripts\\python.exe run_classical_pipeline.py {normalizedTicker}",
            $".\\.venv\\Scripts\\python.exe export_dashboard_payload.py {normalizedTicker}",
        ];
    }

    public ProcessStartInfo? CreatePythonProcessStartInfo(IEnumerable<string> arguments)
    {
        var pythonPath = ResolvePythonExecutable();
        var mlProjectPath = ResolveMlProjectPath();

        if (pythonPath is null || mlProjectPath is null)
        {
            return null;
        }

        var startInfo = new ProcessStartInfo
        {
            FileName = pythonPath,
            WorkingDirectory = mlProjectPath,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        return startInfo;
    }

    private IReadOnlyList<string> GetMlProjectCandidates()
    {
        var contentRootCandidate = Path.GetFullPath(Path.Combine(
            environment.ContentRootPath,
            "..",
            MlProjectRelativePath));

        var baseDirectoryCandidate = Path.GetFullPath(Path.Combine(
            AppContext.BaseDirectory,
            "..",
            "..",
            "..",
            "..",
            MlProjectRelativePath));

        return
        [
            contentRootCandidate,
            baseDirectoryCandidate,
        ];
    }
}
