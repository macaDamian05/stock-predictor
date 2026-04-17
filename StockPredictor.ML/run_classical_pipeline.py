from __future__ import annotations

import argparse
import json
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
from core.paths import ensure_runtime_directories, get_classical_artifact_paths
from core.predictor import (
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
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of chronological samples reserved for testing.",
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


def save_test_plot(
    artifact_path: Path,
    test_frame: pd.DataFrame,
    baseline_predictions,
    random_forest_predictions,
) -> None:
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
    plt.savefig(artifact_path, dpi=150)
    plt.close()


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    price_data, source_name = resolve_data_source(args)
    dataset = build_next_close_dataset(price_data, lags=args.lags)
    train_frame, test_frame = chronological_train_test_split(
        dataset.supervised_frame,
        test_size=args.test_size,
    )

    X_train = train_frame[dataset.feature_columns]
    y_train = train_frame[dataset.target_column].to_numpy(dtype=float)
    X_test = test_frame[dataset.feature_columns]
    y_test_close = test_frame[dataset.close_target_column].to_numpy(dtype=float)

    baseline_model = PersistenceRegressor(reference_column=dataset.reference_column)
    baseline_model.fit(X_train, y_train)
    baseline_predictions = baseline_model.predict(X_test)

    random_forest_config = RandomForestConfig(
        n_estimators=args.n_estimators,
        max_depth=None if args.max_depth == 0 else args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.random_state,
    )
    random_forest_model = build_random_forest_regressor(random_forest_config)
    random_forest_model.fit(X_train, y_train)
    random_forest_return_predictions = random_forest_model.predict(X_test)
    random_forest_predictions = X_test[dataset.reference_column].to_numpy(dtype=float) * (
        1.0 + random_forest_return_predictions
    )

    baseline_metrics = regression_metrics(y_test_close, baseline_predictions)
    baseline_metrics["directional_accuracy"] = one_step_directional_accuracy(
        reference_values=X_test[dataset.reference_column].to_numpy(dtype=float),
        actual_values=y_test_close,
        predicted_values=baseline_predictions,
    )

    random_forest_metrics = regression_metrics(y_test_close, random_forest_predictions)
    random_forest_metrics["directional_accuracy"] = one_step_directional_accuracy(
        reference_values=X_test[dataset.reference_column].to_numpy(dtype=float),
        actual_values=y_test_close,
        predicted_values=random_forest_predictions,
    )

    next_business_day = build_forecast_index(price_data.index[-1], 1)[0]
    latest_features = dataset.latest_features[dataset.feature_columns]
    next_return_prediction = float(random_forest_model.predict(latest_features)[0])
    next_forecast = {
        "forecast_date": next_business_day.date().isoformat(),
        "last_close_date": price_data.index[-1].date().isoformat(),
        "last_close": float(price_data["Close"].iloc[-1]),
        "baseline_prediction": float(baseline_model.predict(latest_features)[0]),
        "random_forest_predicted_return": next_return_prediction,
        "random_forest_prediction": float(
            latest_features[dataset.reference_column].iloc[0] * (1.0 + next_return_prediction)
        ),
    }

    predictions_frame = pd.DataFrame(
        {
            "feature_date": test_frame.index,
            "target_date": test_frame[dataset.target_date_column].to_numpy(),
            "close_current": X_test[dataset.reference_column].to_numpy(dtype=float),
            "actual_next_close": y_test_close,
            "actual_next_return": test_frame[dataset.target_column].to_numpy(dtype=float),
            "baseline_prediction": baseline_predictions,
            "random_forest_predicted_return": random_forest_return_predictions,
            "random_forest_prediction": random_forest_predictions,
        }
    )

    artifacts = get_classical_artifact_paths(source_name)
    joblib.dump(random_forest_model, artifacts.model)
    predictions_frame.to_csv(artifacts.predictions, index=False)
    artifacts.metrics.write_text(
        json.dumps(
            {
                "baseline_persistence": baseline_metrics,
                "random_forest": random_forest_metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    artifacts.forecast.write_text(json.dumps(next_forecast, indent=2), encoding="utf-8")
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
                "test_size": args.test_size,
                "train_rows": len(train_frame),
                "test_rows": len(test_frame),
                "data_rows": len(price_data),
                "data_start": price_data.index[0].date().isoformat(),
                "data_end": price_data.index[-1].date().isoformat(),
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
    save_test_plot(
        artifact_path=artifacts.plot,
        test_frame=test_frame,
        baseline_predictions=baseline_predictions,
        random_forest_predictions=random_forest_predictions,
    )

    print(f"Source: {source_name}")
    print(
        "Data range: "
        f"{price_data.index[0].date().isoformat()} to {price_data.index[-1].date().isoformat()} "
        f"({len(price_data)} rows)"
    )
    print(f"Train rows: {len(train_frame)} | Test rows: {len(test_frame)}")
    print("Baseline metrics:")
    print(
        f"  MSE={baseline_metrics['mse']:.4f} "
        f"RMSE={baseline_metrics['rmse']:.4f} "
        f"MAE={baseline_metrics['mae']:.4f} "
        f"Direction={baseline_metrics['directional_accuracy']:.2%}"
    )
    print("Random Forest metrics:")
    print(
        f"  MSE={random_forest_metrics['mse']:.4f} "
        f"RMSE={random_forest_metrics['rmse']:.4f} "
        f"MAE={random_forest_metrics['mae']:.4f} "
        f"Direction={random_forest_metrics['directional_accuracy']:.2%}"
    )
    print(
        "Next forecast: "
        f"{next_forecast['forecast_date']} | "
        f"baseline={next_forecast['baseline_prediction']:.2f} | "
        f"random_forest={next_forecast['random_forest_prediction']:.2f}"
    )
    print(f"Artifacts written to: {artifacts.base_dir}")

    if args.show_plot:
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
        plt.show()


if __name__ == "__main__":
    main()
