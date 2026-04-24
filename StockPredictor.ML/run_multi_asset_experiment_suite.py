from __future__ import annotations

import argparse
import json
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from core.benchmark_presets import TICKER_BASKETS, get_ticker_basket
from core.data_loader import download_price_data
from core.multi_asset import build_multi_asset_dataset, chronological_train_test_split_by_target_date
from core.paths import ensure_runtime_directories, get_multi_asset_suite_artifact_paths
from core.tabular_features import DEFAULT_FEATURE_PROFILE, FEATURE_PROFILES
from run_classical_pipeline import (
    MODEL_DISPLAY_NAMES,
    build_decision_tree_config,
    build_random_forest_config,
    build_ridge_config,
    select_best_model_from_metric_source,
)
from run_multi_asset_pipeline import (
    build_forecast_summary_frame,
    build_per_ticker_metrics_frame,
    evaluate_multi_asset_models,
    run_multi_asset_walk_forward_evaluation,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a compact experiment suite for pooled multi-asset training."
    )
    parser.add_argument(
        "--basket-presets",
        nargs="+",
        default=["mixed_assets", "etf_core"],
        choices=list(TICKER_BASKETS),
        help="Named ticker baskets for the pooled suite.",
    )
    parser.add_argument("--start-date", default="1990-01-01", help="Historical download start date.")
    parser.add_argument("--end-date", default=None, help="Historical download end date.")
    parser.add_argument(
        "--feature-profiles",
        nargs="+",
        default=["technical_basic", DEFAULT_FEATURE_PROFILE],
        choices=list(FEATURE_PROFILES),
        help="Feature profiles to compare.",
    )
    parser.add_argument(
        "--lag-values",
        nargs="+",
        type=int,
        default=[5, 10],
        help="Lag values to compare.",
    )
    parser.add_argument(
        "--forecast-days",
        type=int,
        default=5,
        help="Forecast horizon per asset.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of shared target dates reserved for holdout evaluation.",
    )
    parser.add_argument(
        "--walk-forward-folds",
        type=int,
        default=5,
        help="Number of expanding walk-forward folds over shared target dates.",
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


def build_experiment_id(basket_preset: str, feature_profile: str, lags: int) -> str:
    return f"{basket_preset}__{feature_profile}__lag{lags}"


def save_suite_plot(artifact_path, summary_frame: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(14, 10))
    labels = summary_frame["experiment_id"].tolist()
    x_positions = list(range(len(labels)))

    axes[0].bar(
        [position - 0.2 for position in x_positions],
        summary_frame["baseline_rmse"],
        width=0.4,
        label="Baseline RMSE",
    )
    axes[0].bar(
        [position + 0.2 for position in x_positions],
        summary_frame["shared_model_rmse"],
        width=0.4,
        label="Shared model RMSE",
    )
    axes[0].set_title("Pooled multi-asset RMSE by experiment")
    axes[0].set_ylabel("RMSE")
    axes[0].set_xticks(x_positions)
    axes[0].set_xticklabels(labels, rotation=30, ha="right")
    axes[0].grid(True, axis="y")
    axes[0].legend()

    axes[1].bar(
        x_positions,
        summary_frame["shared_model_minus_baseline_rmse"],
        label="Shared model minus baseline RMSE",
    )
    axes[1].plot(
        x_positions,
        summary_frame["shared_model_directional_accuracy"] * 100.0,
        color="red",
        marker="o",
        label="Shared model directional accuracy (%)",
    )
    axes[1].axhline(0.0, color="black", linewidth=1)
    axes[1].set_title("RMSE gap and directional accuracy by pooled experiment")
    axes[1].set_ylabel("Gap / Accuracy")
    axes[1].set_xticks(x_positions)
    axes[1].set_xticklabels(labels, rotation=30, ha="right")
    axes[1].grid(True, axis="y")
    axes[1].legend()

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def build_report(
    run_name: str,
    summary_frame: pd.DataFrame,
    best_configs_frame: pd.DataFrame,
    failures: list[dict[str, str]],
) -> str:
    lines = [
        f"# Multi-Asset Experiment Suite: {run_name}",
        "",
        "Diese Suite vergleicht gemeinsame Multi-Asset-Trainingslaeufe ueber mehrere Koerbe.",
        "",
        "## Beste Konfiguration pro Korb",
        "",
    ]

    for row in best_configs_frame.itertuples(index=False):
        lines.append(
            f"- {row.basket_preset}: `{row.experiment_id}` mit "
            f"{row.shared_model_label}, shared RMSE {row.shared_model_rmse:.4f}, "
            f"Baseline {row.baseline_rmse:.4f}, mittlere 5-Tage-Aenderung "
            f"{row.mean_forecast_horizon_change_pct:+.2f}%"
        )

    lines.extend(["", "## Gesamtranking", ""])
    for rank, row in enumerate(summary_frame.itertuples(index=False), start=1):
        lines.append(
            f"{rank}. `{row.experiment_id}`: shared RMSE {row.shared_model_rmse:.4f}, "
            f"Baseline {row.baseline_rmse:.4f}, "
            f"Modell {row.shared_model_label}"
        )

    if failures:
        lines.extend(["", "## Fehlgeschlagene Experimente", ""])
        for failure in failures:
            lines.append(
                f"- {failure['experiment_id']}: {failure['error']}"
            )

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    run_name = args.run_name or ("multi_asset_suite_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    artifacts = get_multi_asset_suite_artifact_paths(run_name)

    ridge_config = build_ridge_config(args)
    decision_tree_config = build_decision_tree_config(args)
    random_forest_config = build_random_forest_config(args)

    market_data_cache: dict[str, pd.DataFrame] = {}
    summary_rows: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []

    for basket_preset in args.basket_presets:
        tickers = [ticker.upper() for ticker in get_ticker_basket(basket_preset)]
        for feature_profile in args.feature_profiles:
            for lags in args.lag_values:
                experiment_id = build_experiment_id(basket_preset, feature_profile, lags)
                print(f"Running pooled experiment {experiment_id}...")
                try:
                    price_data_by_ticker: dict[str, pd.DataFrame] = {}
                    for ticker in tickers:
                        if ticker not in market_data_cache:
                            market_data_cache[ticker] = download_price_data(
                                ticker=ticker,
                                start_date=args.start_date,
                                end_date=args.end_date or pd.Timestamp.today().date().isoformat(),
                            )
                        price_data_by_ticker[ticker] = market_data_cache[ticker]

                    dataset = build_multi_asset_dataset(
                        price_data_by_ticker=price_data_by_ticker,
                        lags=lags,
                        feature_profile=feature_profile,
                    )
                    train_frame, test_frame = chronological_train_test_split_by_target_date(
                        frame=dataset.supervised_frame,
                        target_date_column=dataset.target_date_column,
                        test_size=args.test_size,
                    )
                    holdout_predictions, holdout_metrics, trained_models = evaluate_multi_asset_models(
                        train_frame=train_frame,
                        evaluation_frame=test_frame,
                        dataset=dataset,
                        ridge_config=ridge_config,
                        decision_tree_config=decision_tree_config,
                        random_forest_config=random_forest_config,
                        evaluation_name="holdout",
                    )
                    walk_forward_predictions, walk_forward_summary = run_multi_asset_walk_forward_evaluation(
                        supervised_frame=dataset.supervised_frame,
                        dataset=dataset,
                        ridge_config=ridge_config,
                        decision_tree_config=decision_tree_config,
                        random_forest_config=random_forest_config,
                        initial_train_size=args.walk_forward_train_size,
                        folds=args.walk_forward_folds,
                    )

                    shared_metric_source = (
                        walk_forward_summary["overall"] if walk_forward_summary is not None else holdout_metrics
                    )
                    shared_model_name = select_best_model_from_metric_source(shared_metric_source)
                    per_ticker_frame = build_per_ticker_metrics_frame(
                        dataset=dataset,
                        holdout_predictions=holdout_predictions,
                        walk_forward_predictions=walk_forward_predictions,
                        shared_model_name=shared_model_name,
                    )
                    forecast_frame = build_forecast_summary_frame(
                        dataset=dataset,
                        price_data_by_ticker=price_data_by_ticker,
                        shared_model=trained_models[shared_model_name],
                        shared_model_name=shared_model_name,
                        lags=lags,
                        forecast_days=args.forecast_days,
                    )

                    summary_rows.append(
                        {
                            "experiment_id": experiment_id,
                            "basket_preset": basket_preset,
                            "tickers": ",".join(tickers),
                            "ticker_count": len(tickers),
                            "feature_profile": feature_profile,
                            "lags": lags,
                            "shared_model_name": shared_model_name,
                            "shared_model_label": MODEL_DISPLAY_NAMES[shared_model_name],
                            "shared_model_rmse": shared_metric_source[shared_model_name]["rmse"],
                            "shared_model_directional_accuracy": shared_metric_source[shared_model_name][
                                "directional_accuracy"
                            ],
                            "baseline_rmse": shared_metric_source["baseline_persistence"]["rmse"],
                            "shared_model_minus_baseline_rmse": shared_metric_source[shared_model_name]["rmse"]
                            - shared_metric_source["baseline_persistence"]["rmse"],
                            "mean_best_learned_rmse": per_ticker_frame["best_learned_rmse"].mean(),
                            "mean_forecast_horizon_change_pct": forecast_frame[
                                "forecast_horizon_change_pct"
                            ].mean(),
                            "mean_average_forecast_distance_pct_to_last_close": forecast_frame[
                                "average_forecast_distance_pct_to_last_close"
                            ].mean(),
                            "top_forecast_ticker": forecast_frame.iloc[0]["ticker"],
                            "top_forecast_horizon_change_pct": forecast_frame.iloc[0][
                                "forecast_horizon_change_pct"
                            ],
                        }
                    )
                except Exception as error:
                    failures.append(
                        {
                            "experiment_id": experiment_id,
                            "error": str(error),
                        }
                    )
                    print(f"  Failed: {error}")

    if not summary_rows:
        raise RuntimeError("No pooled multi-asset experiment result could be generated.")

    summary_frame = pd.DataFrame(summary_rows).sort_values("shared_model_rmse")
    best_configs_frame = (
        summary_frame.sort_values(["basket_preset", "shared_model_rmse"])
        .groupby("basket_preset", as_index=False)
        .first()
        .sort_values("shared_model_rmse")
    )

    summary_frame.to_csv(artifacts.summary_csv, index=False)
    best_configs_frame.to_csv(artifacts.best_configs_csv, index=False)
    artifacts.summary_json.write_text(
        json.dumps(
            {
                "run_name": run_name,
                "basket_presets": args.basket_presets,
                "feature_profiles": args.feature_profiles,
                "lag_values": args.lag_values,
                "forecast_days": args.forecast_days,
                "summary": summary_frame.to_dict(orient="records"),
                "basket_best_configs": best_configs_frame.to_dict(orient="records"),
                "failures": failures,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    save_suite_plot(artifacts.comparison_plot, summary_frame)
    artifacts.report.write_text(
        build_report(
            run_name=run_name,
            summary_frame=summary_frame,
            best_configs_frame=best_configs_frame,
            failures=failures,
        ),
        encoding="utf-8",
    )

    print(f"Multi-asset suite run: {run_name}")
    print("Best configuration per basket:")
    for row in best_configs_frame.itertuples(index=False):
        print(
            f"  {row.basket_preset}: {row.experiment_id} | "
            f"{row.shared_model_label} RMSE={row.shared_model_rmse:.4f} | "
            f"Baseline={row.baseline_rmse:.4f}"
        )
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
