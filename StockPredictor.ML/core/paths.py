from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = PROJECT_ROOT / "storage"
TRAINING_DATA_DIR = STORAGE_DIR / "trainingsdaten"
CLASSICAL_DATA_DIR = STORAGE_DIR / "classical"
BENCHMARK_DATA_DIR = STORAGE_DIR / "benchmarks"
EXPERIMENT_DATA_DIR = STORAGE_DIR / "experiments"
MULTI_ASSET_DATA_DIR = STORAGE_DIR / "multi_asset"
MULTI_ASSET_SUITE_DATA_DIR = STORAGE_DIR / "multi_asset_suites"
THESIS_DATA_DIR = STORAGE_DIR / "thesis"
DASHBOARD_DATA_DIR = STORAGE_DIR / "dashboard"
MARKET_DATA_DIR = STORAGE_DIR / "market_data"


@dataclass(frozen=True)
class ArtifactPaths:
    ticker: str
    safe_ticker: str
    base_dir: Path
    model: Path
    scaler: Path
    metadata: Path
    log: Path


@dataclass(frozen=True)
class ClassicalArtifactPaths:
    source_name: str
    safe_name: str
    base_dir: Path
    model: Path
    metrics: Path
    predictions: Path
    walk_forward_metrics: Path
    walk_forward_predictions: Path
    forecast: Path
    summary: Path
    metadata: Path
    history_plot: Path
    test_plot: Path
    walk_forward_plot: Path
    forecast_plot: Path


@dataclass(frozen=True)
class BenchmarkArtifactPaths:
    run_name: str
    safe_name: str
    base_dir: Path
    summary_csv: Path
    summary_json: Path
    comparison_plot: Path
    report: Path


@dataclass(frozen=True)
class ExperimentArtifactPaths:
    run_name: str
    safe_name: str
    base_dir: Path
    summary_csv: Path
    summary_json: Path
    comparison_plot: Path
    report: Path
    per_ticker_csv: Path


@dataclass(frozen=True)
class MultiAssetArtifactPaths:
    run_name: str
    safe_name: str
    base_dir: Path
    model: Path
    summary_csv: Path
    summary_json: Path
    per_ticker_metrics_csv: Path
    forecast_csv: Path
    holdout_predictions_csv: Path
    walk_forward_predictions_csv: Path
    report: Path
    comparison_plot: Path


@dataclass(frozen=True)
class MultiAssetSuiteArtifactPaths:
    run_name: str
    safe_name: str
    base_dir: Path
    summary_csv: Path
    summary_json: Path
    best_configs_csv: Path
    report: Path
    comparison_plot: Path


@dataclass(frozen=True)
class ProfileComparisonArtifactPaths:
    run_name: str
    safe_name: str
    base_dir: Path
    summary_csv: Path
    summary_json: Path
    per_ticker_csv: Path
    report: Path
    mean_rmse_plot: Path
    delta_plot: Path


@dataclass(frozen=True)
class ThesisArtifactPaths:
    run_name: str
    safe_name: str
    base_dir: Path
    report: Path
    starter_models_csv: Path
    starter_suite_csv: Path
    core_profile_summary_csv: Path
    core_profile_per_ticker_csv: Path
    summary_json: Path
    starter_rmse_plot: Path
    core_profile_plot: Path
    core_profile_delta_plot: Path
    model_wins_plot: Path
    diversified_profile_summary_csv: Path
    diversified_profile_per_ticker_csv: Path
    diversified_profile_plot: Path
    diversified_profile_delta_plot: Path
    basket_comparison_plot: Path


@dataclass(frozen=True)
class DashboardArtifactPaths:
    run_name: str
    safe_name: str
    base_dir: Path
    payload_json: Path
    featured_tickers_csv: Path
    basket_summary_csv: Path
    company_ranking_csv: Path
    multi_asset_summary_csv: Path


@dataclass(frozen=True)
class MarketDataArtifactPaths:
    ticker: str
    safe_ticker: str
    base_dir: Path
    snapshot_json: Path


