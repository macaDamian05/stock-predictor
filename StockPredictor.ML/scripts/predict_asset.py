from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.prediction_service import predict_saved_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a forecast from already trained core models without retraining."
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--start-date", default="1990-01-01")
    parser.add_argument("--end-date", default=None)
    parser.add_argument(
        "--refresh-market-data",
        action="store_true",
        help="Prefer a fresh yfinance download before falling back to local market snapshots.",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Print the prediction without updating storage/predictions.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = predict_saved_model(
        symbol=args.symbol,
        horizon=args.horizon,
        start_date=args.start_date,
        end_date=args.end_date,
        prefer_cached_market_data=not args.refresh_market_data,
        persist=not args.no_persist,
    )
    payload = asdict(result)
    if payload.get("path") is not None:
        payload["path"] = str(payload["path"])
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
