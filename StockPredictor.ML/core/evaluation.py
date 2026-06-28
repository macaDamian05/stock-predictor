from __future__ import annotations

import math

import numpy as np
import pandas as pd


def calculate_prediction_metrics(
    actual_close: pd.Series | np.ndarray,
    predicted_close: pd.Series | np.ndarray,
    reference_close: pd.Series | np.ndarray,
) -> dict[str, float | int | None]:
    actual = np.asarray(actual_close, dtype=float)
    predicted = np.asarray(predicted_close, dtype=float)
    reference = np.asarray(reference_close, dtype=float)

    if len(actual) == 0:
        raise ValueError("Cannot calculate metrics for an empty validation set.")
    if len(actual) != len(predicted) or len(actual) != len(reference):
        raise ValueError("actual, predicted and reference arrays must have the same length.")

    errors = predicted - actual
    mse = float(np.mean(np.square(errors)))
    rmse = float(math.sqrt(mse))
    mae = float(np.mean(np.abs(errors)))

    non_zero_actual = np.abs(actual) > np.finfo(float).eps
    mape = None
    if np.any(non_zero_actual):
        mape = float(np.mean(np.abs(errors[non_zero_actual] / actual[non_zero_actual])) * 100.0)

    actual_direction = np.sign(actual - reference)
    predicted_direction = np.sign(predicted - reference)
    directional_accuracy = float(np.mean(actual_direction == predicted_direction))

    return {
        "mse": mse,
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "directional_accuracy": directional_accuracy,
        "sample_count": int(len(actual)),
    }


def add_baseline_gaps(
    metrics_by_model: dict[str, dict[str, float | int | None]],
    baseline_key: str = "baseline_persistence",
) -> dict[str, dict[str, float | int | None]]:
    baseline = metrics_by_model.get(baseline_key)
    if baseline is None:
        return metrics_by_model

    baseline_rmse = float(baseline["rmse"])
    baseline_mae = float(baseline["mae"])
    baseline_directional_accuracy = float(baseline["directional_accuracy"])

    enriched: dict[str, dict[str, float | int | None]] = {}
    for model_key, metrics in metrics_by_model.items():
        enriched_metrics = dict(metrics)
        enriched_metrics["rmse_gap_vs_baseline"] = float(metrics["rmse"]) - baseline_rmse
        enriched_metrics["mae_gap_vs_baseline"] = float(metrics["mae"]) - baseline_mae
        enriched_metrics["directional_accuracy_gap_vs_baseline"] = (
            float(metrics["directional_accuracy"]) - baseline_directional_accuracy
        )
        enriched[model_key] = enriched_metrics

    return enriched


def select_best_model_key(
    metrics_by_model: dict[str, dict[str, float | int | None]],
) -> str:
    if not metrics_by_model:
        raise ValueError("No model metrics available for selection.")

    return min(
        metrics_by_model,
        key=lambda model_key: (
            float(metrics_by_model[model_key]["rmse"]),
            float(metrics_by_model[model_key]["mae"]),
            -float(metrics_by_model[model_key]["directional_accuracy"]),
        ),
    )
