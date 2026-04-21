from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np

from core.config import TrainingConfig
from core.data_loader import download_price_data
from core.indicators import average_recent_rsi, calculate_rsi
from core.model_factory import build_lstm_model
from core.paths import ensure_runtime_directories, get_artifact_paths
from core.predictor import (
    average_daily_slope,
    average_distance_pct_to_reference,
    average_distance_to_reference,
    build_forecast_index,
    forecast_future_prices,
    predict_historical,
    regression_metrics,
)
from core.preprocessing import PreparedData, prepare_training_data
from core.trainer import (
    append_run_log,
    artifacts_exist,
    build_incremental_frame,
    config_requires_full_retrain,
    fit_and_persist_model,
    load_metadata,
    load_saved_model,
    load_saved_scaler,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train, update, and evaluate the stock predictor prototype."
    )
    parser.add_argument("ticker", nargs="?", help="Ticker symbol, for example AAPL or ENR.DE.")
    parser.add_argument("--retrain", action="store_true", help="Ignore stored artifacts and train again.")
    parser.add_argument("--start-date", default="1990-01-01", help="Historical download start date.")
    parser.add_argument("--end-date", default=None, help="Historical download end date.")
    parser.add_argument("--lookback-days", type=int, default=200, help="Days used as model input.")
    parser.add_argument("--forecast-days", type=int, default=5, help="Business days to predict ahead.")
    parser.add_argument("--display-days", type=int, default=200, help="Days shown in history plots.")
    parser.add_argument("--lstm-units", type=int, default=75, help="Number of LSTM units.")
    parser.add_argument("--epochs", type=int, default=300, help="Training epochs.")
    parser.add_argument("--batch-size", type=int, default=32, help="Training batch size.")
    parser.add_argument("--rsi-window", type=int, default=14, help="RSI rolling window.")
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Disable matplotlib windows. Useful for remote runs and CI.",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> TrainingConfig:
    return TrainingConfig(
        lookback_days=args.lookback_days,
        forecast_days=args.forecast_days,
        display_days=args.display_days,
        lstm_units=args.lstm_units,
        epochs=args.epochs,
        batch_size=args.batch_size,
        rsi_window=args.rsi_window,
        start_date=args.start_date,
        end_date=args.end_date,
        show_plots=not args.no_plots,
    )