def ensure_runtime_directories() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    CLASSICAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    BENCHMARK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIMENT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    MULTI_ASSET_DATA_DIR.mkdir(parents=True, exist_ok=True)
    MULTI_ASSET_SUITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    THESIS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    MARKET_DATA_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_name(value: str, uppercase: bool = False) -> str:
    normalized = value.upper() if uppercase else value
    return re.sub(r"[^A-Za-z0-9._-]", "_", normalized)


def sanitize_ticker(ticker: str) -> str:
    return sanitize_name(ticker, uppercase=True)


def get_artifact_paths(ticker: str) -> ArtifactPaths:
    safe_ticker = sanitize_ticker(ticker)
    base_dir = TRAINING_DATA_DIR / safe_ticker
    base_dir.mkdir(parents=True, exist_ok=True)

    return ArtifactPaths(
        ticker=ticker.upper(),
        safe_ticker=safe_ticker,
        base_dir=base_dir,
        model=base_dir / f"{safe_ticker}_lstm_model.keras",
        scaler=base_dir / f"{safe_ticker}_scaler.save",
        metadata=base_dir / f"{safe_ticker}_meta.json",
        log=base_dir / "training_log.txt",
    )


def get_classical_artifact_paths(source_name: str) -> ClassicalArtifactPaths:
    safe_name = sanitize_name(source_name, uppercase=True)
    base_dir = CLASSICAL_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return ClassicalArtifactPaths(
        source_name=source_name,
        safe_name=safe_name,
        base_dir=base_dir,
        model=base_dir / "classical_models.joblib",
        metrics=base_dir / "metrics.json",
        predictions=base_dir / "predictions.csv",
        walk_forward_metrics=base_dir / "walk_forward_metrics.json",
        walk_forward_predictions=base_dir / "walk_forward_predictions.csv",
        forecast=base_dir / "forecast.json",
        summary=base_dir / "summary.json",
        metadata=base_dir / "metadata.json",
        history_plot=base_dir / "price_history.png",
        test_plot=base_dir / "test_predictions.png",
        walk_forward_plot=base_dir / "walk_forward_predictions.png",
        forecast_plot=base_dir / "future_forecast.png",
    )


def get_benchmark_artifact_paths(run_name: str) -> BenchmarkArtifactPaths:
    safe_name = sanitize_name(run_name, uppercase=True)
    base_dir = BENCHMARK_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return BenchmarkArtifactPaths(
        run_name=run_name,
        safe_name=safe_name,
        base_dir=base_dir,
        summary_csv=base_dir / "benchmark_summary.csv",
        summary_json=base_dir / "benchmark_summary.json",
        comparison_plot=base_dir / "benchmark_comparison.png",
        report=base_dir / "benchmark_report.md",
    )


def get_experiment_artifact_paths(run_name: str) -> ExperimentArtifactPaths:
    safe_name = sanitize_name(run_name, uppercase=True)
    base_dir = EXPERIMENT_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return ExperimentArtifactPaths(
        run_name=run_name,
        safe_name=safe_name,
        base_dir=base_dir,
        summary_csv=base_dir / "experiment_summary.csv",
        summary_json=base_dir / "experiment_summary.json",
        comparison_plot=base_dir / "experiment_comparison.png",
        report=base_dir / "experiment_report.md",
        per_ticker_csv=base_dir / "ticker_best_configs.csv",
    )


def get_multi_asset_artifact_paths(run_name: str) -> MultiAssetArtifactPaths:
    safe_name = sanitize_name(run_name, uppercase=True)
    base_dir = MULTI_ASSET_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return MultiAssetArtifactPaths(
        run_name=run_name,
        safe_name=safe_name,
        base_dir=base_dir,
        model=base_dir / "multi_asset_models.joblib",
        summary_csv=base_dir / "multi_asset_summary.csv",
        summary_json=base_dir / "multi_asset_summary.json",
        per_ticker_metrics_csv=base_dir / "per_ticker_metrics.csv",
        forecast_csv=base_dir / "forecast_summary.csv",
        holdout_predictions_csv=base_dir / "holdout_predictions.csv",
        walk_forward_predictions_csv=base_dir / "walk_forward_predictions.csv",
        report=base_dir / "multi_asset_report.md",
        comparison_plot=base_dir / "per_ticker_comparison.png",
    )


