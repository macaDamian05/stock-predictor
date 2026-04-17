from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


DEFAULT_START_DATE = "1990-01-01"


@dataclass(frozen=True)
class TrainingConfig:
    lookback_days: int = 200
    forecast_days: int = 5
    display_days: int = 200
    lstm_units: int = 75
    epochs: int = 300
    batch_size: int = 32
    rsi_window: int = 14
    start_date: str = DEFAULT_START_DATE
    end_date: str | None = None
    show_plots: bool = True
    training_verbose: int = 1
    prediction_verbose: int = 0

    def __post_init__(self) -> None:
        numeric_values = {
            "lookback_days": self.lookback_days,
            "forecast_days": self.forecast_days,
            "display_days": self.display_days,
            "lstm_units": self.lstm_units,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "rsi_window": self.rsi_window,
        }
        for field_name, value in numeric_values.items():
            if value <= 0:
                raise ValueError(f"{field_name} must be positive, got {value}.")

    @property
    def resolved_end_date(self) -> str:
        return self.end_date or date.today().isoformat()

    def to_metadata_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["end_date"] = self.resolved_end_date
        return payload
