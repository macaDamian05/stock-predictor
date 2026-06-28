from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import DEFAULT_START_DATE
from .data_loader import load_price_data_for_symbol
from .model_registry import (
    CoreModelRegistryRecord,
    get_prediction_path,
    load_registry,
    utc_now_iso,
)
from .tabular_features import build_latest_feature_frame_from_close_series


@dataclass(frozen=True)
class CoreForecastPoint:
    date: str
    predicted_return: float
    predicted_close: float


@dataclass(frozen=True)
class CorePredictionResult:
    symbol: str
    horizon: int
    generated_at: str
    model_trained_at: str
    data_start: str
    data_until: str
    last_close_date: str
    last_close: float
    selected_model_key: str
    selected_model_label: str
    forecast_path: list[CoreForecastPoint]
    next_forecast_date: str
    next_predicted_close: float
    next_predicted_change_pct: float
    forecast_end_date: str
    forecast_end_close: float
    forecast_horizon_change_pct: float
    average_forecast_slope: float
    average_forecast_distance_to_last_close: float
    average_forecast_distance_pct_to_last_close: float
    path: Path | None = None


def predict_saved_model(
    symbol: str,
    horizon: int,
    start_date: str = DEFAULT_START_DATE,
    end_date: str | None = None,
    prefer_cached_market_data: bool = True,
    persist: bool = True,
) -> CorePredictionResult:
    registry = load_registry(symbol, horizon)
    model_path = registry.model_paths.get(registry.selected_model_key)
    if model_path is None:
        raise FileNotFoundError(
            f"Selected model '{registry.selected_model_key}' has no saved model path in the registry."
        )
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"Saved model file not found: {model_path}. Run scripts/train_model_suite.py first."
        )

    model = joblib.load(model_path)
    data = load_price_data_for_symbol(
        symbol,
        start_date=start_date,
        end_date=end_date,
        prefer_cached_snapshot=prefer_cached_market_data,
    )
    result = predict_from_model_and_registry(model, registry, data)

    if persist:
        path = save_prediction(result)
        return replace(result, path=path)

    return result


def predict_from_model_and_registry(
    model,
    registry: CoreModelRegistryRecord,
    data: pd.DataFrame,
) -> CorePredictionResult:
    close_history = data["Close"].astype(float).copy()
    if close_history.empty:
        raise ValueError(f"No close prices available for {registry.symbol}.")

    last_close = float(close_history.iloc[-1])
    last_close_date = close_history.index[-1].date().isoformat()
    future_dates = pd.bdate_range(
        start=close_history.index[-1] + pd.offsets.BDay(1),
        periods=registry.horizon,
    )

    forecast_points: list[CoreForecastPoint] = []
    for forecast_date in future_dates:
        latest_features, _ = build_latest_feature_frame_from_close_series(
            close_history,
            lags=registry.lags,
            feature_profile=registry.feature_profile,
        )
        latest_features = latest_features[registry.feature_columns]
        predicted_return = float(np.asarray(model.predict(latest_features), dtype=float)[0])
        if not np.isfinite(predicted_return):
            raise ValueError(
                f"Model '{registry.selected_model_key}' returned a non-finite prediction."
            )

        previous_close = float(close_history.iloc[-1])
        predicted_close = previous_close * (1.0 + predicted_return)
        close_history.loc[forecast_date] = predicted_close
        forecast_points.append(
            CoreForecastPoint(
                date=forecast_date.date().isoformat(),
                predicted_return=predicted_return,
                predicted_close=float(predicted_close),
            )
        )

    if not forecast_points:
        raise ValueError("Forecast horizon produced no forecast points.")

    predicted_closes = np.asarray([point.predicted_close for point in forecast_points], dtype=float)
    forecast_end_close = float(predicted_closes[-1])
    average_distance = float(np.mean(predicted_closes - last_close))
    average_distance_pct = float((average_distance / last_close) * 100.0) if last_close else 0.0
    average_slope = float(np.mean(np.diff(np.r_[last_close, predicted_closes])))

    return CorePredictionResult(
        symbol=registry.symbol,
        horizon=registry.horizon,
        generated_at=utc_now_iso(),
        model_trained_at=registry.trained_at,
        data_start=data.index[0].date().isoformat(),
        data_until=data.index[-1].date().isoformat(),
        last_close_date=last_close_date,
        last_close=last_close,
        selected_model_key=registry.selected_model_key,
        selected_model_label=registry.selected_model_label,
        forecast_path=forecast_points,
        next_forecast_date=forecast_points[0].date,
        next_predicted_close=forecast_points[0].predicted_close,
        next_predicted_change_pct=((forecast_points[0].predicted_close / last_close) - 1.0) * 100.0
        if last_close
        else 0.0,
        forecast_end_date=forecast_points[-1].date,
        forecast_end_close=forecast_end_close,
        forecast_horizon_change_pct=((forecast_end_close / last_close) - 1.0) * 100.0
        if last_close
        else 0.0,
        average_forecast_slope=average_slope,
        average_forecast_distance_to_last_close=average_distance,
        average_forecast_distance_pct_to_last_close=average_distance_pct,
    )


def save_prediction(result: CorePredictionResult) -> Path:
    path = get_prediction_path(result.symbol, result.horizon)
    payload = asdict(result)
    payload.pop("path", None)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_prediction(symbol: str, horizon: int) -> CorePredictionResult:
    path = get_prediction_path(symbol, horizon)
    if not path.exists():
        raise FileNotFoundError(
            f"No prediction payload found for {symbol} horizon {horizon}. "
            f"Run scripts/predict_asset.py first."
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    return prediction_from_dict(payload, path=path)


def prediction_from_dict(payload: dict, path: Path | None = None) -> CorePredictionResult:
    forecast_path = [CoreForecastPoint(**point) for point in payload.get("forecast_path", [])]
    return CorePredictionResult(
        symbol=payload["symbol"],
        horizon=int(payload["horizon"]),
        generated_at=payload["generated_at"],
        model_trained_at=payload["model_trained_at"],
        data_start=payload["data_start"],
        data_until=payload["data_until"],
        last_close_date=payload["last_close_date"],
        last_close=float(payload["last_close"]),
        selected_model_key=payload["selected_model_key"],
        selected_model_label=payload["selected_model_label"],
        forecast_path=forecast_path,
        next_forecast_date=payload["next_forecast_date"],
        next_predicted_close=float(payload["next_predicted_close"]),
        next_predicted_change_pct=float(payload["next_predicted_change_pct"]),
        forecast_end_date=payload["forecast_end_date"],
        forecast_end_close=float(payload["forecast_end_close"]),
        forecast_horizon_change_pct=float(payload["forecast_horizon_change_pct"]),
        average_forecast_slope=float(payload["average_forecast_slope"]),
        average_forecast_distance_to_last_close=float(
            payload["average_forecast_distance_to_last_close"]
        ),
        average_forecast_distance_pct_to_last_close=float(
            payload["average_forecast_distance_pct_to_last_close"]
        ),
        path=path,
    )
