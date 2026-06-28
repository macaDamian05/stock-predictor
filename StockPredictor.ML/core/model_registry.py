from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .paths import CORE_PREDICTIONS_DIR, MODEL_REGISTRY_DIR, TRAINED_MODELS_DIR, sanitize_ticker


MODEL_LABELS: dict[str, str] = {
    "baseline_persistence": "Persistence-Baseline",
    "ridge_regression": "Ridge-Regression",
    "random_forest": "Random Forest",
    "lstm": "LSTM",
}


@dataclass(frozen=True)
class CoreModelMetric:
    model_key: str
    model_label: str
    mse: float
    rmse: float
    mae: float
    mape: float | None
    directional_accuracy: float
    sample_count: int
    rmse_gap_vs_baseline: float | None = None
    mae_gap_vs_baseline: float | None = None
    directional_accuracy_gap_vs_baseline: float | None = None
    is_selected: bool = False


@dataclass(frozen=True)
class CoreModelRegistryRecord:
    symbol: str
    horizon: int
    trained_at: str
    data_start: str
    data_until: str
    validation_start: str
    validation_end: str
    lags: int
    feature_profile: str
    target: str
    selected_model_key: str
    selected_model_label: str
    model_paths: dict[str, str]
    feature_columns: list[str]
    metrics: list[CoreModelMetric]
    training_rows: int
    validation_rows: int
    source: str
    notes: list[str]


def model_label(model_key: str) -> str:
    return MODEL_LABELS.get(model_key, model_key.replace("_", " ").title())


def get_registry_dir(symbol: str, horizon: int) -> Path:
    path = MODEL_REGISTRY_DIR / sanitize_ticker(symbol) / f"horizon_{horizon}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_registry_path(symbol: str, horizon: int) -> Path:
    return get_registry_dir(symbol, horizon) / "registry.json"


def get_prediction_dir(symbol: str, horizon: int) -> Path:
    path = CORE_PREDICTIONS_DIR / sanitize_ticker(symbol) / f"horizon_{horizon}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_prediction_path(symbol: str, horizon: int) -> Path:
    return get_prediction_dir(symbol, horizon) / "latest_prediction.json"


def get_model_dir(symbol: str, horizon: int) -> Path:
    path = TRAINED_MODELS_DIR / sanitize_ticker(symbol) / f"horizon_{horizon}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_model_path(symbol: str, horizon: int, model_key: str) -> Path:
    return get_model_dir(symbol, horizon) / f"{model_key}.joblib"


def save_registry(record: CoreModelRegistryRecord) -> Path:
    path = get_registry_path(record.symbol, record.horizon)
    payload = asdict(record)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_registry(symbol: str, horizon: int) -> CoreModelRegistryRecord:
    path = get_registry_path(symbol, horizon)
    if not path.exists():
        raise FileNotFoundError(
            f"No model registry found for {symbol} horizon {horizon}. "
            f"Run scripts/train_model_suite.py first."
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    return registry_from_dict(payload)


def registry_from_dict(payload: dict[str, Any]) -> CoreModelRegistryRecord:
    metrics = [CoreModelMetric(**metric) for metric in payload.get("metrics", [])]
    return CoreModelRegistryRecord(
        symbol=payload["symbol"],
        horizon=int(payload["horizon"]),
        trained_at=payload["trained_at"],
        data_start=payload["data_start"],
        data_until=payload["data_until"],
        validation_start=payload["validation_start"],
        validation_end=payload["validation_end"],
        lags=int(payload["lags"]),
        feature_profile=payload["feature_profile"],
        target=payload.get("target", "next_day_return"),
        selected_model_key=payload["selected_model_key"],
        selected_model_label=payload["selected_model_label"],
        model_paths=dict(payload.get("model_paths", {})),
        feature_columns=list(payload.get("feature_columns", [])),
        metrics=metrics,
        training_rows=int(payload.get("training_rows", 0)),
        validation_rows=int(payload.get("validation_rows", 0)),
        source=payload.get("source", "unknown"),
        notes=list(payload.get("notes", [])),
    )


def discover_registries(symbols: list[str] | None = None, horizon: int | None = None) -> list[CoreModelRegistryRecord]:
    if not MODEL_REGISTRY_DIR.exists():
        return []

    allowed_symbols = {sanitize_ticker(symbol) for symbol in symbols} if symbols else None
    records: list[CoreModelRegistryRecord] = []
    for path in MODEL_REGISTRY_DIR.glob("*/horizon_*/registry.json"):
        symbol_dir = path.parents[1].name
        if allowed_symbols is not None and symbol_dir not in allowed_symbols:
            continue

        if horizon is not None and path.parent.name != f"horizon_{horizon}":
            continue

        records.append(registry_from_dict(json.loads(path.read_text(encoding="utf-8"))))

    return sorted(records, key=lambda record: (record.symbol, record.horizon))


def utc_now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
