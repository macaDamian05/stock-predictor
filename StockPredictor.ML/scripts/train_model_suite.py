from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.orchestrator import CoreModelOrchestrator, CoreTrainingConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the stable core model suite for one or more symbols."
    )
    parser.add_argument("--symbols", nargs="+", required=True, help="Ticker symbols to train.")
    parser.add_argument("--horizon", type=int, default=5, help="Forecast horizon in business days.")
    parser.add_argument("--lags", type=int, default=10, help="Return lag count for feature engineering.")
    parser.add_argument(
        "--feature-profile",
        default="technical_extended",
        choices=["lag_only", "technical_basic", "technical_extended"],
    )
    parser.add_argument("--validation-size", type=float, default=0.2)
    parser.add_argument("--start-date", default="1990-01-01")
    parser.add_argument("--end-date", default=None)
    parser.add_argument(
        "--refresh-market-data",
        action="store_true",
        help="Prefer a fresh yfinance download before falling back to local market snapshots.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = CoreTrainingConfig(
        horizon=args.horizon,
        lags=args.lags,
        feature_profile=args.feature_profile,
        validation_size=args.validation_size,
        start_date=args.start_date,
        end_date=args.end_date,
        prefer_cached_market_data=not args.refresh_market_data,
    )
    orchestrator = CoreModelOrchestrator(config)
    results = []
    failures = []

    for symbol in args.symbols:
        try:
            results.append(orchestrator.train_symbol(symbol))
        except Exception as exception:
            failures.append((symbol, str(exception)))

    for result in results:
        print(
            f"{result.symbol}: selected={result.selected_model_key} "
            f"registry={result.registry_path} prediction={result.prediction_path}"
        )

    for symbol, message in failures:
        print(f"{symbol}: failed={message}", file=sys.stderr)

    if not results:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
