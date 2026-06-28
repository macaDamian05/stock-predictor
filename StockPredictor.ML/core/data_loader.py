from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yfinance as yf

from .paths import STORAGE_DIR, get_market_data_artifact_paths


def _normalize_price_frame(frame: pd.DataFrame, source_label: str) -> pd.DataFrame:
    normalized = frame.copy()

    if isinstance(normalized.columns, pd.MultiIndex):
        normalized.columns = [
            column[0] if isinstance(column, tuple) else column
            for column in normalized.columns.to_flat_index()
        ]

    if "Close" not in normalized.columns:
        raise ValueError(f"Price data from '{source_label}' does not contain a 'Close' column.")

    normalized = normalized.sort_index()
    normalized = normalized[~normalized.index.duplicated(keep="last")]
    normalized = normalized.dropna(subset=["Close"])

    if normalized.empty:
        raise ValueError(f"All close prices from '{source_label}' are empty after cleanup.")

    return normalized


def download_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    local_cache_dir = STORAGE_DIR / "yfinance-cache"
    local_cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(local_cache_dir))

    raw_data = yf.download(
        tickers=ticker,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False,
        group_by="column",
    )

    if raw_data.empty:
        raise ValueError(
            f"No market data returned for ticker '{ticker}' between {start_date} and {end_date}."
        )

    return _normalize_price_frame(raw_data, source_label=ticker)


def download_intraday_price_data(
    ticker: str,
    period: str = "5d",
    interval: str = "15m",
) -> pd.DataFrame:
    local_cache_dir = STORAGE_DIR / "yfinance-cache"
    local_cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(local_cache_dir))

    raw_data = yf.download(
        tickers=ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        group_by="column",
    )

    if raw_data.empty:
        raise ValueError(
            f"No intraday market data returned for ticker '{ticker}' with period={period} and interval={interval}."
        )

    return _normalize_price_frame(raw_data, source_label=f"{ticker}:{period}:{interval}")


def load_price_data_from_csv(
    csv_path: str | Path,
    date_column: str = "Date",
    close_column: str = "Close",
) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    frame = pd.read_csv(path)
    if date_column not in frame.columns:
        raise ValueError(f"CSV file '{path}' does not contain the date column '{date_column}'.")
    if close_column not in frame.columns:
        raise ValueError(f"CSV file '{path}' does not contain the close column '{close_column}'.")

    frame = frame.copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="raise")
    frame = frame.set_index(date_column)
    if close_column != "Close":
        frame = frame.rename(columns={close_column: "Close"})

    if "Close" in frame.columns:
        frame["Close"] = pd.to_numeric(frame["Close"], errors="coerce")

    return _normalize_price_frame(frame, source_label=str(path))


def load_price_data_from_market_snapshot(
    ticker: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    paths = get_market_data_artifact_paths(ticker)
    if not paths.snapshot_json.exists():
        raise FileNotFoundError(
            f"Local market snapshot not found for '{ticker}': {paths.snapshot_json}"
        )

    payload = json.loads(paths.snapshot_json.read_text(encoding="utf-8"))
    daily_points = payload.get("daily_points") or []
    if not daily_points:
        raise ValueError(f"Local market snapshot for '{ticker}' does not contain daily points.")

    frame = pd.DataFrame(daily_points)
    if "timestamp" not in frame.columns or "close" not in frame.columns:
        raise ValueError(
            f"Local market snapshot for '{ticker}' must contain timestamp and close fields."
        )

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="raise")
    frame = frame.set_index("timestamp")
    frame = frame.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    for column in ["Open", "High", "Low", "Close", "Volume"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if start_date:
        frame = frame.loc[frame.index >= pd.Timestamp(start_date)]
    if end_date:
        frame = frame.loc[frame.index <= pd.Timestamp(end_date)]

    return _normalize_price_frame(frame, source_label=f"market_snapshot:{ticker}")


def load_price_data_for_symbol(
    ticker: str,
    start_date: str,
    end_date: str | None = None,
    prefer_cached_snapshot: bool = True,
) -> pd.DataFrame:
    resolved_end_date = end_date or pd.Timestamp.today().date().isoformat()

    if prefer_cached_snapshot:
        try:
            return load_price_data_from_market_snapshot(
                ticker,
                start_date=start_date,
                end_date=resolved_end_date,
            )
        except (FileNotFoundError, ValueError):
            pass

    try:
        return download_price_data(ticker, start_date=start_date, end_date=resolved_end_date)
    except Exception:
        if prefer_cached_snapshot:
            raise

        return load_price_data_from_market_snapshot(
            ticker,
            start_date=start_date,
            end_date=resolved_end_date,
        )
