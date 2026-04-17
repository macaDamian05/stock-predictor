from __future__ import annotations

import argparse
import json
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from core.benchmark_presets import TICKER_BASKETS, get_ticker_basket
from core.data_loader import download_price_data
from core.paths import ensure_runtime_directories, get_benchmark_artifact_paths
from core.tabular_features import (
    DEFAULT_FEATURE_PROFILE,
    FEATURE_PROFILES,
    build_next_close_dataset,
    chronological_train_test_split,
)
from run_classical_pipeline import (
    MODEL_DISPLAY_NAMES,
    MODEL_ORDER,
    build_decision_tree_config,
    build_random_forest_config,
    build_ridge_config,
    evaluate_models,
    run_walk_forward_evaluation,
    select_best_model_from_metric_source,
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare multiple tickers with the classical walk-forward pipeline."
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Ticker symbols to compare. When empty, the selected basket preset is used.",
    )
    parser.add_argument(
        "--basket-preset",
        default="starter",
        choices=list(TICKER_BASKETS),
        help="Named ticker basket for benchmark runs.",
    )
    parser.add_argument("--start-date", default="1990-01-01", help="Historical download start date.")
    parser.add_argument("--end-date", default=None, help="Historical download end date.")
    parser.add_argument("--lags", type=int, default=10, help="Number of lagged return features.")
    parser.add_argument(
        "--feature-profile",
        default=DEFAULT_FEATURE_PROFILE,
        choices=list(FEATURE_PROFILES),
        help="Feature profile for the classical models.",
    )
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
    parser.add_argument(
        "--ridge-alpha",
        type=float,
        default=1.0,
        help="Regularization strength for the Ridge Regression model.",
    )
    parser.add_argument(
        "--tree-max-depth",
        type=int,
        default=8,
        help="Maximum tree depth for the Decision Tree. Use 0 to disable the limit.",
    )
    parser.add_argument(
        "--tree-min-samples-leaf",
        type=int,
        default=5,
        help="Minimum number of samples per leaf for the Decision Tree.",
    )
    parser.add_argument("--n-estimators", type=int, default=300, help="Random Forest tree count.")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=12,
        help="Maximum tree depth for the Random Forest. Use 0 to disable the limit.",
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


