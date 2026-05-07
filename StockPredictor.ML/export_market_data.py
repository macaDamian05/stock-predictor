from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from core.data_loader import download_intraday_price_data, download_price_data
from core.paths import ensure_runtime_directories, get_market_data_artifact_paths


DEFAULT_START_DATE = "1990-01-01"
DEFAULT_CACHE_FRESH_MINUTES = 30
DEFAULT_INTRADAY_PERIOD = "5d"
DEFAULT_INTRADAY_INTERVAL = "15m"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export local market data snapshots for one or more tickers."
    )
    parser.add_argument(
        "tickers",
        nargs="+",
        help="Ticker symbols to export, for example AAPL TSLA MSFT ENR.DE.",
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
        help="Historical daily download start date.",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="Historical daily download end date. Defaults to today.",
    )
    parser.add_argument(
        "--intraday-period",
        default=DEFAULT_INTRADAY_PERIOD,
        help="Intraday lookback period passed to yfinance, for example 5d.",
    )
    parser.add_argument(
        "--intraday-interval",
        default=DEFAULT_INTRADAY_INTERVAL,
        help="Intraday interval passed to yfinance, for example 15m.",
    )
    parser.add_argument(
        "--use-cache-if-fresh-minutes",
        type=int,
        default=DEFAULT_CACHE_FRESH_MINUTES,
        help="Use an existing local market snapshot when it is fresh enough.",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore cache freshness and fetch market data again.",
    )
    return parser.parse_args()


def is_cache_fresh(snapshot_path: Path, fresh_minutes: int) -> bool:
    if not snapshot_path.exists() or fresh_minutes < 0:
        return False

    modified_at = datetime.fromtimestamp(snapshot_path.stat().st_mtime)
    return modified_at >= datetime.now() - timedelta(minutes=fresh_minutes)


def load_snapshot(snapshot_path: Path) -> dict[str, Any] | None:
    if not snapshot_path.exists():
        return None

    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def normalize_timestamp(value: pd.Timestamp) -> str:
    if value.tzinfo is not None:
        value = value.tz_convert(None)
    return value.isoformat(timespec="minutes")


def frame_to_price_points(frame: pd.DataFrame) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []

    for timestamp, row in frame.iterrows():
        point_timestamp = pd.Timestamp(timestamp)
        if point_timestamp.tzinfo is not None:
            point_timestamp = point_timestamp.tz_convert(None)

        points.append(
            {
                "timestamp": normalize_timestamp(point_timestamp),
                "open": float(row["Open"]) if "Open" in row and pd.notna(row["Open"]) else None,
                "high": float(row["High"]) if "High" in row and pd.notna(row["High"]) else None,
                "low": float(row["Low"]) if "Low" in row and pd.notna(row["Low"]) else None,
                "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
                "volume": float(row["Volume"]) if "Volume" in row and pd.notna(row["Volume"]) else None,
            }
        )

    return points


def build_market_snapshot(
    ticker: str,
    daily_frame: pd.DataFrame,
    intraday_frame: pd.DataFrame | None,
) -> dict[str, Any]:
    daily_frame = daily_frame.sort_index()
    intraday_points = frame_to_price_points(intraday_frame.sort_index()) if intraday_frame is not None else []

    return {
        "ticker": ticker,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ok",
        "warning": None,
        "error": None,
        "daily_data_until": normalize_timestamp(pd.Timestamp(daily_frame.index[-1])),
        "intraday_data_until": (
            normalize_timestamp(pd.Timestamp(intraday_frame.index[-1]))
            if intraday_frame is not None and not intraday_frame.empty
            else None
        ),
        "daily_points": frame_to_price_points(daily_frame),
        "intraday_points": intraday_points,
    }


def fetch_market_snapshot(args: argparse.Namespace, ticker: str) -> dict[str, Any]:
    end_date = args.end_date or pd.Timestamp.today().date().isoformat()
    daily_frame = download_price_data(
        ticker=ticker,
        start_date=args.start_date,
        end_date=end_date,
    )

    intraday_frame: pd.DataFrame | None
    try:
        intraday_frame = download_intraday_price_data(
            ticker=ticker,
            period=args.intraday_period,
            interval=args.intraday_interval,
        )
    except Exception:
        intraday_frame = None

    return build_market_snapshot(
        ticker=ticker,
        daily_frame=daily_frame,
        intraday_frame=intraday_frame,
    )


def resolve_ticker_snapshot(args: argparse.Namespace, ticker: str) -> dict[str, Any]:
    artifacts = get_market_data_artifact_paths(ticker)
    normalized_ticker = ticker.upper()

    if not args.force_refresh and is_cache_fresh(
        artifacts.snapshot_json,
        args.use_cache_if_fresh_minutes,
    ):
        cached_snapshot = load_snapshot(artifacts.snapshot_json)
        if cached_snapshot is not None:
            cached_snapshot["status"] = "cached"
            return cached_snapshot

    try:
        snapshot = fetch_market_snapshot(args, normalized_ticker)
        artifacts.snapshot_json.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        return snapshot
    except Exception as exception:
        cached_snapshot = load_snapshot(artifacts.snapshot_json)
        if cached_snapshot is not None:
            cached_snapshot["status"] = "cached_error_fallback"
            cached_snapshot["warning"] = (
                "Frische Marktdaten konnten nicht geladen werden. "
                "Die App verwendet den zuletzt lokal gespeicherten Snapshot."
            )
            cached_snapshot["error"] = str(exception)
            return cached_snapshot

        return {
            "ticker": normalized_ticker,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status": "error",
            "warning": None,
            "error": str(exception),
            "daily_data_until": None,
            "intraday_data_until": None,
            "daily_points": [],
            "intraday_points": [],
        }


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    results = [resolve_ticker_snapshot(args, ticker.strip().upper()) for ticker in args.tickers if ticker.strip()]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "result_count": len(results),
        "results": results,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
