from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from .indicators import calculate_rsi


TARGET_COLUMN = "target_close_next"
RETURN_TARGET_COLUMN = "target_return_next"
TARGET_DATE_COLUMN = "target_date"
REFERENCE_COLUMN = "close_current"
DEFAULT_FEATURE_PROFILE = "technical_extended"
FEATURE_PROFILES = {
    "lag_only": "Nur Rendite-Lags und aktueller Schlusskurs.",
    "technical_basic": "Lags plus einfache Trend-, Volatilitaets- und RSI-Features.",
    "technical_extended": "Erweiterter Technik-Satz mit EMA, Breakout, Drawdown und Z-Score.",
}


@dataclass(frozen=True)
class NextCloseDataset:
    supervised_frame: pd.DataFrame
    latest_features: pd.DataFrame
    feature_columns: list[str]
    feature_profile: str = DEFAULT_FEATURE_PROFILE
    target_column: str = RETURN_TARGET_COLUMN
    close_target_column: str = TARGET_COLUMN
    target_date_column: str = TARGET_DATE_COLUMN
    reference_column: str = REFERENCE_COLUMN


def build_feature_frame_from_close_series(
    close_series: pd.Series,
    lags: int,
    feature_profile: str = DEFAULT_FEATURE_PROFILE,
) -> tuple[pd.DataFrame, list[str]]:
    if lags <= 0:
        raise ValueError(f"lags must be positive, got {lags}.")
    if feature_profile not in FEATURE_PROFILES:
        raise ValueError(
            f"Unknown feature profile '{feature_profile}'. "
            f"Expected one of: {', '.join(FEATURE_PROFILES)}."
        )

    close_series = close_series.astype(float)
    return_series = close_series.pct_change()
    feature_frame = pd.DataFrame(index=close_series.index)
    feature_frame[REFERENCE_COLUMN] = close_series

    feature_columns = [REFERENCE_COLUMN]
    for lag in range(0, lags):
        column_name = f"return_lag_{lag}"
        feature_frame[column_name] = return_series.shift(lag)
        feature_columns.append(column_name)

    sma_5 = close_series.rolling(window=5, min_periods=5).mean()
    sma_10 = close_series.rolling(window=10, min_periods=10).mean()
    sma_20 = close_series.rolling(window=20, min_periods=20).mean()
    ema_5 = close_series.ewm(span=5, adjust=False, min_periods=5).mean()
    ema_10 = close_series.ewm(span=10, adjust=False, min_periods=10).mean()
    ema_20 = close_series.ewm(span=20, adjust=False, min_periods=20).mean()
    rolling_std_20 = close_series.rolling(window=20, min_periods=20).std()
    rolling_max_20 = close_series.rolling(window=20, min_periods=20).max()
    rolling_min_20 = close_series.rolling(window=20, min_periods=20).min()
    volatility_5 = return_series.rolling(window=5, min_periods=5).std()
    volatility_10 = return_series.rolling(window=10, min_periods=10).std()
    volatility_20 = return_series.rolling(window=20, min_periods=20).std()
    rsi_14 = calculate_rsi(close_series, window=14)
    momentum_5 = close_series.pct_change(periods=5)
    momentum_10 = close_series.pct_change(periods=10)
    momentum_20 = close_series.pct_change(periods=20)

    engineered_features: dict[str, pd.Series] = {}
    if feature_profile in {"technical_basic", "technical_extended"}:
        engineered_features.update(
            {
                "return_mean_5": return_series.rolling(window=5, min_periods=5).mean(),
                "return_mean_10": return_series.rolling(window=10, min_periods=10).mean(),
                "return_mean_20": return_series.rolling(window=20, min_periods=20).mean(),
                "sma_5_gap": (close_series / sma_5) - 1.0,
                "sma_10_gap": (close_series / sma_10) - 1.0,
                "sma_20_gap": (close_series / sma_20) - 1.0,
                "volatility_5": volatility_5,
                "volatility_10": volatility_10,
                "volatility_20": volatility_20,
                "momentum_5": momentum_5,
                "momentum_10": momentum_10,
                "momentum_20": momentum_20,
                "rsi_14": rsi_14 / 100.0,
            }
        )
    if feature_profile == "technical_extended":
        engineered_features.update(
            {
                "ema_5_gap": (close_series / ema_5) - 1.0,
                "ema_10_gap": (close_series / ema_10) - 1.0,
                "ema_20_gap": (close_series / ema_20) - 1.0,
                "breakout_20_gap": (close_series / rolling_max_20) - 1.0,
                "drawdown_20_gap": (close_series / rolling_min_20) - 1.0,
                "price_zscore_20": (close_series - sma_20) / rolling_std_20,
            }
        )

    for column_name, values in engineered_features.items():
        feature_frame[column_name] = values
        feature_columns.append(column_name)

    return feature_frame, feature_columns


def build_latest_feature_frame_from_close_series(
    close_series: pd.Series,
    lags: int,
    feature_profile: str = DEFAULT_FEATURE_PROFILE,
) -> tuple[pd.DataFrame, list[str]]:
    feature_frame, feature_columns = build_feature_frame_from_close_series(
        close_series=close_series,
        lags=lags,
        feature_profile=feature_profile,
    )
    latest_features = feature_frame.dropna().tail(1).copy()
    if latest_features.empty:
        raise ValueError(
            f"Not enough rows to build features with {lags} lags. "
            f"At least {lags + 1} close values are required."
        )

    return latest_features, feature_columns


def build_next_close_dataset(
    data: pd.DataFrame,
    lags: int,
    feature_profile: str = DEFAULT_FEATURE_PROFILE,
) -> NextCloseDataset:
    close_series = data["Close"].astype(float)
    return_series = close_series.pct_change()
    feature_frame, feature_columns = build_feature_frame_from_close_series(
        close_series=close_series,
        lags=lags,
        feature_profile=feature_profile,
    )
    latest_features, _ = build_latest_feature_frame_from_close_series(
        close_series=close_series,
        lags=lags,
        feature_profile=feature_profile,
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
        feature_profile=feature_profile,
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
