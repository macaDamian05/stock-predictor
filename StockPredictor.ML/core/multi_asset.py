from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from .paths import sanitize_ticker
from .tabular_features import (
    DEFAULT_FEATURE_PROFILE,
    FEATURE_PROFILES,
    REFERENCE_COLUMN,
    RETURN_TARGET_COLUMN,
    TARGET_COLUMN,
    TARGET_DATE_COLUMN,
    build_latest_feature_frame_from_close_series,
    build_next_close_dataset,
)


TICKER_COLUMN = "ticker"
IDENTITY_PREFIX = "ticker_id_"


@dataclass(frozen=True)
class MultiAssetDataset:
    supervised_frame: pd.DataFrame
    feature_columns: list[str]
    base_feature_columns: list[str]
    identity_feature_columns: list[str]
    tickers: list[str]
    feature_profile: str = DEFAULT_FEATURE_PROFILE
    target_column: str = RETURN_TARGET_COLUMN
    close_target_column: str = TARGET_COLUMN
    target_date_column: str = TARGET_DATE_COLUMN
    reference_column: str = REFERENCE_COLUMN
    ticker_column: str = TICKER_COLUMN


def build_identity_feature_name(ticker: str) -> str:
    safe_ticker = sanitize_ticker(ticker).replace(".", "_").lower()
    return f"{IDENTITY_PREFIX}{safe_ticker}"


def attach_identity_features(
    feature_frame: pd.DataFrame,
    tickers: list[str],
    active_ticker: str,
) -> tuple[pd.DataFrame, list[str]]:
    if active_ticker not in tickers:
        raise ValueError(
            f"Ticker '{active_ticker}' is not part of the configured multi-asset universe."
        )

    enriched_frame = feature_frame.copy()
    identity_feature_columns: list[str] = []

    for ticker in tickers:
        column_name = build_identity_feature_name(ticker)
        enriched_frame[column_name] = 1.0 if ticker == active_ticker else 0.0
        identity_feature_columns.append(column_name)

    return enriched_frame, identity_feature_columns


def build_multi_asset_dataset(
    price_data_by_ticker: dict[str, pd.DataFrame],
    lags: int,
    feature_profile: str = DEFAULT_FEATURE_PROFILE,
) -> MultiAssetDataset:
    if not price_data_by_ticker:
        raise ValueError("price_data_by_ticker must not be empty.")
    if feature_profile not in FEATURE_PROFILES:
        raise ValueError(
            f"Unknown feature profile '{feature_profile}'. "
            f"Expected one of: {', '.join(FEATURE_PROFILES)}."
        )

    normalized_tickers = list(dict.fromkeys(ticker.upper() for ticker in price_data_by_ticker))
    supervised_frames: list[pd.DataFrame] = []
    base_feature_columns: list[str] | None = None
    identity_feature_columns: list[str] = []

    for ticker in normalized_tickers:
        dataset = build_next_close_dataset(
            data=price_data_by_ticker[ticker],
            lags=lags,
            feature_profile=feature_profile,
        )
        if base_feature_columns is None:
            base_feature_columns = list(dataset.feature_columns)
        elif list(dataset.feature_columns) != base_feature_columns:
            raise ValueError("Base feature columns differ across tickers.")

        supervised_frame = dataset.supervised_frame.copy()
        supervised_frame[TICKER_COLUMN] = ticker
        supervised_frame, identity_feature_columns = attach_identity_features(
            supervised_frame,
            tickers=normalized_tickers,
            active_ticker=ticker,
        )
        supervised_frames.append(supervised_frame)

    pooled_frame = pd.concat(supervised_frames, axis=0).sort_values(
        [TARGET_DATE_COLUMN, TICKER_COLUMN]
    )

    return MultiAssetDataset(
        supervised_frame=pooled_frame,
        feature_columns=[*(base_feature_columns or []), *identity_feature_columns],
        base_feature_columns=list(base_feature_columns or []),
        identity_feature_columns=identity_feature_columns,
        tickers=normalized_tickers,
        feature_profile=feature_profile,
    )


def build_multi_asset_latest_feature_frame(
    close_series: pd.Series,
    ticker: str,
    tickers: list[str],
    lags: int,
    feature_profile: str = DEFAULT_FEATURE_PROFILE,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    latest_features, base_feature_columns = build_latest_feature_frame_from_close_series(
        close_series=close_series,
        lags=lags,
        feature_profile=feature_profile,
    )
    enriched_features, identity_feature_columns = attach_identity_features(
        latest_features,
        tickers=tickers,
        active_ticker=ticker.upper(),
    )
    return enriched_features, base_feature_columns, identity_feature_columns


def chronological_train_test_split_by_target_date(
    frame: pd.DataFrame,
    target_date_column: str,
    test_size: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < test_size < 1:
        raise ValueError(f"test_size must be between 0 and 1, got {test_size}.")

    target_dates = pd.to_datetime(frame[target_date_column])
    unique_dates = pd.Index(sorted(target_dates.unique()))
    test_date_count = max(1, math.ceil(len(unique_dates) * test_size))
    train_date_count = len(unique_dates) - test_date_count

    if train_date_count < 1:
        raise ValueError(
            "Split leaves no training dates. "
            f"unique_dates={len(unique_dates)}, test_size={test_size}."
        )

    test_dates = set(unique_dates[-test_date_count:])
    test_mask = target_dates.isin(test_dates)
    train_frame = frame.loc[~test_mask].copy()
    test_frame = frame.loc[test_mask].copy()
    return train_frame, test_frame


def build_expanding_date_splits(
    frame: pd.DataFrame,
    target_date_column: str,
    initial_train_size: float,
    folds: int,
) -> list[tuple[int, pd.DataFrame, pd.DataFrame]]:
    if folds < 0:
        raise ValueError(f"walk_forward_folds must be non-negative, got {folds}.")
    if folds == 0:
        return []
    if not 0 < initial_train_size < 1:
        raise ValueError(
            "walk_forward_train_size must be between 0 and 1, "
            f"got {initial_train_size}."
        )

    target_dates = pd.to_datetime(frame[target_date_column])
    unique_dates = pd.Index(sorted(target_dates.unique()))
    initial_train_dates = max(1, math.ceil(len(unique_dates) * initial_train_size))
    remaining_dates = len(unique_dates) - initial_train_dates

    if remaining_dates < folds:
        raise ValueError(
            "Walk-forward split leaves too few dates for the requested number of folds. "
            f"unique_dates={len(unique_dates)}, initial_train_dates={initial_train_dates}, folds={folds}."
        )

    base_test_dates = remaining_dates // folds
    extra_dates = remaining_dates % folds
    splits: list[tuple[int, pd.DataFrame, pd.DataFrame]] = []
    test_start = initial_train_dates

    for fold_index in range(1, folds + 1):
        test_date_count = base_test_dates + (1 if fold_index <= extra_dates else 0)
        test_end = test_start + test_date_count
        train_dates = set(unique_dates[:test_start])
        test_dates = set(unique_dates[test_start:test_end])

        train_frame = frame.loc[target_dates.isin(train_dates)].copy()
        test_frame = frame.loc[target_dates.isin(test_dates)].copy()
        splits.append((fold_index, train_frame, test_frame))
        test_start = test_end

    return splits