def plot_close_history(ticker: str, close_series) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(close_series.index, close_series.values, label="Close price")
    plt.title(f"{ticker} closing prices")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_historical_fit(
    ticker: str,
    target_dates,
    actual_prices: np.ndarray,
    predicted_prices: np.ndarray,
    display_days: int,
) -> None:
    display_start = max(0, len(target_dates) - display_days)

    plt.figure(figsize=(12, 6))
    plt.plot(target_dates[display_start:], actual_prices[display_start:], label="Actual prices")
    plt.plot(target_dates[display_start:], predicted_prices[display_start:], label="Predicted prices")
    plt.title(f"Actual vs predicted close prices for {ticker}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_future_forecast(ticker: str, close_series, future_dates, future_prices: np.ndarray) -> None:
    history_window = min(len(close_series), max(20, len(future_prices) * 2))
    recent_history = close_series.tail(history_window)

    plt.figure(figsize=(12, 6))
    plt.plot(recent_history.index, recent_history.values, label="Recent close prices")
    plt.plot(
        future_dates,
        future_prices,
        marker="o",
        linestyle="--",
        color="red",
        label="Forecast",
    )
    plt.title(f"{ticker} forecast for the next {len(future_prices)} business days")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def run_pipeline(ticker: str, config: TrainingConfig, force_retrain: bool = False) -> None:
    ensure_runtime_directories()
    paths = get_artifact_paths(ticker)
    data = download_price_data(ticker, config.start_date, config.resolved_end_date)
    close_series = data["Close"].astype(float)
    last_data_date = data.index[-1].date().isoformat()

    metadata = load_metadata(paths)
    has_artifacts = artifacts_exist(paths)

    prepared_full: PreparedData | None = None

    if config.show_plots:
        plot_close_history(ticker, close_series)

    if (
        force_retrain
        or
        not has_artifacts
        or metadata is None
        or config_requires_full_retrain(metadata, config)
    ):
        prepared_full = prepare_training_data(data, config.lookback_days)
        model = build_lstm_model(config.lstm_units, config.lookback_days)
        if force_retrain:
            run_mode = "manual_retrain"
        else:
            run_mode = "initial_train" if not has_artifacts else "configuration_retrain"
        fit_and_persist_model(
            model=model,
            prepared_data=prepared_full,
            paths=paths,
            ticker=ticker,
            config=config,
            last_data_date=last_data_date,
            run_mode=run_mode,
        )
        active_scaler = prepared_full.scaler
    else:
        model = load_saved_model(paths)
        active_scaler = load_saved_scaler(paths)
        saved_date = metadata.get("last_data_date")

        if saved_date == last_data_date:
            run_mode = "loaded_current_model"
            append_run_log(
                paths=paths,
                run_mode=run_mode,
                config=config,
                last_data_date=last_data_date,
                sample_count=0,
            )
        else:
            try:
                incremental_frame = build_incremental_frame(
                    data=data,
                    saved_date=saved_date,
                    lookback_days=config.lookback_days,
                )
            except ValueError as error:
                prepared_full = prepare_training_data(data, config.lookback_days)
                model = build_lstm_model(config.lstm_units, config.lookback_days)
                run_mode = "metadata_retrain"
                fit_and_persist_model(
                    model=model,
                    prepared_data=prepared_full,
                    paths=paths,
                    ticker=ticker,
                    config=config,
                    last_data_date=last_data_date,
                    run_mode=run_mode,
                )
                active_scaler = prepared_full.scaler
                append_run_log(
                    paths=paths,
                    run_mode="metadata_warning",
                    config=config,
                    last_data_date=last_data_date,
                    sample_count=0,
                    note=str(error),
                )
            else:
                if incremental_frame.empty:
                    run_mode = "loaded_current_model"
                    append_run_log(
                        paths=paths,
                        run_mode=run_mode,
                        config=config,
                        last_data_date=last_data_date,
                        sample_count=0,
                    )
                else:
                    prepared_incremental = prepare_training_data(
                        incremental_frame,
                        lookback_days=config.lookback_days,
                        scaler=active_scaler,
                        fit_scaler=False,
                    )
                    run_mode = "incremental_update"
                    fit_and_persist_model(
                        model=model,
                        prepared_data=prepared_incremental,
                        paths=paths,
                        ticker=ticker,
                        config=config,
                        last_data_date=last_data_date,
                        run_mode=run_mode,
                    )

    if prepared_full is None:
        prepared_full = prepare_training_data(
            data,
            lookback_days=config.lookback_days,
            scaler=active_scaler,
            fit_scaler=False,
        )

    historical_predictions = predict_historical(
        model=model,
        prepared_data=prepared_full,
        verbose=config.prediction_verbose,
    )
    future_predictions = forecast_future_prices(
        model=model,
        close_scaled=prepared_full.close_scaled,
        scaler=prepared_full.scaler,
        lookback_days=config.lookback_days,
        forecast_days=config.forecast_days,
        verbose=config.prediction_verbose,
    )
    future_dates = build_forecast_index(data.index[-1], config.forecast_days)

    actual_prices = close_series.iloc[config.lookback_days:].to_numpy(dtype=float)
    metrics = regression_metrics(actual_prices, historical_predictions)
    average_slope = average_daily_slope(future_predictions)
    average_distance_to_last_close = average_distance_to_reference(
        future_predictions,
        reference_value=float(close_series.iloc[-1]),
    )
    average_distance_pct_to_last_close = average_distance_pct_to_reference(
        future_predictions,
        reference_value=float(close_series.iloc[-1]),
    )

    rsi_values = calculate_rsi(close_series, config.rsi_window)
    average_rsi = average_recent_rsi(rsi_values, config.forecast_days)

    print(f"Ticker: {ticker}")
    print(
        "Data range: "
        f"{data.index[0].date().isoformat()} to {data.index[-1].date().isoformat()} "
        f"({len(data)} rows)"
    )
    print(f"Artifacts directory: {paths.base_dir}")
    print(f"Execution mode: {run_mode}")
    print(f"MAE: {metrics['mae']:.4f}")
    print(f"RMSE: {metrics['rmse']:.4f}")
    print(f"Directional accuracy: {metrics['directional_accuracy']:.2%}")
    print(f"Average forecast slope: {average_slope:.4f} per business day")
    print(
        "Average forecast distance to last close: "
        f"{average_distance_to_last_close:.4f} "
        f"({average_distance_pct_to_last_close:.2f}%)"
    )

    if average_rsi is None:
        print(f"Average RSI ({config.forecast_days} days): not enough data available")
    else:
        print(f"Average RSI ({config.forecast_days} days): {average_rsi:.2f}")

    print("Forecast:")
    for forecast_date, predicted_price in zip(future_dates, future_predictions):
        print(f"  {forecast_date.date().isoformat()}: {predicted_price:.2f}")

    if config.show_plots:
        plot_historical_fit(
            ticker=ticker,
            target_dates=prepared_full.target_dates,
            actual_prices=actual_prices,
            predicted_prices=historical_predictions,
            display_days=config.display_days,
        )
        plot_future_forecast(
            ticker=ticker,
            close_series=close_series,
            future_dates=future_dates,
            future_prices=future_predictions,
        )


def main() -> None:
    args = parse_args()
    ticker = (args.ticker or input("Please enter a ticker symbol: ")).strip().upper()
    if not ticker:
        raise ValueError("Ticker symbol is required.")

    config = build_config(args)
    run_pipeline(ticker=ticker, config=config, force_retrain=args.retrain)


if __name__ == "__main__":
    main()
