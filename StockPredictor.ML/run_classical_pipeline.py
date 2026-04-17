from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from core.classical_models import (
    PersistenceRegressor,
    RandomForestConfig,
    build_random_forest_regressor,
)
from core.data_loader import download_price_data, load_price_data_from_csv
from core.indicators import average_recent_rsi, calculate_rsi
from core.paths import ensure_runtime_directories, get_classical_artifact_paths
from core.predictor import (
    average_daily_slope,
    build_forecast_index,
    one_step_directional_accuracy,
    regression_metrics,
)
from core.tabular_features import build_next_close_dataset, chronological_train_test_split


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a baseline and Random Forest time-series pipeline for stock forecasting."
    )
    parser.add_argument("ticker", nargs="?", help="Ticker symbol, for example AAPL or ENR.DE.")
    parser.add_argument("--csv-path", help="Optional CSV path instead of downloading market data.")
    parser.add_argument("--date-column", default="Date", help="Date column name for CSV input.")
    parser.add_argument("--close-column", default="Close", help="Close price column name for CSV input.")
    parser.add_argument("--source-name", default=None, help="Artifact name override for CSV runs.")
    parser.add_argument("--start-date", default="1990-01-01", help="Historical download start date.")
    parser.add_argument("--end-date", default=None, help="Historical download end date.")
    parser.add_argument("--lags", type=int, default=10, help="Number of lagged close prices to use.")
    parser.add_argument("--forecast-days", type=int, default=5, help="Number of future business days to forecast.")
    parser.add_argument(
        "--display-days",
        type=int,
        default=200,
        help="How many recent trading days to show in saved plots.",
    )
    parser.add_argument("--rsi-window", type=int, default=14, help="Rolling window for RSI.")
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of chronological samples reserved for testing.",
    )
    parser.add_argument(
        "--walk-forward-folds",
        type=int,
        default=5,
        help="Number of expanding walk-forward folds. Use 0 to disable.",
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
        "--show-plot",
        action="store_true",
        help="Open the saved test prediction plot after writing it to disk.",
    )
    return parser.parse_args()


def resolve_data_source(args: argparse.Namespace) -> tuple[pd.DataFrame, str]:
    if args.csv_path:
        frame = load_price_data_from_csv(
            csv_path=args.csv_path,
            date_column=args.date_column,
            close_column=args.close_column,
        )
        source_name = args.source_name or Path(args.csv_path).stem
        return frame, source_name

    ticker = (args.ticker or input("Please enter a ticker symbol: ")).strip().upper()
    if not ticker:
        raise ValueError("A ticker symbol or --csv-path is required.")

    frame = download_price_data(
        ticker=ticker,
        start_date=args.start_date,
        end_date=args.end_date or pd.Timestamp.today().date().isoformat(),
    )
    return frame, ticker


def save_prediction_plot(artifact_path: Path, prediction_frame: pd.DataFrame, title: str) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(
        prediction_frame["target_date"],
        prediction_frame["actual_next_close"],
        label="Actual next close",
        linewidth=2,
    )
    plt.plot(
        prediction_frame["target_date"],
        prediction_frame["baseline_prediction"],
        label="Persistence baseline",
        linestyle="--",
    )
    plt.plot(
        prediction_frame["target_date"],
        prediction_frame["random_forest_prediction"],
        label="Random Forest",
        linestyle="-.",
    )
    plt.title(title)
    plt.xlabel("Target date")
    plt.ylabel("Close price")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(artifact_path, dpi=150)
    plt.close()


def save_history_plot(artifact_path: Path, close_series: pd.Series, display_days: int) -> None:
    history = close_series.tail(display_days)

    plt.figure(figsize=(12, 6))
    plt.plot(history.index, history.values, label="Close price", linewidth=2)
    plt.title("Recent close price history")
    plt.xlabel("Date")
    plt.ylabel("Close price")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(artifact_path, dpi=150)
    plt.close()


