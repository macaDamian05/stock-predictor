from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

from models.baseline_model import create_baseline_model
from models.random_forest_model import create_random_forest_model
from models.ridge_model import create_ridge_model

from .config import DEFAULT_START_DATE
from .data_loader import load_price_data_for_symbol
from .evaluation import add_baseline_gaps, calculate_prediction_metrics, select_best_model_key
from .model_registry import (
    CoreModelMetric,
    CoreModelRegistryRecord,
    get_model_path,
    model_label,
    save_registry,
    utc_now_iso,
)
from .prediction_service import predict_saved_model
from .tabular_features import (
    DEFAULT_FEATURE_PROFILE,
    REFERENCE_COLUMN,
    RETURN_TARGET_COLUMN,
    TARGET_COLUMN,
    build_next_close_dataset,
    chronological_train_test_split,
)


DEFAULT_CORE_MODELS = ("baseline_persistence", "ridge_regression", "random_forest")


@dataclass(frozen=True)
class CoreTrainingConfig:
    horizon: int = 5
    lags: int = 10
    feature_profile: str = DEFAULT_FEATURE_PROFILE
    validation_size: float = 0.2
    start_date: str = DEFAULT_START_DATE
    end_date: str | None = None
    prefer_cached_market_data: bool = True
    model_keys: tuple[str, ...] = DEFAULT_CORE_MODELS


@dataclass(frozen=True)
class CoreTrainingResult:
    symbol: str
    horizon: int
    selected_model_key: str
    registry_path: Path
    prediction_path: Path | None


class CoreModelOrchestrator:
    def __init__(self, config: CoreTrainingConfig) -> None:
        if config.horizon <= 0:
            raise ValueError(f"horizon must be positive, got {config.horizon}.")
        if config.lags <= 0:
            raise ValueError(f"lags must be positive, got {config.lags}.")

        self.config = config

    def train_symbol(self, symbol: str) -> CoreTrainingResult:
        data = load_price_data_for_symbol(
            symbol,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            prefer_cached_snapshot=self.config.prefer_cached_market_data,
        )
        dataset = build_next_close_dataset(
            data,
            lags=self.config.lags,
            feature_profile=self.config.feature_profile,
        )
        train_frame, validation_frame = chronological_train_test_split(
            dataset.supervised_frame,
            test_size=self.config.validation_size,
        )

        metrics_by_model: dict[str, dict[str, float | int | None]] = {}
        for model_key in self.config.model_keys:
            model = create_core_model(model_key)
            model.fit(train_frame[dataset.feature_columns], train_frame[RETURN_TARGET_COLUMN])
            predicted_returns = np.asarray(
                model.predict(validation_frame[dataset.feature_columns]),
                dtype=float,
            )
            predicted_close = validation_frame[REFERENCE_COLUMN].to_numpy(dtype=float) * (
                1.0 + predicted_returns
            )
            metrics_by_model[model_key] = calculate_prediction_metrics(
                actual_close=validation_frame[TARGET_COLUMN],
                predicted_close=predicted_close,
                reference_close=validation_frame[REFERENCE_COLUMN],
            )

        metrics_by_model = add_baseline_gaps(metrics_by_model)
        selected_model_key = select_best_model_key(metrics_by_model)

        model_paths: dict[str, str] = {}
        for model_key in self.config.model_keys:
            final_model = create_core_model(model_key)
            final_model.fit(
                dataset.supervised_frame[dataset.feature_columns],
                dataset.supervised_frame[RETURN_TARGET_COLUMN],
            )
            model_path = get_model_path(symbol, self.config.horizon, model_key)
            joblib.dump(final_model, model_path)
            model_paths[model_key] = str(model_path)

        metric_records = [
            CoreModelMetric(
                model_key=model_key,
                model_label=model_label(model_key),
                mse=float(metrics["mse"]),
                rmse=float(metrics["rmse"]),
                mae=float(metrics["mae"]),
                mape=None if metrics["mape"] is None else float(metrics["mape"]),
                directional_accuracy=float(metrics["directional_accuracy"]),
                sample_count=int(metrics["sample_count"]),
                rmse_gap_vs_baseline=_optional_float(metrics["rmse_gap_vs_baseline"]),
                mae_gap_vs_baseline=_optional_float(metrics["mae_gap_vs_baseline"]),
                directional_accuracy_gap_vs_baseline=_optional_float(
                    metrics["directional_accuracy_gap_vs_baseline"]
                ),
                is_selected=model_key == selected_model_key,
            )
            for model_key, metrics in metrics_by_model.items()
        ]

        record = CoreModelRegistryRecord(
            symbol=symbol.upper(),
            horizon=self.config.horizon,
            trained_at=utc_now_iso(),
            data_start=_date_to_iso(data.index[0]),
            data_until=_date_to_iso(data.index[-1]),
            validation_start=_date_to_iso(validation_frame.index[0]),
            validation_end=_date_to_iso(validation_frame.index[-1]),
            lags=self.config.lags,
            feature_profile=self.config.feature_profile,
            target="next_day_return",
            selected_model_key=selected_model_key,
            selected_model_label=model_label(selected_model_key),
            model_paths=model_paths,
            feature_columns=dataset.feature_columns,
            metrics=metric_records,
            training_rows=len(train_frame),
            validation_rows=len(validation_frame),
            source="local_market_snapshot_or_yfinance",
            notes=[
                "Chronological validation split without shuffling.",
                "Saved models are used for prediction; the web app does not retrain on page visits.",
                "Outputs are research estimates and not investment advice.",
            ],
        )
        registry_path = save_registry(record)

        prediction_path: Path | None = None
        prediction = predict_saved_model(
            symbol=symbol,
            horizon=self.config.horizon,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            prefer_cached_market_data=self.config.prefer_cached_market_data,
            persist=True,
        )
        prediction_path = prediction.path

        return CoreTrainingResult(
            symbol=symbol.upper(),
            horizon=self.config.horizon,
            selected_model_key=selected_model_key,
            registry_path=registry_path,
            prediction_path=prediction_path,
        )

    def train_symbols(self, symbols: list[str]) -> list[CoreTrainingResult]:
        return [self.train_symbol(symbol) for symbol in symbols]


def create_core_model(model_key: str):
    if model_key == "baseline_persistence":
        return create_baseline_model()
    if model_key == "ridge_regression":
        return create_ridge_model()
    if model_key == "random_forest":
        return create_random_forest_model()

    raise ValueError(f"Unknown core model key: {model_key}")


def _date_to_iso(value) -> str:
    return value.date().isoformat()


def _optional_float(value: float | int | None) -> float | None:
    return None if value is None else float(value)
