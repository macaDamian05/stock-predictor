from __future__ import annotations

import argparse
import json
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from core.classical_models import RandomForestConfig
from core.data_loader import download_price_data
from core.paths import ensure_runtime_directories, get_benchmark_artifact_paths
from core.tabular_features import build_next_close_dataset, chronological_train_test_split
from run_classical_pipeline import evaluate_models, run_walk_forward_evaluation


DEFAULT_TICKERS = ["AAPL", "TSLA", "DOU.DE"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare multiple tickers with the classical walk-forward pipeline."
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Ticker symbols to compare. Defaults to AAPL, TSLA and DOU.DE.",
    )
    parser.add_argument("--start-date", default="1990-01-01", help="Historical download start date.")
    parser.add_argument("--end-date", default=None, help="Historical download end date.")
    parser.add_argument("--lags", type=int, default=10, help="Number of lagged return features.")
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of chronological samples reserved for the holdout test.",
    )
    parser.add_argument(
        "--walk-forward-folds",
        type=int,
        default=5,
        help="Number of expanding walk-forward folds.",
    )
    parser.add_argument(
        "--walk-forward-train-size",
        type=float,
        default=0.7,
        help="Initial training fraction for walk-forward evaluation.",
    )
    parser.add_argument("--n-estimators", type=int, default=300, help="Random Forest tree count.")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=12,
        help="Maximum tree depth. Use 0 to disable the limit.",
    )
    parser.add_argument(
        "--min-samples-leaf",
        type=int,
        default=5,
        help="Minimum number of samples per leaf in the Random Forest.",
    )
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--run-name",
        default=None,
        help="Optional artifact folder name. Defaults to a timestamp-based name.",
    )
    return parser.parse_args()


def build_random_forest_config(args: argparse.Namespace) -> RandomForestConfig:
    return RandomForestConfig(
        n_estimators=args.n_estimators,
        max_depth=None if args.max_depth == 0 else args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.random_state,
    )


