from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

import joblib
import pandas as pd

from .config import TrainingConfig
from .paths import ArtifactPaths


def artifacts_exist(paths: ArtifactPaths) -> bool:
    return all(path.exists() for path in (paths.model, paths.scaler, paths.metadata))


def load_metadata(paths: ArtifactPaths) -> dict[str, Any] | None:
    if not paths.metadata.exists():
        return None

    return json.loads(paths.metadata.read_text(encoding="utf-8"))


def load_saved_scaler(paths: ArtifactPaths):
    return joblib.load(paths.scaler)


def load_saved_model(paths: ArtifactPaths):
    try:
        from tensorflow.keras.models import load_model
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "TensorFlow is not installed. Create a Python 3.11 environment and install "
            "StockPredictor.ML/requirements.txt before loading a model."
        ) from exc

    return load_model(paths.model)


def config_requires_full_retrain(metadata: dict[str, Any] | None, config: TrainingConfig) -> bool:
    if metadata is None:
        return True

    return any(
        (
            metadata.get("lookback_days") != config.lookback_days,
            metadata.get("lstm_units") != config.lstm_units,
            metadata.get("start_date") != config.start_date,
        )
    )


def build_incremental_frame(data: pd.DataFrame, saved_date: str | None, lookback_days: int) -> pd.DataFrame:
    if not saved_date:
        raise ValueError("Metadata does not contain a last_data_date value.")

    saved_timestamp = pd.Timestamp(saved_date)
    if saved_timestamp not in data.index:
        raise ValueError(
            f"Saved date {saved_date} is not present in the current market data index."
        )

    saved_index = data.index.get_loc(saved_timestamp)
    if isinstance(saved_index, slice):
        saved_index = saved_index.stop - 1

    if saved_index >= len(data.index) - 1:
        return data.iloc[0:0]

    start_index = max(saved_index + 1 - lookback_days, 0)
    return data.iloc[start_index:].copy()


def append_run_log(
    paths: ArtifactPaths,
    run_mode: str,
    config: TrainingConfig,
    last_data_date: str,
    sample_count: int,
    note: str | None = None,
) -> None:
    timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
    line = (
        f"[{timestamp}] "
        f"mode={run_mode} "
        f"ticker={paths.ticker} "
        f"samples={sample_count} "
        f"lookback={config.lookback_days} "
        f"epochs={config.epochs} "
        f"batch_size={config.batch_size} "
        f"last_data_date={last_data_date}"
    )
    if note:
        line += f" note={note}"
    line += "\n"

    with paths.log.open("a", encoding="utf-8") as handle:
        handle.write(line)


def fit_and_persist_model(
    model,
    prepared_data,
    paths: ArtifactPaths,
    ticker: str,
    config: TrainingConfig,
    last_data_date: str,
    run_mode: str,
) -> dict[str, Any]:
    model.fit(
        prepared_data.X,
        prepared_data.y,
        epochs=config.epochs,
        batch_size=config.batch_size,
        verbose=config.training_verbose,
    )
    model.save(paths.model)
    joblib.dump(prepared_data.scaler, paths.scaler)

    metadata = {
        "ticker": ticker.upper(),
        "safe_ticker": paths.safe_ticker,
        "model_type": "single_layer_lstm",
        "last_data_date": last_data_date,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_mode": run_mode,
        "sample_count": int(len(prepared_data.X)),
        **config.to_metadata_dict(),
    }
    paths.metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    append_run_log(
        paths=paths,
        run_mode=run_mode,
        config=config,
        last_data_date=last_data_date,
        sample_count=int(len(prepared_data.X)),
    )

    return metadata
