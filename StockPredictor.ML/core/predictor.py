from __future__ import annotations

import numpy as np
import pandas as pd

from .preprocessing import PreparedData


def predict_historical(model, prepared_data: PreparedData, verbose: int = 0) -> np.ndarray:
    predicted_scaled = model.predict(prepared_data.X, verbose=verbose)
    return prepared_data.scaler.inverse_transform(predicted_scaled).reshape(-1)


def forecast_future_prices(
    model,
    close_scaled: np.ndarray,
    scaler,
    lookback_days: int,
    forecast_days: int,
    verbose: int = 0,
) -> np.ndarray:
    if len(close_scaled) < lookback_days:
        raise ValueError(
            f"Need at least {lookback_days} rows to forecast, got {len(close_scaled)}."
        )

    rolling_window = close_scaled[-lookback_days:].reshape(1, lookback_days, 1)
    future_scaled = []

    for _ in range(forecast_days):
        next_prediction = float(model.predict(rolling_window, verbose=verbose)[0, 0])
        future_scaled.append(next_prediction)
        next_step = np.array(next_prediction, dtype=float).reshape(1, 1, 1)
        rolling_window = np.concatenate([rolling_window[:, 1:, :], next_step], axis=1)

    return scaler.inverse_transform(np.asarray(future_scaled).reshape(-1, 1)).reshape(-1)


def build_forecast_index(last_date: pd.Timestamp, forecast_days: int) -> pd.DatetimeIndex:
    return pd.bdate_range(last_date + pd.offsets.BDay(1), periods=forecast_days)


def average_daily_slope(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0

    return float(np.diff(values).mean())


def average_distance_to_reference(
    values: np.ndarray,
    reference_value: float,
    absolute: bool = True,
) -> float:
    numeric_values = np.asarray(values, dtype=float).reshape(-1)
    if len(numeric_values) == 0:
        return 0.0

    distances = numeric_values - float(reference_value)
    if absolute:
        distances = np.abs(distances)

    return float(distances.mean())


def average_distance_pct_to_reference(
    values: np.ndarray,
    reference_value: float,
    absolute: bool = True,
) -> float:
    numeric_reference = float(reference_value)
    if abs(numeric_reference) < 1e-12:
        return 0.0

    return (
        average_distance_to_reference(values, reference_value=numeric_reference, absolute=absolute)
        / abs(numeric_reference)
        * 100.0
    )


def regression_metrics(actual_values: np.ndarray, predicted_values: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual_values, dtype=float).reshape(-1)
    predicted = np.asarray(predicted_values, dtype=float).reshape(-1)

    if actual.shape != predicted.shape:
        raise ValueError(
            f"Actual and predicted arrays must have identical shapes, got {actual.shape} and {predicted.shape}."
        )

    mse = float(np.mean((actual - predicted) ** 2))
    metrics = {
        "mae": float(np.mean(np.abs(actual - predicted))),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
    }

    if len(actual) < 2:
        metrics["directional_accuracy"] = 0.0
    else:
        actual_direction = np.sign(np.diff(actual))
        predicted_direction = np.sign(np.diff(predicted))
        metrics["directional_accuracy"] = float((actual_direction == predicted_direction).mean())

    return metrics


def one_step_directional_accuracy(
    reference_values: np.ndarray,
    actual_values: np.ndarray,
    predicted_values: np.ndarray,
) -> float:
    reference = np.asarray(reference_values, dtype=float).reshape(-1)
    actual = np.asarray(actual_values, dtype=float).reshape(-1)
    predicted = np.asarray(predicted_values, dtype=float).reshape(-1)

    if not (reference.shape == actual.shape == predicted.shape):
        raise ValueError(
            "Reference, actual, and predicted arrays must have identical shapes. "
            f"Got {reference.shape}, {actual.shape}, and {predicted.shape}."
        )

    if len(reference) == 0:
        return 0.0

    actual_direction = np.sign(actual - reference)
    predicted_direction = np.sign(predicted - reference)
    return float((actual_direction == predicted_direction).mean())