def save_forecast_plot(
    artifact_path: Path,
    close_series: pd.Series,
    future_dates: pd.DatetimeIndex,
    future_prices: list[float],
    display_days: int,
) -> None:
    history = close_series.tail(display_days)

    plt.figure(figsize=(12, 6))
    plt.plot(history.index, history.values, label="Recent close prices", linewidth=2)
    plt.plot(
        future_dates,
        future_prices,
        label="Random Forest forecast",
        marker="o",
        linestyle="--",
        color="red",
    )
    plt.title("Recent prices and future forecast")
    plt.xlabel("Date")
    plt.ylabel("Close price")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(artifact_path, dpi=150)
    plt.close()


def build_random_forest_config(args: argparse.Namespace) -> RandomForestConfig:
    return RandomForestConfig(
        n_estimators=args.n_estimators,
        max_depth=None if args.max_depth == 0 else args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.random_state,
    )


def fit_models(train_frame: pd.DataFrame, dataset, random_forest_config: RandomForestConfig):
    X_train = train_frame[dataset.feature_columns]
    y_train = train_frame[dataset.target_column].to_numpy(dtype=float)

    baseline_model = PersistenceRegressor(reference_column=dataset.reference_column)
    baseline_model.fit(X_train, y_train)

    random_forest_model = build_random_forest_regressor(random_forest_config)
    random_forest_model.fit(X_train, y_train)
    return baseline_model, random_forest_model


def build_predictions_frame(
    evaluation_frame: pd.DataFrame,
    dataset,
    baseline_predictions,
    random_forest_return_predictions,
    random_forest_predictions,
    evaluation_name: str,
    fold_index: int | None = None,
) -> pd.DataFrame:
    X_eval = evaluation_frame[dataset.feature_columns]
    predictions_frame = pd.DataFrame(
        {
            "evaluation": evaluation_name,
            "feature_date": evaluation_frame.index,
            "target_date": evaluation_frame[dataset.target_date_column].to_numpy(),
            "close_current": X_eval[dataset.reference_column].to_numpy(dtype=float),
            "actual_next_close": evaluation_frame[dataset.close_target_column].to_numpy(dtype=float),
            "actual_next_return": evaluation_frame[dataset.target_column].to_numpy(dtype=float),
            "baseline_prediction": baseline_predictions,
            "random_forest_predicted_return": random_forest_return_predictions,
            "random_forest_prediction": random_forest_predictions,
        }
    )

    if fold_index is not None:
        predictions_frame.insert(1, "fold", fold_index)

    return predictions_frame