def save_comparison_plot(artifact_path, benchmark_frame: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(13, 10))
    y_positions = list(range(len(benchmark_frame)))
    bar_height = 0.8 / len(MODEL_ORDER)
    offsets = [
        (-0.4 + (bar_height / 2.0)) + (index * bar_height) for index in range(len(MODEL_ORDER))
    ]

    for suffix, title, xlabel, scale in [
        ("rmse", "Walk-forward RMSE by ticker", "RMSE", 1.0),
        (
            "directional_accuracy",
            "Walk-forward directional accuracy by ticker",
            "Directional accuracy (%)",
            100.0,
        ),
    ]:
        current_axis = axes[0] if suffix == "rmse" else axes[1]
        for offset, model_name in zip(offsets, MODEL_ORDER):
            current_axis.barh(
                [position + offset for position in y_positions],
                benchmark_frame[f"walk_forward_{model_name}_{suffix}"] * scale,
                height=bar_height,
                label=MODEL_DISPLAY_NAMES[model_name],
            )
        current_axis.set_yticks(y_positions)
        current_axis.set_yticklabels(benchmark_frame["ticker"])
        current_axis.set_title(title)
        current_axis.set_xlabel(xlabel)
        current_axis.grid(True, axis="x")
        current_axis.legend()

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
        "## Ranking nach bestem Walk-Forward-RMSE",
        "",
    ]

    for rank, row in enumerate(benchmark_frame.itertuples(index=False), start=1):
        lines.append(
            f"{rank}. {row.ticker}: bestes Modell {MODEL_DISPLAY_NAMES[row.best_learned_model]}, "
            f"Best-RMSE {row.best_learned_rmse:.4f}, "
            f"Baseline-RMSE {row.walk_forward_baseline_persistence_rmse:.4f}, "
            f"Best-Richtung {row.best_learned_directional_accuracy:.2%}"
        )

    if failures:
        lines.extend(["", "## Fehlgeschlagene Ticker", ""])
        for failure in failures:
            lines.append(f"- {failure['ticker']}: {failure['error']}")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    tickers = [ticker.upper() for ticker in (args.tickers or get_ticker_basket(args.basket_preset))]
    run_name = args.run_name or ("benchmark_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    artifacts = get_benchmark_artifact_paths(run_name)
    ridge_config = build_ridge_config(args)
    decision_tree_config = build_decision_tree_config(args)
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
            dataset = build_next_close_dataset(
                price_data,
                lags=args.lags,
                feature_profile=args.feature_profile,
            )
            train_frame, test_frame = chronological_train_test_split(
                dataset.supervised_frame,
                test_size=args.test_size,
            )
            _, holdout_metrics, _ = evaluate_models(
                train_frame=train_frame,
                evaluation_frame=test_frame,
                dataset=dataset,
                ridge_config=ridge_config,
                decision_tree_config=decision_tree_config,
                random_forest_config=random_forest_config,
                evaluation_name="holdout",
            )
            _, walk_forward_summary = run_walk_forward_evaluation(
                supervised_frame=dataset.supervised_frame,
                dataset=dataset,
                ridge_config=ridge_config,
                decision_tree_config=decision_tree_config,
                random_forest_config=random_forest_config,
                initial_train_size=args.walk_forward_train_size,
                folds=args.walk_forward_folds,
            )
            if walk_forward_summary is None:
                raise ValueError("Walk-forward evaluation is disabled or returned no results.")

            best_learned_model = select_best_model_from_metric_source(
                walk_forward_summary["overall"]
            )
            benchmark_row: dict[str, object] = {
                "ticker": ticker,
                "data_start": price_data.index[0].date().isoformat(),
                "data_end": price_data.index[-1].date().isoformat(),
                "data_rows": len(price_data),
                "supervised_rows": len(dataset.supervised_frame),
                "walk_forward_fold_count": walk_forward_summary["fold_count"],
                "walk_forward_total_predictions": walk_forward_summary["total_predictions"],
                "best_learned_model": best_learned_model,
                "best_learned_rmse": walk_forward_summary["overall"][best_learned_model]["rmse"],
                "best_learned_directional_accuracy": walk_forward_summary["overall"][
                    best_learned_model
                ]["directional_accuracy"],
                "best_learned_minus_baseline_rmse": walk_forward_summary["overall"][
                    best_learned_model
                ]["rmse"]
                - walk_forward_summary["overall"]["baseline_persistence"]["rmse"],
            }

            for model_name in MODEL_ORDER:
                benchmark_row[f"holdout_{model_name}_rmse"] = holdout_metrics[model_name]["rmse"]
                benchmark_row[f"holdout_{model_name}_directional_accuracy"] = holdout_metrics[
                    model_name
                ]["directional_accuracy"]
                benchmark_row[f"walk_forward_{model_name}_rmse"] = walk_forward_summary[
                    "overall"
                ][model_name]["rmse"]
                benchmark_row[
                    f"walk_forward_{model_name}_directional_accuracy"
                ] = walk_forward_summary["overall"][model_name]["directional_accuracy"]

            benchmark_rows.append(benchmark_row)
        except Exception as error:
            failures.append({"ticker": ticker, "error": str(error)})
            print(f"  Failed: {error}")

    if not benchmark_rows:
        raise RuntimeError("No benchmark result could be generated.")

    benchmark_frame = pd.DataFrame(benchmark_rows).sort_values("best_learned_rmse")
    benchmark_frame.to_csv(artifacts.summary_csv, index=False)
    artifacts.summary_json.write_text(
        json.dumps(
            {
                "run_name": run_name,
                "tickers": tickers,
                "basket_preset": args.basket_preset,
                "successful_tickers": benchmark_frame["ticker"].tolist(),
                "failed_tickers": failures,
                "feature_profile": args.feature_profile,
                "models": {
                    "ridge_regression": {
                        "alpha": ridge_config.alpha,
                    },
                    "decision_tree": {
                        "max_depth": decision_tree_config.max_depth,
                        "min_samples_leaf": decision_tree_config.min_samples_leaf,
                        "random_state": decision_tree_config.random_state,
                    },
                    "random_forest": {
                        "n_estimators": random_forest_config.n_estimators,
                        "max_depth": random_forest_config.max_depth,
                        "min_samples_leaf": random_forest_config.min_samples_leaf,
                        "random_state": random_forest_config.random_state,
                    },
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
    print("Ranking by best learned walk-forward RMSE:")
    for row in benchmark_frame.itertuples(index=False):
        print(
            f"  {row.ticker}: "
            f"{MODEL_DISPLAY_NAMES[row.best_learned_model]} "
            f"RMSE={row.best_learned_rmse:.4f} | "
            f"Baseline RMSE={row.walk_forward_baseline_persistence_rmse:.4f} | "
            f"Direction={row.best_learned_directional_accuracy:.2%}"
        )
    if failures:
        print("Failed tickers:")
        for failure in failures:
            print(f"  {failure['ticker']}: {failure['error']}")
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
