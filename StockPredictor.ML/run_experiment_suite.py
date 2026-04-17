from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from core.benchmark_presets import TICKER_BASKETS, get_ticker_basket
from core.data_loader import download_price_data
from core.paths import ensure_runtime_directories, get_experiment_artifact_paths
from core.tabular_features import (
    DEFAULT_FEATURE_PROFILE,
    FEATURE_PROFILES,
    build_next_close_dataset,
    chronological_train_test_split,
)
from run_classical_pipeline import (
    LEARNED_MODEL_ORDER,
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
        description="Run a reproducible experiment suite across baskets, feature profiles and lags."
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Optional explicit ticker list. When empty, the basket preset is used.",
    )
    parser.add_argument(
        "--basket-preset",
        default="starter",
        choices=list(TICKER_BASKETS),
        help="Named ticker basket for the suite.",
    )
    parser.add_argument("--start-date", default="1990-01-01", help="Historical download start date.")
    parser.add_argument("--end-date", default=None, help="Historical download end date.")
    parser.add_argument(
        "--feature-profiles",
        nargs="+",
        default=["lag_only", "technical_basic", DEFAULT_FEATURE_PROFILE],
        choices=list(FEATURE_PROFILES),
        help="Feature profiles to compare.",
    )
    parser.add_argument(
        "--lag-values",
        nargs="+",
        type=int,
        default=[5, 10],
        help="Lag values to compare in the suite.",
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


def build_experiment_id(feature_profile: str, lags: int) -> str:
    return f"{feature_profile}_lag{lags}"


def save_suite_plot(artifact_path, experiment_frame: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(14, 10))
    labels = experiment_frame["experiment_id"].tolist()
    x_positions = list(range(len(labels)))

    axes[0].bar(
        [position - 0.2 for position in x_positions],
        experiment_frame["mean_walk_forward_baseline_rmse"],
        width=0.4,
        label="Baseline RMSE",
    )
    axes[0].bar(
        [position + 0.2 for position in x_positions],
        experiment_frame["mean_best_learned_rmse"],
        width=0.4,
        label="Best learned RMSE",
    )
    axes[0].set_title("Average walk-forward RMSE by experiment")
    axes[0].set_ylabel("RMSE")
    axes[0].set_xticks(x_positions)
    axes[0].set_xticklabels(labels, rotation=30, ha="right")
    axes[0].grid(True, axis="y")
    axes[0].legend()

    axes[1].bar(
        x_positions,
        experiment_frame["mean_best_learned_minus_baseline_rmse"],
        label="Best learned minus baseline RMSE",
    )
    axes[1].plot(
        x_positions,
        experiment_frame["mean_best_learned_directional_accuracy"] * 100.0,
        color="red",
        marker="o",
        label="Best learned directional accuracy (%)",
    )
    axes[1].axhline(0.0, color="black", linewidth=1)
    axes[1].set_title("RMSE gap and directional accuracy by experiment")
    axes[1].set_ylabel("Gap / Accuracy")
    axes[1].set_xticks(x_positions)
    axes[1].set_xticklabels(labels, rotation=30, ha="right")
    axes[1].grid(True, axis="y")
    axes[1].legend()

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def build_suite_report(
    run_name: str,
    basket_name: str,
    tickers: list[str],
    experiment_frame: pd.DataFrame,
    ticker_best_frame: pd.DataFrame,
    failures: list[dict[str, str]],
) -> str:
    best_overall = experiment_frame.iloc[0]
    lines = [
        f"# Experiment Report: {run_name}",
        "",
        f"Ticker basket: `{basket_name}`",
        "",
        f"Tickers: {', '.join(tickers)}",
        "",
        "## Kurzinterpretation",
        "",
        (
            f"Die aktuell beste Konfiguration in dieser Suite ist "
            f"`{best_overall['experiment_id']}` mit einem mittleren besten gelernten "
            f"Walk-Forward-RMSE von {best_overall['mean_best_learned_rmse']:.4f}."
        ),
        (
            f"Die zugehoerige mittlere Baseline-RMSE liegt bei "
            f"{best_overall['mean_walk_forward_baseline_rmse']:.4f}."
        ),
        (
            "Damit bleibt die naive Persistence-Baseline im Mittel weiterhin leicht staerker, "
            "waehrend die gelernten Modelle vor allem ueber die Richtungsprognose und "
            "tickerabhaengige Staerken relevant werden."
        ),
        "",
        "## Ranking der Experiment-Konfigurationen",
        "",
    ]

    for rank, row in enumerate(experiment_frame.itertuples(index=False), start=1):
        lines.append(
            f"{rank}. `{row.experiment_id}`: bestes gelerntes Mittel-RMSE "
            f"{row.mean_best_learned_rmse:.4f}, Baseline-Mittel-RMSE "
            f"{row.mean_walk_forward_baseline_rmse:.4f}, "
            f"bester Modelltyp im Mittel `{row.dominant_best_model}`"
        )

    lines.extend(["", "## Beste Konfiguration pro Ticker", ""])
    for row in ticker_best_frame.itertuples(index=False):
        lines.append(
            f"- {row.ticker}: `{row.experiment_id}` mit "
            f"{MODEL_DISPLAY_NAMES[row.best_learned_model]} "
            f"(RMSE {row.best_learned_rmse:.4f}, Richtung {row.best_learned_directional_accuracy:.2%})"
        )

    if failures:
        lines.extend(["", "## Fehlgeschlagene Einzelruns", ""])
        for failure in failures:
            lines.append(
                f"- {failure['experiment_id']} / {failure['ticker']}: {failure['error']}"
            )

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    tickers = [ticker.upper() for ticker in (args.tickers or get_ticker_basket(args.basket_preset))]
    run_name = args.run_name or ("experiment_suite_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    artifacts = get_experiment_artifact_paths(run_name)

    ridge_config = build_ridge_config(args)
    decision_tree_config = build_decision_tree_config(args)
    random_forest_config = build_random_forest_config(args)

    experiment_rows: list[dict[str, object]] = []
    ticker_rows: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []

    for feature_profile in args.feature_profiles:
        for lags in args.lag_values:
            experiment_id = build_experiment_id(feature_profile, lags)
            print(f"Running experiment {experiment_id}...")
            local_rows: list[dict[str, object]] = []
            dominant_best_model_counter: Counter[str] = Counter()

            for ticker in tickers:
                print(f"  Ticker {ticker}...")
                try:
                    price_data = download_price_data(
                        ticker=ticker,
                        start_date=args.start_date,
                        end_date=args.end_date or pd.Timestamp.today().date().isoformat(),
                    )
                    dataset = build_next_close_dataset(
                        price_data,
                        lags=lags,
                        feature_profile=feature_profile,
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
                    dominant_best_model_counter[best_learned_model] += 1

                    row: dict[str, object] = {
                        "experiment_id": experiment_id,
                        "feature_profile": feature_profile,
                        "lags": lags,
                        "ticker": ticker,
                        "data_rows": len(price_data),
                        "data_start": price_data.index[0].date().isoformat(),
                        "data_end": price_data.index[-1].date().isoformat(),
                        "best_learned_model": best_learned_model,
                        "best_learned_rmse": walk_forward_summary["overall"][best_learned_model]["rmse"],
                        "best_learned_directional_accuracy": walk_forward_summary["overall"][
                            best_learned_model
                        ]["directional_accuracy"],
                        "best_learned_minus_baseline_rmse": walk_forward_summary["overall"][
                            best_learned_model
                        ]["rmse"]
                        - walk_forward_summary["overall"]["baseline_persistence"]["rmse"],
                        "walk_forward_fold_count": walk_forward_summary["fold_count"],
                    }

                    for model_name in MODEL_ORDER:
                        row[f"holdout_{model_name}_rmse"] = holdout_metrics[model_name]["rmse"]
                        row[f"holdout_{model_name}_directional_accuracy"] = holdout_metrics[
                            model_name
                        ]["directional_accuracy"]
                        row[f"walk_forward_{model_name}_rmse"] = walk_forward_summary[
                            "overall"
                        ][model_name]["rmse"]
                        row[
                            f"walk_forward_{model_name}_directional_accuracy"
                        ] = walk_forward_summary["overall"][model_name]["directional_accuracy"]

                    local_rows.append(row)
                    ticker_rows.append(row)
                except Exception as error:
                    failures.append(
                        {
                            "experiment_id": experiment_id,
                            "ticker": ticker,
                            "error": str(error),
                        }
                    )
                    print(f"    Failed: {error}")

            if not local_rows:
                continue

            local_frame = pd.DataFrame(local_rows)
            dominant_best_model = dominant_best_model_counter.most_common(1)[0][0]
            experiment_rows.append(
                {
                    "experiment_id": experiment_id,
                    "feature_profile": feature_profile,
                    "lags": lags,
                    "ticker_count": len(tickers),
                    "successful_tickers": len(local_frame),
                    "failed_tickers": len(tickers) - len(local_frame),
                    "mean_walk_forward_baseline_rmse": local_frame[
                        "walk_forward_baseline_persistence_rmse"
                    ].mean(),
                    "mean_best_learned_rmse": local_frame["best_learned_rmse"].mean(),
                    "mean_best_learned_directional_accuracy": local_frame[
                        "best_learned_directional_accuracy"
                    ].mean(),
                    "mean_best_learned_minus_baseline_rmse": local_frame[
                        "best_learned_minus_baseline_rmse"
                    ].mean(),
                    "dominant_best_model": dominant_best_model,
                    "ridge_wins": int((local_frame["best_learned_model"] == "ridge_regression").sum()),
                    "decision_tree_wins": int((local_frame["best_learned_model"] == "decision_tree").sum()),
                    "random_forest_wins": int((local_frame["best_learned_model"] == "random_forest").sum()),
                }
            )

    if not experiment_rows:
        raise RuntimeError("No experiment result could be generated.")

    experiment_frame = pd.DataFrame(experiment_rows).sort_values("mean_best_learned_rmse")
    ticker_frame = pd.DataFrame(ticker_rows)
    ticker_best_frame = (
        ticker_frame.sort_values(["ticker", "best_learned_rmse"])
        .groupby("ticker", as_index=False)
        .first()
        .sort_values("best_learned_rmse")
    )

    experiment_frame.to_csv(artifacts.summary_csv, index=False)
    ticker_best_frame.to_csv(artifacts.per_ticker_csv, index=False)
    artifacts.summary_json.write_text(
        json.dumps(
            {
                "run_name": run_name,
                "basket_preset": args.basket_preset,
                "tickers": tickers,
                "feature_profiles": args.feature_profiles,
                "lag_values": args.lag_values,
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
                "summary": experiment_frame.to_dict(orient="records"),
                "ticker_best_configs": ticker_best_frame.to_dict(orient="records"),
                "failures": failures,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    save_suite_plot(artifacts.comparison_plot, experiment_frame)
    artifacts.report.write_text(
        build_suite_report(
            run_name=run_name,
            basket_name=args.basket_preset,
            tickers=tickers,
            experiment_frame=experiment_frame,
            ticker_best_frame=ticker_best_frame,
            failures=failures,
        ),
        encoding="utf-8",
    )

    print(f"Experiment suite run: {run_name}")
    print("Ranking by mean best learned walk-forward RMSE:")
    for row in experiment_frame.itertuples(index=False):
        print(
            f"  {row.experiment_id}: "
            f"mean best RMSE={row.mean_best_learned_rmse:.4f} | "
            f"baseline mean RMSE={row.mean_walk_forward_baseline_rmse:.4f} | "
            f"dominant model={MODEL_DISPLAY_NAMES[row.dominant_best_model]}"
        )
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