def get_multi_asset_suite_artifact_paths(run_name: str) -> MultiAssetSuiteArtifactPaths:
    safe_name = sanitize_name(run_name, uppercase=True)
    base_dir = MULTI_ASSET_SUITE_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return MultiAssetSuiteArtifactPaths(
        run_name=run_name,
        safe_name=safe_name,
        base_dir=base_dir,
        summary_csv=base_dir / "multi_asset_suite_summary.csv",
        summary_json=base_dir / "multi_asset_suite_summary.json",
        best_configs_csv=base_dir / "basket_best_configs.csv",
        report=base_dir / "multi_asset_suite_report.md",
        comparison_plot=base_dir / "multi_asset_suite_comparison.png",
    )


def get_profile_comparison_artifact_paths(run_name: str) -> ProfileComparisonArtifactPaths:
    safe_name = sanitize_name(run_name, uppercase=True)
    base_dir = EXPERIMENT_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return ProfileComparisonArtifactPaths(
        run_name=run_name,
        safe_name=safe_name,
        base_dir=base_dir,
        summary_csv=base_dir / "profile_comparison_summary.csv",
        summary_json=base_dir / "profile_comparison_summary.json",
        per_ticker_csv=base_dir / "profile_comparison_per_ticker.csv",
        report=base_dir / "profile_comparison_report.md",
        mean_rmse_plot=base_dir / "profile_comparison_mean_rmse.png",
        delta_plot=base_dir / "profile_comparison_delta_per_ticker.png",
    )


def get_thesis_artifact_paths(run_name: str) -> ThesisArtifactPaths:
    safe_name = sanitize_name(run_name, uppercase=True)
    base_dir = THESIS_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return ThesisArtifactPaths(
        run_name=run_name,
        safe_name=safe_name,
        base_dir=base_dir,
        report=base_dir / "thesis_results_report.md",
        starter_models_csv=base_dir / "starter_model_results.csv",
        starter_suite_csv=base_dir / "starter_suite_results.csv",
        core_profile_summary_csv=base_dir / "core_profile_summary.csv",
        core_profile_per_ticker_csv=base_dir / "core_profile_per_ticker.csv",
        summary_json=base_dir / "thesis_results_summary.json",
        starter_rmse_plot=base_dir / "starter_best_vs_baseline_rmse.png",
        core_profile_plot=base_dir / "core_profile_mean_rmse.png",
        core_profile_delta_plot=base_dir / "core_profile_delta_per_ticker.png",
        model_wins_plot=base_dir / "core_profile_model_wins.png",
        diversified_profile_summary_csv=base_dir / "diversified_profile_summary.csv",
        diversified_profile_per_ticker_csv=base_dir / "diversified_profile_per_ticker.csv",
        diversified_profile_plot=base_dir / "diversified_profile_mean_rmse.png",
        diversified_profile_delta_plot=base_dir / "diversified_profile_delta_per_ticker.png",
        basket_comparison_plot=base_dir / "basket_profile_comparison.png",
    )


def get_dashboard_artifact_paths(run_name: str) -> DashboardArtifactPaths:
    safe_name = sanitize_name(run_name, uppercase=True)
    base_dir = DASHBOARD_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return DashboardArtifactPaths(
        run_name=run_name,
        safe_name=safe_name,
        base_dir=base_dir,
        payload_json=base_dir / "dashboard_payload.json",
        featured_tickers_csv=base_dir / "featured_tickers.csv",
        basket_summary_csv=base_dir / "basket_summary.csv",
        company_ranking_csv=base_dir / "company_ranking.csv",
        multi_asset_summary_csv=base_dir / "multi_asset_summary.csv",
    )


def get_market_data_artifact_paths(ticker: str) -> MarketDataArtifactPaths:
    safe_ticker = sanitize_ticker(ticker)
    base_dir = MARKET_DATA_DIR / safe_ticker
    base_dir.mkdir(parents=True, exist_ok=True)

    return MarketDataArtifactPaths(
        ticker=ticker.upper(),
        safe_ticker=safe_ticker,
        base_dir=base_dir,
        snapshot_json=base_dir / "snapshot.json",
    )