def save_comparison_plot(artifact_path, benchmark_frame: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(12, 10))
    y_positions = range(len(benchmark_frame))

    axes[0].barh(
        [position - 0.2 for position in y_positions],
        benchmark_frame["walk_forward_baseline_rmse"],
        height=0.4,
        label="Baseline",
    )
    axes[0].barh(
        [position + 0.2 for position in y_positions],
        benchmark_frame["walk_forward_random_forest_rmse"],
        height=0.4,
        label="Random Forest",
    )
    axes[0].set_yticks(list(y_positions))
    axes[0].set_yticklabels(benchmark_frame["ticker"])
    axes[0].set_title("Walk-forward RMSE by ticker")
    axes[0].set_xlabel("RMSE")
    axes[0].grid(True, axis="x")
    axes[0].legend()

    axes[1].barh(
        [position - 0.2 for position in y_positions],
        benchmark_frame["walk_forward_baseline_directional_accuracy"] * 100.0,
        height=0.4,
        label="Baseline",
    )
    axes[1].barh(
        [position + 0.2 for position in y_positions],
        benchmark_frame["walk_forward_random_forest_directional_accuracy"] * 100.0,
        height=0.4,
        label="Random Forest",
    )
    axes[1].set_yticks(list(y_positions))
    axes[1].set_yticklabels(benchmark_frame["ticker"])
    axes[1].set_title("Walk-forward directional accuracy by ticker")
    axes[1].set_xlabel("Directional accuracy (%)")
    axes[1].grid(True, axis="x")
    axes[1].legend()

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def build_report(
    benchmark_frame: pd.DataFrame,
    failures: list[dict[str, str]],
    run_name: str,
) -> str:
    lines = [
        f"# Benchmark Report: {run_name}",
        "",
        "Dieser Lauf vergleicht die klassische Pipeline ueber mehrere Ticker.",
        "",
        "## Ranking nach Walk-Forward-RMSE",
        "",
    ]

    for rank, row in enumerate(benchmark_frame.itertuples(index=False), start=1):
        lines.append(
            f"{rank}. {row.ticker}: RF RMSE {row.walk_forward_random_forest_rmse:.4f}, "
            f"Baseline RMSE {row.walk_forward_baseline_rmse:.4f}, "
            f"RF Richtung {row.walk_forward_random_forest_directional_accuracy:.2%}"
        )

    if failures:
        lines.extend(["", "## Fehlgeschlagene Ticker", ""])
        for failure in failures:
            lines.append(f"- {failure['ticker']}: {failure['error']}")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    tickers = [ticker.upper() for ticker in (args.tickers or DEFAULT_TICKERS)]
    run_name = args.run_name or (
        "benchmark_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    artifacts = get_benchmark_artifact_paths(run_name)
    random_forest_config = build_random_forest_config(args)

    benchmark_rows: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []

    for ticker in tickers:
        print(f"Running benchmark for {ticker}...")
        try:
            price_data = download_price_data(
                ticker=ticker,
                start_date=args.start_date,
                end_date=args.end_date or pd.Timestamp.today().date().isoformat(),
            )
            dataset = build_next_close_dataset(price_data, lags=args.lags)
            train_frame, test_frame = chronological_train_test_split(
                dataset.supervised_frame,
                test_size=args.test_size,
            )
            _, holdout_metrics, _, _ = evaluate_models(
                train_frame=train_frame,
                evaluation_frame=test_frame,
                dataset=dataset,
                random_forest_config=random_forest_config,
                evaluation_name="holdout",
            )
            _, walk_forward_summary = run_walk_forward_evaluation(
                supervised_frame=dataset.supervised_frame,
                dataset=dataset,
                random_forest_config=random_forest_config,
                initial_train_size=args.walk_forward_train_size,
                folds=args.walk_forward_folds,
            )
            if walk_forward_summary is None:
                raise ValueError("Walk-forward evaluation is disabled or returned no results.")

            benchmark_rows.append(
                {
                    "ticker": ticker,
                    "data_start": price_data.index[0].date().isoformat(),
                    "data_end": price_data.index[-1].date().isoformat(),
                    "data_rows": len(price_data),
                    "supervised_rows": len(dataset.supervised_frame),
                    "holdout_baseline_rmse": holdout_metrics["baseline_persistence"]["rmse"],
                    "holdout_random_forest_rmse": holdout_metrics["random_forest"]["rmse"],
                    "holdout_baseline_directional_accuracy": holdout_metrics[
                        "baseline_persistence"
                    ]["directional_accuracy"],
                    "holdout_random_forest_directional_accuracy": holdout_metrics[
                        "random_forest"
                    ]["directional_accuracy"],
                    "walk_forward_baseline_rmse": walk_forward_summary["overall"][
                        "baseline_persistence"
                    ]["rmse"],
                    "walk_forward_random_forest_rmse": walk_forward_summary["overall"][
                        "random_forest"
                    ]["rmse"],
                    "walk_forward_baseline_directional_accuracy": walk_forward_summary[
                        "overall"
                    ]["baseline_persistence"]["directional_accuracy"],
                    "walk_forward_random_forest_directional_accuracy": walk_forward_summary[
                        "overall"
                    ]["random_forest"]["directional_accuracy"],
                    "walk_forward_fold_count": walk_forward_summary["fold_count"],
                    "walk_forward_total_predictions": walk_forward_summary["total_predictions"],
                    "rf_minus_baseline_rmse": walk_forward_summary["overall"]["random_forest"][
                        "rmse"
                    ]
                    - walk_forward_summary["overall"]["baseline_persistence"]["rmse"],
                }
            )
        except Exception as error:
            failures.append({"ticker": ticker, "error": str(error)})
            print(f"  Failed: {error}")

    if not benchmark_rows:
        raise RuntimeError("No benchmark result could be generated.")

    benchmark_frame = pd.DataFrame(benchmark_rows).sort_values(
        "walk_forward_random_forest_rmse"
    )
    benchmark_frame.to_csv(artifacts.summary_csv, index=False)
    artifacts.summary_json.write_text(
        json.dumps(
            {
                "run_name": run_name,
                "tickers": tickers,
                "successful_tickers": benchmark_frame["ticker"].tolist(),
                "failed_tickers": failures,
                "random_forest": {
                    "n_estimators": random_forest_config.n_estimators,
                    "max_depth": random_forest_config.max_depth,
                    "min_samples_leaf": random_forest_config.min_samples_leaf,
                    "random_state": random_forest_config.random_state,
                },
                "walk_forward": {
                    "folds": args.walk_forward_folds,
                    "initial_train_size": args.walk_forward_train_size,
                },
                "results": benchmark_frame.to_dict(orient="records"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    save_comparison_plot(artifacts.comparison_plot, benchmark_frame)
    artifacts.report.write_text(
        build_report(
            benchmark_frame=benchmark_frame,
            failures=failures,
            run_name=run_name,
        ),
        encoding="utf-8",
    )

    print(f"Benchmark run: {run_name}")
    print("Ranking by walk-forward Random Forest RMSE:")
    for row in benchmark_frame.itertuples(index=False):
        print(
            f"  {row.ticker}: RF RMSE={row.walk_forward_random_forest_rmse:.4f} | "
            f"Baseline RMSE={row.walk_forward_baseline_rmse:.4f} | "
            f"RF Direction={row.walk_forward_random_forest_directional_accuracy:.2%}"
        )
    if failures:
        print("Failed tickers:")
        for failure in failures:
            print(f"  {failure['ticker']}: {failure['error']}")
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
