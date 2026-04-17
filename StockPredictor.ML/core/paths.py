from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = PROJECT_ROOT / "storage"
TRAINING_DATA_DIR = STORAGE_DIR / "trainingsdaten"
CLASSICAL_DATA_DIR = STORAGE_DIR / "classical"


@dataclass(frozen=True)
class ArtifactPaths:
    ticker: str
    safe_ticker: str
    base_dir: Path
    model: Path
    scaler: Path
    metadata: Path
    log: Path


@dataclass(frozen=True)
class ClassicalArtifactPaths:
    source_name: str
    safe_name: str
    base_dir: Path
    model: Path
    metrics: Path
    predictions: Path
    forecast: Path
    metadata: Path
    plot: Path


def ensure_runtime_directories() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    CLASSICAL_DATA_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_name(value: str, uppercase: bool = False) -> str:
    normalized = value.upper() if uppercase else value
    return re.sub(r"[^A-Za-z0-9._-]", "_", normalized)


def sanitize_ticker(ticker: str) -> str:
    return sanitize_name(ticker, uppercase=True)


def get_artifact_paths(ticker: str) -> ArtifactPaths:
    safe_ticker = sanitize_ticker(ticker)
    base_dir = TRAINING_DATA_DIR / safe_ticker
    base_dir.mkdir(parents=True, exist_ok=True)

    return ArtifactPaths(
        ticker=ticker.upper(),
        safe_ticker=safe_ticker,
        base_dir=base_dir,
        model=base_dir / f"{safe_ticker}_lstm_model.keras",
        scaler=base_dir / f"{safe_ticker}_scaler.save",
        metadata=base_dir / f"{safe_ticker}_meta.json",
        log=base_dir / "training_log.txt",
    )


def get_classical_artifact_paths(source_name: str) -> ClassicalArtifactPaths:
    safe_name = sanitize_name(source_name, uppercase=True)
    base_dir = CLASSICAL_DATA_DIR / safe_name
    base_dir.mkdir(parents=True, exist_ok=True)

    return ClassicalArtifactPaths(
        source_name=source_name,
        safe_name=safe_name,
        base_dir=base_dir,
        model=base_dir / "random_forest.joblib",
        metrics=base_dir / "metrics.json",
        predictions=base_dir / "predictions.csv",
        forecast=base_dir / "forecast.json",
        metadata=base_dir / "metadata.json",
        plot=base_dir / "test_predictions.png",
    )
