from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


@dataclass
class PreparedData:
    scaler: MinMaxScaler
    close_scaled: np.ndarray
    X: np.ndarray
    y: np.ndarray
    target_dates: pd.DatetimeIndex


def prepare_training_data(
    data: pd.DataFrame,
    lookback_days: int,
    scaler: MinMaxScaler | None = None,
    fit_scaler: bool = True,
) -> PreparedData:
    if lookback_days <= 0:
        raise ValueError(f"lookback_days must be positive, got {lookback_days}.")

    close_prices = data[["Close"]].astype(float).copy()

    if scaler is None:
        scaler = MinMaxScaler()
        fit_scaler = True

    close_scaled = scaler.fit_transform(close_prices) if fit_scaler else scaler.transform(close_prices)

    if len(close_scaled) <= lookback_days:
        raise ValueError(
            f"Not enough samples for lookback window {lookback_days}. Got only {len(close_scaled)} rows."
        )

    feature_rows = []
    target_values = []
    for index in range(lookback_days, len(close_scaled)):
        feature_rows.append(close_scaled[index - lookback_days:index, 0])
        target_values.append(close_scaled[index, 0])

    X = np.asarray(feature_rows, dtype=float).reshape(-1, lookback_days, 1)
    y = np.asarray(target_values, dtype=float)

    return PreparedData(
        scaler=scaler,
        close_scaled=close_scaled,
        X=X,
        y=y,
        target_dates=pd.DatetimeIndex(data.index[lookback_days:]),
    )
