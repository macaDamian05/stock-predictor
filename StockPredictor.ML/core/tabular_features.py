from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


TARGET_COLUMN = "target_close_next"
RETURN_TARGET_COLUMN = "target_return_next"
TARGET_DATE_COLUMN = "target_date"
REFERENCE_COLUMN = "close_current"


@dataclass(frozen=True)
class NextCloseDataset:
    supervised_frame: pd.DataFrame
    latest_features: pd.DataFrame
    feature_columns: list[str]
    target_column: str = RETURN_TARGET_COLUMN
    close_target_column: str = TARGET_COLUMN
    target_date_column: str = TARGET_DATE_COLUMN
    reference_column: str = REFERENCE_COLUMN


def build_next_close_dataset(data: pd.DataFrame, lags: int) -> NextCloseDataset:
    if lags <= 0:
        raise ValueError(f"lags must be positive, got {lags}.")

    close_series = data["Close"].astype(float)
    return_series = close_series.pct_change()
    feature_frame = pd.DataFrame(index=data.index)
    feature_frame[REFERENCE_COLUMN] = close_series

    feature_columns = [REFERENCE_COLUMN]
    for lag in range(0, lags):
        column_name = f"return_lag_{lag}"
        feature_frame[column_name] = return_series.shift(lag)
        feature_columns.append(column_name)

    latest_features = feature_frame.dropna().tail(1).copy()
    if latest_features.empty:
        raise ValueError(
            f"Not enough rows to build features with {lags} lags. "
            f"At least {lags + 1} close values are required."
        )

    supervised_frame = feature_frame.copy()
    supervised_frame[RETURN_TARGET_COLUMN] = return_series.shift(-1)
    supervised_frame[TARGET_COLUMN] = close_series.shift(-1)
    supervised_frame[TARGET_DATE_COLUMN] = pd.Series(data.index, index=data.index).shift(-1)
    supervised_frame = supervised_frame.dropna().copy()

    if supervised_frame.empty:
        raise ValueError(
            f"Not enough rows to build supervised samples with {lags} lags. "
            f"At least {lags + 2} close values are required."
        )

    return NextCloseDataset(
        supervised_frame=supervised_frame,
        latest_features=latest_features,
        feature_columns=feature_columns,
    )


def chronological_train_test_split(
    frame: pd.DataFrame,
    test_size: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < test_size < 1:
        raise ValueError(f"test_size must be between 0 and 1, got {test_size}.")

    total_rows = len(frame)
    test_rows = max(1, math.ceil(total_rows * test_size))
    train_rows = total_rows - test_rows

    if train_rows < 1:
        raise ValueError(
            f"Split leaves no training rows. total_rows={total_rows}, test_size={test_size}."
        )

    train_frame = frame.iloc[:train_rows].copy()
    test_frame = frame.iloc[train_rows:].copy()
    return train_frame, test_frame
