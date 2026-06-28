from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.dashboard_export import export_core_dashboard_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the stable core dashboard payload from saved model registries."
    )
    parser.add_argument("--symbols", nargs="*", default=None)
    parser.add_argument("--horizon", type=int, default=None)
    parser.add_argument("--run-name", default="LATEST")
    parser.add_argument("--stale-after-days", type=int, default=5)
    parser.add_argument(
        "--no-refresh-missing-predictions",
        action="store_true",
        help="Do not create missing predictions from saved models during export.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = export_core_dashboard_payload(
        symbols=args.symbols,
        horizon=args.horizon,
        run_name=args.run_name,
        stale_after_days=args.stale_after_days,
        refresh_missing_predictions=not args.no_refresh_missing_predictions,
    )
    print(
        "Exported core dashboard payload with "
        f"{len(payload.get('featured_tickers', []))} featured tickers."
    )


if __name__ == "__main__":
    main()