def calculate_metrics_from_predictions(prediction_frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    actual_values = prediction_frame["actual_next_close"].to_numpy(dtype=float)
    reference_values = prediction_frame["close_current"].to_numpy(dtype=float)
    baseline_predictions = prediction_frame["baseline_prediction"].to_numpy(dtype=float)
    random_forest_predictions = prediction_frame["random_forest_prediction"].to_numpy(dtype=float)

    baseline_metrics = regression_metrics(actual_values, baseline_predictions)
    baseline_metrics["directional_accuracy"] = one_step_directional_accuracy(
        reference_values=reference_values,
        actual_values=actual_values,
        predicted_values=baseline_predictions,
    )

    random_forest_metrics = regression_metrics(actual_values, random_forest_predictions)
    random_forest_metrics["directional_accuracy"] = one_step_directional_accuracy(
        reference_values=reference_values,
        actual_values=actual_values,
        predicted_values=random_forest_predictions,
    )

    return {
        "baseline_persistence": baseline_metrics,
        "random_forest": random_forest_metrics,
    }


def evaluate_models(
    train_frame: pd.DataFrame,
    evaluation_frame: pd.DataFrame,
    dataset,
    random_forest_config: RandomForestConfig,
    evaluation_name: str,
    fold_index: int | None = None,
):
    baseline_model, random_forest_model = fit_models(
        train_frame=train_frame,
        dataset=dataset,
        random_forest_config=random_forest_config,
    )

    X_eval = evaluation_frame[dataset.feature_columns]
    baseline_predictions = baseline_model.predict(X_eval)
    random_forest_return_predictions = random_forest_model.predict(X_eval)
    random_forest_predictions = X_eval[dataset.reference_column].to_numpy(dtype=float) * (
        1.0 + random_forest_return_predictions
    )

    predictions_frame = build_predictions_frame(
        evaluation_frame=evaluation_frame,
        dataset=dataset,
        baseline_predictions=baseline_predictions,
        random_forest_return_predictions=random_forest_return_predictions,
        random_forest_predictions=random_forest_predictions,
        evaluation_name=evaluation_name,
        fold_index=fold_index,
    )
    metrics = calculate_metrics_from_predictions(predictions_frame)
    return predictions_frame, metrics, baseline_model, random_forest_model


def build_walk_forward_splits(
    supervised_frame: pd.DataFrame,
    initial_train_size: float,
    folds: int,
) -> list[tuple[int, pd.DataFrame, pd.DataFrame]]:
    if folds < 0:
        raise ValueError(f"walk_forward_folds must be non-negative, got {folds}.")
    if folds == 0:
        return []
    if not 0 < initial_train_size < 1:
        raise ValueError(
            "walk_forward_train_size must be between 0 and 1, "
            f"got {initial_train_size}."
        )

    total_rows = len(supervised_frame)
    initial_train_rows = max(1, math.ceil(total_rows * initial_train_size))
    remaining_rows = total_rows - initial_train_rows

    if remaining_rows < folds:
        raise ValueError(
            "Walk-forward split leaves too few rows for the requested number of folds. "
            f"total_rows={total_rows}, initial_train_rows={initial_train_rows}, folds={folds}."
        )

    base_test_rows = remaining_rows // folds
    extra_rows = remaining_rows % folds
    splits: list[tuple[int, pd.DataFrame, pd.DataFrame]] = []
    test_start = initial_train_rows

    for fold_index in range(1, folds + 1):
        test_rows = base_test_rows + (1 if fold_index <= extra_rows else 0)
        test_end = test_start + test_rows

        train_frame = supervised_frame.iloc[:test_start].copy()
        test_frame = supervised_frame.iloc[test_start:test_end].copy()
        splits.append((fold_index, train_frame, test_frame))
        test_start = test_end

    return splits


def average_metric_sections(metric_sections: list[dict[str, float]]) -> dict[str, float]:
    if not metric_sections:
        return {}

    keys = metric_sections[0].keys()
    return {
        key: float(sum(section[key] for section in metric_sections) / len(metric_sections))
        for key in keys
    }


def run_walk_forward_evaluation(
    supervised_frame: pd.DataFrame,
    dataset,
    random_forest_config: RandomForestConfig,
    initial_train_size: float,
    folds: int,
):
    splits = build_walk_forward_splits(
        supervised_frame=supervised_frame,
        initial_train_size=initial_train_size,
        folds=folds,
    )
    if not splits:
        return None, None

    prediction_frames: list[pd.DataFrame] = []
    fold_summaries: list[dict[str, object]] = []

    for fold_index, train_frame, test_frame in splits:
        fold_predictions, fold_metrics, _, _ = evaluate_models(
            train_frame=train_frame,
            evaluation_frame=test_frame,
            dataset=dataset,
            random_forest_config=random_forest_config,
            evaluation_name="walk_forward",
            fold_index=fold_index,
        )
        prediction_frames.append(fold_predictions)
        fold_summaries.append(
            {
                "fold": fold_index,
                "train_rows": len(train_frame),
                "test_rows": len(test_frame),
                "train_start": train_frame.index[0].date().isoformat(),
                "train_end": train_frame.index[-1].date().isoformat(),
                "test_start": pd.Timestamp(test_frame[dataset.target_date_column].iloc[0])
                .date()
                .isoformat(),
                "test_end": pd.Timestamp(test_frame[dataset.target_date_column].iloc[-1])
                .date()
                .isoformat(),
                "baseline_persistence": fold_metrics["baseline_persistence"],
                "random_forest": fold_metrics["random_forest"],
            }
        )

    walk_forward_predictions = (
        pd.concat(prediction_frames, ignore_index=True)
        .sort_values("target_date")
        .reset_index(drop=True)
    )
    overall_metrics = calculate_metrics_from_predictions(walk_forward_predictions)
    mean_across_folds = {
        "baseline_persistence": average_metric_sections(
            [fold["baseline_persistence"] for fold in fold_summaries]
        ),
        "random_forest": average_metric_sections(
            [fold["random_forest"] for fold in fold_summaries]
        ),
    }
    walk_forward_summary = {
        "fold_count": len(fold_summaries),
        "initial_train_size": initial_train_size,
        "total_rows": len(supervised_frame),
        "total_predictions": len(walk_forward_predictions),
        "overall": overall_metrics,
        "mean_across_folds": mean_across_folds,
        "folds": fold_summaries,
    }
    return walk_forward_predictions, walk_forward_summary


def recursive_forecast(
    model,
    latest_features: pd.DataFrame,
    feature_columns: list[str],
    reference_column: str,
    forecast_days: int,
) -> tuple[list[float], list[float]]:
    state = latest_features[feature_columns].iloc[0].to_dict()
    predicted_returns: list[float] = []
    predicted_prices: list[float] = []

    lag_columns = [column for column in feature_columns if column != reference_column]
    current_close = float(state[reference_column])

    for _ in range(forecast_days):
        feature_row = pd.DataFrame([{column: state[column] for column in feature_columns}])
        next_return = float(model.predict(feature_row)[0])
        next_close = current_close * (1.0 + next_return)

        predicted_returns.append(next_return)
        predicted_prices.append(next_close)

        previous_returns = [state[column] for column in lag_columns]
        shifted_returns = [next_return, *previous_returns[:-1]] if previous_returns else []

        current_close = next_close
        state[reference_column] = current_close
        for column, value in zip(lag_columns, shifted_returns):
            state[column] = value

    return predicted_returns, predicted_prices


def show_plots(
    close_series: pd.Series,
    display_days: int,
    test_frame: pd.DataFrame,
    baseline_predictions,
    random_forest_predictions,
    future_dates: pd.DatetimeIndex,
    future_prices: list[float],
) -> None:
    history = close_series.tail(display_days)

    plt.figure(figsize=(12, 6))
    plt.plot(history.index, history.values, label="Close price", linewidth=2)
    plt.title("Recent close price history")
    plt.xlabel("Date")
    plt.ylabel("Close price")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.figure(figsize=(12, 6))
    plt.plot(
        test_frame["target_date"],
        test_frame["target_close_next"],
        label="Actual next close",
        linewidth=2,
    )
    plt.plot(
        test_frame["target_date"],
        baseline_predictions,
        label="Persistence baseline",
        linestyle="--",
    )
    plt.plot(
        test_frame["target_date"],
        random_forest_predictions,
        label="Random Forest",
        linestyle="-.",
    )
    plt.title("Chronological test predictions")
    plt.xlabel("Target date")
    plt.ylabel("Close price")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.figure(figsize=(12, 6))
    plt.plot(history.index, history.values, label="Recent close prices", linewidth=2)
    plt.plot(
        future_dates,
        future_prices,
        label="Random Forest forecast",
        marker="o",
        linestyle="--",
        color="red",
    )
    plt.title("Recent prices and future forecast")
    plt.xlabel("Date")
    plt.ylabel("Close price")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    price_data, source_name = resolve_data_source(args)
    dataset = build_next_close_dataset(price_data, lags=args.lags)
    train_frame, test_frame = chronological_train_test_split(
        dataset.supervised_frame,
        test_size=args.test_size,
    )

    random_forest_config = build_random_forest_config(args)
    predictions_frame, holdout_metrics, baseline_model, random_forest_model = evaluate_models(
        train_frame=train_frame,
        evaluation_frame=test_frame,
        dataset=dataset,
        random_forest_config=random_forest_config,
        evaluation_name="holdout",
    )

    walk_forward_predictions, walk_forward_summary = run_walk_forward_evaluation(
        supervised_frame=dataset.supervised_frame,
        dataset=dataset,
        random_forest_config=random_forest_config,
        initial_train_size=args.walk_forward_train_size,
        folds=args.walk_forward_folds,
    )

    latest_features = dataset.latest_features[dataset.feature_columns]
    future_dates = build_forecast_index(price_data.index[-1], args.forecast_days)
    future_return_predictions, future_price_predictions = recursive_forecast(
        model=random_forest_model,
        latest_features=latest_features,
        feature_columns=dataset.feature_columns,
        reference_column=dataset.reference_column,
        forecast_days=args.forecast_days,
    )
    next_return_prediction = future_return_predictions[0]
    next_business_day = future_dates[0]

    rsi_values = calculate_rsi(price_data["Close"].astype(float), args.rsi_window)
    average_rsi = average_recent_rsi(rsi_values, args.forecast_days)
    forecast_slope = average_daily_slope(pd.Series(future_price_predictions, dtype=float).to_numpy())

    next_forecast = {
        "forecast_date": next_business_day.date().isoformat(),
        "last_close_date": price_data.index[-1].date().isoformat(),
        "last_close": float(price_data["Close"].iloc[-1]),
        "baseline_prediction": float(baseline_model.predict(latest_features)[0]),
        "random_forest_predicted_return": next_return_prediction,
        "random_forest_prediction": future_price_predictions[0],
        "forecast_days": args.forecast_days,
        "forecast_path": [
            {
                "date": forecast_date.date().isoformat(),
                "predicted_return": predicted_return,
                "predicted_close": predicted_close,
            }
            for forecast_date, predicted_return, predicted_close in zip(
                future_dates,
                future_return_predictions,
                future_price_predictions,
            )
        ],
    }

    artifacts = get_classical_artifact_paths(source_name)
    joblib.dump(random_forest_model, artifacts.model)
    predictions_frame.to_csv(artifacts.predictions, index=False)
    artifacts.metrics.write_text(json.dumps(holdout_metrics, indent=2), encoding="utf-8")

    if walk_forward_predictions is not None and walk_forward_summary is not None:
        walk_forward_predictions.to_csv(artifacts.walk_forward_predictions, index=False)
        artifacts.walk_forward_metrics.write_text(
            json.dumps(walk_forward_summary, indent=2),
            encoding="utf-8",
        )

    artifacts.forecast.write_text(json.dumps(next_forecast, indent=2), encoding="utf-8")
    artifacts.summary.write_text(
        json.dumps(
            {
                "source_name": source_name,
                "last_close": float(price_data["Close"].iloc[-1]),
                "average_recent_rsi": average_rsi,
                "average_forecast_slope": forecast_slope,
                "forecast_days": args.forecast_days,
                "next_forecast": next_forecast,
                "metrics": {
                    "baseline_persistence": holdout_metrics["baseline_persistence"],
                    "random_forest": holdout_metrics["random_forest"],
                    "walk_forward": walk_forward_summary,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    artifacts.metadata.write_text(
        json.dumps(
            {
                "source_name": source_name,
                "source_type": "csv" if args.csv_path else "ticker",
                "csv_path": args.csv_path,
                "date_column": args.date_column if args.csv_path else None,
                "close_column": args.close_column if args.csv_path else None,
                "lags": args.lags,
                "training_target": "next_day_return",
                "reported_forecast_value": "next_day_close",
                "forecast_days": args.forecast_days,
                "display_days": args.display_days,
                "rsi_window": args.rsi_window,
                "test_size": args.test_size,
                "train_rows": len(train_frame),
                "test_rows": len(test_frame),
                "data_rows": len(price_data),
                "data_start": price_data.index[0].date().isoformat(),
                "data_end": price_data.index[-1].date().isoformat(),
                "feature_columns": dataset.feature_columns,
                "walk_forward": {
                    "enabled": args.walk_forward_folds > 0,
                    "folds": args.walk_forward_folds,
                    "initial_train_size": args.walk_forward_train_size,
                },
                "random_forest": {
                    "n_estimators": random_forest_config.n_estimators,
                    "max_depth": random_forest_config.max_depth,
                    "min_samples_leaf": random_forest_config.min_samples_leaf,
                    "random_state": random_forest_config.random_state,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    save_history_plot(
        artifact_path=artifacts.history_plot,
        close_series=price_data["Close"].astype(float),
        display_days=args.display_days,
    )
    save_prediction_plot(
        artifact_path=artifacts.test_plot,
        prediction_frame=predictions_frame,
        title="Chronological holdout predictions",
    )
    if walk_forward_predictions is not None:
        save_prediction_plot(
            artifact_path=artifacts.walk_forward_plot,
            prediction_frame=walk_forward_predictions,
            title="Walk-forward predictions",
        )
    save_forecast_plot(
        artifact_path=artifacts.forecast_plot,
        close_series=price_data["Close"].astype(float),
        future_dates=future_dates,
        future_prices=future_price_predictions,
        display_days=args.display_days,
    )

    print(f"Source: {source_name}")
    print(
        "Data range: "
        f"{price_data.index[0].date().isoformat()} to {price_data.index[-1].date().isoformat()} "
        f"({len(price_data)} rows)"
    )
    print(f"Train rows: {len(train_frame)} | Test rows: {len(test_frame)}")
    print("Holdout baseline metrics:")
    print(
        f"  MSE={holdout_metrics['baseline_persistence']['mse']:.4f} "
        f"RMSE={holdout_metrics['baseline_persistence']['rmse']:.4f} "
        f"MAE={holdout_metrics['baseline_persistence']['mae']:.4f} "
        f"Direction={holdout_metrics['baseline_persistence']['directional_accuracy']:.2%}"
    )
    print("Holdout Random Forest metrics:")
    print(
        f"  MSE={holdout_metrics['random_forest']['mse']:.4f} "
        f"RMSE={holdout_metrics['random_forest']['rmse']:.4f} "
        f"MAE={holdout_metrics['random_forest']['mae']:.4f} "
        f"Direction={holdout_metrics['random_forest']['directional_accuracy']:.2%}"
    )
    if walk_forward_summary is None:
        print("Walk-forward: disabled")
    else:
        print(
            "Walk-forward overall: "
            f"{walk_forward_summary['fold_count']} folds | "
            f"{walk_forward_summary['total_predictions']} predictions"
        )
        print(
            f"  Baseline RMSE={walk_forward_summary['overall']['baseline_persistence']['rmse']:.4f} "
            f"Direction={walk_forward_summary['overall']['baseline_persistence']['directional_accuracy']:.2%}"
        )
        print(
            f"  Random Forest RMSE={walk_forward_summary['overall']['random_forest']['rmse']:.4f} "
            f"Direction={walk_forward_summary['overall']['random_forest']['directional_accuracy']:.2%}"
        )
    print(
        "Next forecast: "
        f"{next_forecast['forecast_date']} | "
        f"baseline={next_forecast['baseline_prediction']:.2f} | "
        f"random_forest={next_forecast['random_forest_prediction']:.2f}"
    )
    if average_rsi is None:
        print(f"Average RSI ({args.forecast_days} days): not enough data available")
    else:
        print(f"Average RSI ({args.forecast_days} days): {average_rsi:.2f}")
    print(f"Average forecast slope: {forecast_slope:.4f} per business day")
    print("Forecast path:")
    for forecast_date, forecast_price in zip(future_dates, future_price_predictions):
        print(f"  {forecast_date.date().isoformat()}: {forecast_price:.2f}")
    print(f"Artifacts written to: {artifacts.base_dir}")

    if args.show_plot:
        show_plots(
            close_series=price_data["Close"].astype(float),
            display_days=args.display_days,
            test_frame=test_frame,
            baseline_predictions=predictions_frame["baseline_prediction"].to_numpy(dtype=float),
            random_forest_predictions=predictions_frame["random_forest_prediction"].to_numpy(
                dtype=float
            ),
            future_dates=future_dates,
            future_prices=future_price_predictions,
        )


if __name__ == "__main__":
    main()
