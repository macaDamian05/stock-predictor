from __future__ import annotations

import argparse
import json
from datetime import datetime

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from core.benchmark_presets import TICKER_BASKETS, get_ticker_basket
from core.data_loader import download_price_data
from core.multi_asset import (
    MultiAssetDataset,
    build_expanding_date_splits,
    build_multi_asset_dataset,
    build_multi_asset_latest_feature_frame,
    chronological_train_test_split_by_target_date,
)
from core.paths import ensure_runtime_directories, get_multi_asset_artifact_paths
from core.predictor import (
    average_daily_slope,
    average_distance_pct_to_reference,
    average_distance_to_reference,
    build_forecast_index,
)
from core.tabular_features import DEFAULT_FEATURE_PROFILE, FEATURE_PROFILES
from run_classical_pipeline import (
    MODEL_DISPLAY_NAMES,
    MODEL_ORDER,
    build_decision_tree_config,
    build_random_forest_config,
    build_ridge_config,
    calculate_metrics_from_predictions,
    evaluate_models,
    format_metrics_line,
    select_best_model_from_metric_source,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train one shared classical model stack across multiple assets."
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Optional explicit ticker list. When empty, the selected basket preset is used.",
    )
    parser.add_argument(
        "--basket-preset",
        default="starter",
        choices=list(TICKER_BASKETS),
        help="Named ticker basket for pooled multi-asset training.",
    )
    parser.add_argument("--start-date", default="1990-01-01", help="Historical download start date.")
    parser.add_argument("--end-date", default=None, help="Historical download end date.")
    parser.add_argument("--lags", type=int, default=10, help="Number of lagged return features.")
    parser.add_argument(
        "--feature-profile",
        default=DEFAULT_FEATURE_PROFILE,
        choices=list(FEATURE_PROFILES),
        help="Feature profile shared across all assets.",
    )
    parser.add_argument(
        "--forecast-days",
        type=int,
        default=5,
        help="Number of future business days to forecast for each asset.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of target dates reserved for pooled holdout evaluation.",
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
        help="Initial training fraction for walk-forward evaluation over shared target dates.",
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


def evaluate_multi_asset_models(
    train_frame: pd.DataFrame,
    evaluation_frame: pd.DataFrame,
    dataset: MultiAssetDataset,
    ridge_config,
    decision_tree_config,
    random_forest_config,
    evaluation_name: str,
    fold_index: int | None = None,
):
    predictions_frame, metrics, models = evaluate_models(
        train_frame=train_frame,
        evaluation_frame=evaluation_frame,
        dataset=dataset,
        ridge_config=ridge_config,
        decision_tree_config=decision_tree_config,
        random_forest_config=random_forest_config,
        evaluation_name=evaluation_name,
        fold_index=fold_index,
    )
    predictions_frame.insert(2, dataset.ticker_column, evaluation_frame[dataset.ticker_column].to_numpy())
    return predictions_frame, metrics, models


def run_multi_asset_walk_forward_evaluation(
    supervised_frame: pd.DataFrame,
    dataset: MultiAssetDataset,
    ridge_config,
    decision_tree_config,
    random_forest_config,
    initial_train_size: float,
    folds: int,
):
    splits = build_expanding_date_splits(
        frame=supervised_frame,
        target_date_column=dataset.target_date_column,
        initial_train_size=initial_train_size,
        folds=folds,
    )
    if not splits:
        return None, None

    prediction_frames: list[pd.DataFrame] = []
    fold_summaries: list[dict[str, object]] = []

    for fold_index, train_frame, test_frame in splits:
        fold_predictions, fold_metrics, _ = evaluate_multi_asset_models(
            train_frame=train_frame,
            evaluation_frame=test_frame,
            dataset=dataset,
            ridge_config=ridge_config,
            decision_tree_config=decision_tree_config,
            random_forest_config=random_forest_config,
            evaluation_name="walk_forward",
            fold_index=fold_index,
        )
        prediction_frames.append(fold_predictions)

        fold_summary: dict[str, object] = {
            "fold": fold_index,
            "train_rows": len(train_frame),
            "test_rows": len(test_frame),
            "train_tickers": sorted(train_frame[dataset.ticker_column].unique().tolist()),
            "test_tickers": sorted(test_frame[dataset.ticker_column].unique().tolist()),
            "train_start": pd.Timestamp(train_frame[dataset.target_date_column].min()).date().isoformat(),
            "train_end": pd.Timestamp(train_frame[dataset.target_date_column].max()).date().isoformat(),
            "test_start": pd.Timestamp(test_frame[dataset.target_date_column].min()).date().isoformat(),
            "test_end": pd.Timestamp(test_frame[dataset.target_date_column].max()).date().isoformat(),
        }
        for model_name in MODEL_ORDER:
            fold_summary[model_name] = fold_metrics[model_name]
        fold_summary["best_learned_model"] = select_best_model_from_metric_source(fold_metrics)
        fold_summaries.append(fold_summary)

    walk_forward_predictions = (
        pd.concat(prediction_frames, ignore_index=True)
        .sort_values(["target_date", dataset.ticker_column])
        .reset_index(drop=True)
    )
    overall_metrics = calculate_metrics_from_predictions(walk_forward_predictions)
    walk_forward_summary = {
        "fold_count": len(fold_summaries),
        "initial_train_size": initial_train_size,
        "total_rows": len(supervised_frame),
        "total_predictions": len(walk_forward_predictions),
        "overall": overall_metrics,
        "best_learned_model": select_best_model_from_metric_source(overall_metrics),
        "folds": fold_summaries,
    }
    return walk_forward_predictions, walk_forward_summary


def build_per_ticker_metrics_frame(
    dataset: MultiAssetDataset,
    holdout_predictions: pd.DataFrame,
    walk_forward_predictions: pd.DataFrame | None,
    shared_model_name: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for ticker in dataset.tickers:
        holdout_slice = holdout_predictions.loc[holdout_predictions[dataset.ticker_column] == ticker].copy()
        walk_forward_slice = (
            walk_forward_predictions.loc[walk_forward_predictions[dataset.ticker_column] == ticker].copy()
            if walk_forward_predictions is not None
            else None
        )
        holdout_metrics = calculate_metrics_from_predictions(holdout_slice)
        metric_source = holdout_metrics
        walk_forward_metrics = None
        if walk_forward_slice is not None and not walk_forward_slice.empty:
            walk_forward_metrics = calculate_metrics_from_predictions(walk_forward_slice)
            metric_source = walk_forward_metrics

        best_learned_model = select_best_model_from_metric_source(metric_source)
        row: dict[str, object] = {
            "ticker": ticker,
            "holdout_rows": len(holdout_slice),
            "walk_forward_rows": 0 if walk_forward_slice is None else len(walk_forward_slice),
            "shared_model_name": shared_model_name,
            "shared_model_label": MODEL_DISPLAY_NAMES[shared_model_name],
            "shared_model_rmse": metric_source[shared_model_name]["rmse"],
            "shared_model_directional_accuracy": metric_source[shared_model_name]["directional_accuracy"],
            "best_learned_model": best_learned_model,
            "best_learned_model_label": MODEL_DISPLAY_NAMES[best_learned_model],
            "best_learned_rmse": metric_source[best_learned_model]["rmse"],
            "best_learned_directional_accuracy": metric_source[best_learned_model]["directional_accuracy"],
            "shared_model_minus_baseline_rmse": metric_source[shared_model_name]["rmse"]
            - metric_source["baseline_persistence"]["rmse"],
            "best_learned_minus_baseline_rmse": metric_source[best_learned_model]["rmse"]
            - metric_source["baseline_persistence"]["rmse"],
        }

        for model_name in MODEL_ORDER:
            row[f"holdout_{model_name}_rmse"] = holdout_metrics[model_name]["rmse"]
            row[f"holdout_{model_name}_directional_accuracy"] = holdout_metrics[model_name][
                "directional_accuracy"
            ]
            if walk_forward_metrics is None:
                row[f"walk_forward_{model_name}_rmse"] = None
                row[f"walk_forward_{model_name}_directional_accuracy"] = None
            else:
                row[f"walk_forward_{model_name}_rmse"] = walk_forward_metrics[model_name]["rmse"]
                row[f"walk_forward_{model_name}_directional_accuracy"] = walk_forward_metrics[
                    model_name
                ]["directional_accuracy"]

        rows.append(row)

    return pd.DataFrame(rows).sort_values("shared_model_rmse")


def recursive_multi_asset_forecast(
    model,
    dataset: MultiAssetDataset,
    ticker: str,
    close_history: pd.Series,
    lags: int,
    forecast_days: int,
) -> tuple[pd.DatetimeIndex, list[float], list[float]]:
    forecast_dates = build_forecast_index(close_history.index[-1], forecast_days)
    rolling_close_history = close_history.astype(float).copy()
    predicted_returns: list[float] = []
    predicted_prices: list[float] = []

    for forecast_date in forecast_dates:
        latest_features, base_feature_columns, identity_feature_columns = (
            build_multi_asset_latest_feature_frame(
                close_series=rolling_close_history,
                ticker=ticker,
                tickers=dataset.tickers,
                lags=lags,
                feature_profile=dataset.feature_profile,
            )
        )
        expected_feature_columns = [*base_feature_columns, *identity_feature_columns]
        if expected_feature_columns != dataset.feature_columns:
            raise ValueError("Forecast feature columns do not match the pooled training feature columns.")

        feature_row = latest_features[dataset.feature_columns]
        next_return = float(model.predict(feature_row)[0])
        current_close = float(rolling_close_history.iloc[-1])
        next_close = current_close * (1.0 + next_return)

        predicted_returns.append(next_return)
        predicted_prices.append(next_close)
        rolling_close_history.loc[forecast_date] = next_close

    return forecast_dates, predicted_returns, predicted_prices


def build_forecast_summary_frame(
    dataset: MultiAssetDataset,
    price_data_by_ticker: dict[str, pd.DataFrame],
    shared_model,
    shared_model_name: str,
    lags: int,
    forecast_days: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for ticker in dataset.tickers:
        close_series = price_data_by_ticker[ticker]["Close"].astype(float)
        forecast_dates, predicted_returns, predicted_prices = recursive_multi_asset_forecast(
            model=shared_model,
            dataset=dataset,
            ticker=ticker,
            close_history=close_series,
            lags=lags,
            forecast_days=forecast_days,
        )
        last_close = float(close_series.iloc[-1])
        next_close = float(predicted_prices[0])
        final_close = float(predicted_prices[-1])

        rows.append(
            {
                "ticker": ticker,
                "forecast_model": shared_model_name,
                "forecast_model_label": MODEL_DISPLAY_NAMES[shared_model_name],
                "last_close_date": close_series.index[-1].date().isoformat(),
                "last_close": last_close,
                "next_forecast_date": forecast_dates[0].date().isoformat(),
                "next_predicted_close": next_close,
                "next_predicted_change_pct": ((next_close / last_close) - 1.0) * 100.0,
                "forecast_end_date": forecast_dates[-1].date().isoformat(),
                "forecast_end_close": final_close,
                "forecast_horizon_change_pct": ((final_close / last_close) - 1.0) * 100.0,
                "forecast_days": forecast_days,
                "average_forecast_slope": average_daily_slope(predicted_prices),
                "average_forecast_distance_to_last_close": average_distance_to_reference(
                    predicted_prices,
                    reference_value=last_close,
                ),
                "average_forecast_distance_pct_to_last_close": average_distance_pct_to_reference(
                    predicted_prices,
                    reference_value=last_close,
                ),
                "forecast_path": json.dumps(
                    [
                        {
                            "date": forecast_date.date().isoformat(),
                            "predicted_return": predicted_return,
                            "predicted_close": predicted_close,
                        }
                        for forecast_date, predicted_return, predicted_close in zip(
                            forecast_dates,
                            predicted_returns,
                            predicted_prices,
                        )
                    ]
                ),
            }
        )

    return pd.DataFrame(rows).sort_values("forecast_horizon_change_pct", ascending=False)


def save_per_ticker_plot(artifact_path, per_ticker_frame: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(13, 6))
    labels = per_ticker_frame["ticker"].tolist()
    x_positions = list(range(len(labels)))

    axis.bar(
        [position - 0.2 for position in x_positions],
        per_ticker_frame["walk_forward_baseline_persistence_rmse"].fillna(
            per_ticker_frame["holdout_baseline_persistence_rmse"]
        ),
        width=0.4,
        label="Baseline RMSE",
    )
    axis.bar(
        [position + 0.2 for position in x_positions],
        per_ticker_frame["shared_model_rmse"],
        width=0.4,
        label="Shared model RMSE",
    )
    axis.set_title("Per-ticker baseline vs. shared pooled model RMSE")
    axis.set_ylabel("RMSE")
    axis.set_xticks(x_positions)
    axis.set_xticklabels(labels, rotation=30, ha="right")
    axis.grid(True, axis="y")
    axis.legend()

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def build_report(
    run_name: str,
    basket_name: str,
    tickers: list[str],
    pooled_summary: dict[str, object],
    per_ticker_frame: pd.DataFrame,
    forecast_frame: pd.DataFrame,
) -> str:
    lines = [
        f"# Multi-Asset Report: {run_name}",
        "",
        f"Ticker basket: `{basket_name}`",
        "",
        f"Tickers: {', '.join(tickers)}",
        "",
        "## Kurzinterpretation",
        "",
        (
            "Dieser Lauf trainiert ein gemeinsames Modell ueber alle angegebenen Assets, "
            "statt pro Ticker getrennte Modelle zu fitten."
        ),
        (
            f"Das global beste gelernte Modell ist `{pooled_summary['shared_model_name']}` "
            f"mit einer gepoolten Walk-Forward-RMSE von {pooled_summary['shared_model_rmse']:.4f}."
        ),
        (
            f"Die gepoolte Baseline-RMSE liegt bei "
            f"{pooled_summary['baseline_rmse']:.4f}."
        ),
        "",
        "## Per-Ticker-Ranking nach gemeinsamem Modell",
        "",
    ]

    for rank, row in enumerate(per_ticker_frame.itertuples(index=False), start=1):
        baseline_rmse = (
            row.walk_forward_baseline_persistence_rmse
            if pd.notna(row.walk_forward_baseline_persistence_rmse)
            else row.holdout_baseline_persistence_rmse
        )
        lines.append(
            f"{rank}. {row.ticker}: shared RMSE {row.shared_model_rmse:.4f}, "
            f"Baseline {baseline_rmse:.4f}, "
            f"bestes lokales gelerntes Modell in der Auswertung "
            f"{row.best_learned_model_label}"
        )

    lines.extend(["", "## Forecast-Ranking des gemeinsamen Modells", ""])
    for rank, row in enumerate(forecast_frame.itertuples(index=False), start=1):
        lines.append(
            f"{rank}. {row.ticker}: 5-Tage-Aenderung {row.forecast_horizon_change_pct:+.2f}%, "
            f"mittlerer Abstand zum letzten Schlusskurs "
            f"{row.average_forecast_distance_pct_to_last_close:.2f}%"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    tickers = [ticker.upper() for ticker in (args.tickers or get_ticker_basket(args.basket_preset))]
    basket_name = args.basket_preset if not args.tickers else "custom"
    run_name = args.run_name or ("multi_asset_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    artifacts = get_multi_asset_artifact_paths(run_name)

    price_data_by_ticker: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        print(f"Loading market data for {ticker}...")
        price_data_by_ticker[ticker] = download_price_data(
            ticker=ticker,
            start_date=args.start_date,
            end_date=args.end_date or pd.Timestamp.today().date().isoformat(),
        )

    dataset = build_multi_asset_dataset(
        price_data_by_ticker=price_data_by_ticker,
        lags=args.lags,
        feature_profile=args.feature_profile,
    )

    train_frame, test_frame = chronological_train_test_split_by_target_date(
        frame=dataset.supervised_frame,
        target_date_column=dataset.target_date_column,
        test_size=args.test_size,
    )

    ridge_config = build_ridge_config(args)
    decision_tree_config = build_decision_tree_config(args)
    random_forest_config = build_random_forest_config(args)

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
    shared_model = trained_models[shared_model_name]

    per_ticker_frame = build_per_ticker_metrics_frame(
        dataset=dataset,
        holdout_predictions=holdout_predictions,
        walk_forward_predictions=walk_forward_predictions,
        shared_model_name=shared_model_name,
    )
    forecast_frame = build_forecast_summary_frame(
        dataset=dataset,
        price_data_by_ticker=price_data_by_ticker,
        shared_model=shared_model,
        shared_model_name=shared_model_name,
        lags=args.lags,
        forecast_days=args.forecast_days,
    )

    summary_row = {
        "run_name": run_name,
        "basket_preset": args.basket_preset,
        "basket_name": basket_name,
        "ticker_count": len(tickers),
        "tickers": ",".join(tickers),
        "feature_profile": args.feature_profile,
        "lags": args.lags,
        "train_rows": len(train_frame),
        "holdout_rows": len(test_frame),
        "holdout_best_learned_model": select_best_model_from_metric_source(holdout_metrics),
        "shared_model_name": shared_model_name,
        "shared_model_label": MODEL_DISPLAY_NAMES[shared_model_name],
        "shared_model_rmse": shared_metric_source[shared_model_name]["rmse"],
        "shared_model_directional_accuracy": shared_metric_source[shared_model_name][
            "directional_accuracy"
        ],
        "baseline_rmse": shared_metric_source["baseline_persistence"]["rmse"],
        "shared_model_minus_baseline_rmse": shared_metric_source[shared_model_name]["rmse"]
        - shared_metric_source["baseline_persistence"]["rmse"],
        "walk_forward_enabled": walk_forward_summary is not None,
        "walk_forward_fold_count": 0 if walk_forward_summary is None else walk_forward_summary["fold_count"],
        "pooled_unique_target_dates": dataset.supervised_frame[dataset.target_date_column].nunique(),
    }
    summary_frame = pd.DataFrame([summary_row])

    summary_payload = {
        "run_name": run_name,
        "training_mode": "pooled_multi_asset_classical",
        "basket_preset": args.basket_preset,
        "basket_name": basket_name,
        "tickers": tickers,
        "feature_profile": args.feature_profile,
        "lags": args.lags,
        "feature_columns": dataset.feature_columns,
        "base_feature_columns": dataset.base_feature_columns,
        "identity_feature_columns": dataset.identity_feature_columns,
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
        "holdout": {
            "train_rows": len(train_frame),
            "test_rows": len(test_frame),
            "test_target_date_start": pd.Timestamp(test_frame[dataset.target_date_column].min())
            .date()
            .isoformat(),
            "test_target_date_end": pd.Timestamp(test_frame[dataset.target_date_column].max())
            .date()
            .isoformat(),
            "overall_metrics": holdout_metrics,
            "best_learned_model": select_best_model_from_metric_source(holdout_metrics),
        },
        "walk_forward": walk_forward_summary,
        "shared_model_name": shared_model_name,
        "shared_model_label": MODEL_DISPLAY_NAMES[shared_model_name],
        "per_ticker_metrics": per_ticker_frame.to_dict(orient="records"),
        "forecast_summary": forecast_frame.drop(columns=["forecast_path"]).to_dict(orient="records"),
    }

    summary_frame.to_csv(artifacts.summary_csv, index=False)
    per_ticker_frame.to_csv(artifacts.per_ticker_metrics_csv, index=False)
    forecast_frame.to_csv(artifacts.forecast_csv, index=False)
    holdout_predictions.to_csv(artifacts.holdout_predictions_csv, index=False)
    joblib.dump(trained_models, artifacts.model)
    if walk_forward_predictions is not None:
        walk_forward_predictions.to_csv(artifacts.walk_forward_predictions_csv, index=False)

    artifacts.summary_json.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    save_per_ticker_plot(artifacts.comparison_plot, per_ticker_frame)
    artifacts.report.write_text(
        build_report(
            run_name=run_name,
            basket_name=basket_name,
            tickers=tickers,
            pooled_summary=summary_row,
            per_ticker_frame=per_ticker_frame,
            forecast_frame=forecast_frame,
        ),
        encoding="utf-8",
    )

    print(f"Multi-asset run: {run_name}")
    print(f"Shared best learned model: {MODEL_DISPLAY_NAMES[shared_model_name]}")
    print("Pooled holdout metrics:")
    for model_name in MODEL_ORDER:
        print(format_metrics_line(model_name, holdout_metrics[model_name]))

    if walk_forward_summary is None:
        print("Walk-forward: disabled")
    else:
        print(
            "Pooled walk-forward overall: "
            f"{walk_forward_summary['fold_count']} folds | "
            f"{walk_forward_summary['total_predictions']} predictions"
        )
        for model_name in MODEL_ORDER:
            print(format_metrics_line(model_name, walk_forward_summary["overall"][model_name]))

    print("Per-ticker ranking by shared model RMSE:")
    for row in per_ticker_frame.itertuples(index=False):
        print(
            f"  {row.ticker}: shared RMSE={row.shared_model_rmse:.4f} | "
            f"best local learned={row.best_learned_model_label} ({row.best_learned_rmse:.4f})"
        )

    print("Forecast ranking:")
    for row in forecast_frame.itertuples(index=False):
        print(
            f"  {row.ticker}: 5T={row.forecast_horizon_change_pct:+.2f}% | "
            f"avg distance={row.average_forecast_distance_pct_to_last_close:.2f}%"
        )
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
