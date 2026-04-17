from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.paths import (
    ensure_runtime_directories,
    get_classical_artifact_paths,
    get_dashboard_artifact_paths,
    get_thesis_artifact_paths,
)


DEFAULT_DASHBOARD_RUN = "latest"
DEFAULT_THESIS_RUN = "BACHELOR_THESIS_RESULTS"
DEFAULT_TICKERS = ["AAPL", "TSLA", "DOU.DE"]
PROFILE_DISPLAY_NAMES = {
    "lag_only": "Lag Only",
    "technical_basic": "Technical Basic",
    "technical_extended": "Technical Extended",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a UI-friendly dashboard payload from ML and thesis artifacts."
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Featured tickers for the dashboard payload. Defaults to AAPL TSLA DOU.DE.",
    )
    parser.add_argument(
        "--thesis-run",
        default=DEFAULT_THESIS_RUN,
        help="Thesis artifact run folder below storage/thesis/.",
    )
    parser.add_argument(
        "--run-name",
        default=DEFAULT_DASHBOARD_RUN,
        help="Output folder name below storage/dashboard/.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Required artifact file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def infer_feature_profile(metadata_payload: dict[str, object]) -> str:
    feature_columns = metadata_payload.get("feature_columns") or []
    feature_column_set = set(feature_columns)

    if {
        "ema_5_gap",
        "breakout_20_gap",
        "drawdown_20_gap",
        "price_zscore_20",
    }.intersection(feature_column_set):
        return "technical_extended"

    if {
        "return_mean_5",
        "sma_5_gap",
        "volatility_5",
        "momentum_5",
        "rsi_14",
    }.intersection(feature_column_set):
        return "technical_basic"

    return "lag_only"


def build_featured_ticker_record(ticker: str) -> dict[str, object]:
    artifacts = get_classical_artifact_paths(ticker)
    summary_payload = load_json(artifacts.summary)
    metadata_payload = load_json(artifacts.metadata)
    forecast_payload = load_json(artifacts.forecast)

    forecast_path = forecast_payload["forecast_path"]
    next_step = forecast_path[0]
    final_step = forecast_path[-1]
    last_close = float(summary_payload["last_close"])
    next_close = float(next_step["predicted_close"])
    final_close = float(final_step["predicted_close"])
    walk_forward_overall = summary_payload["metrics"]["walk_forward"]["overall"]
    walk_forward_best_model = summary_payload["walk_forward_best_model"]
    feature_profile = summary_payload.get("feature_profile") or metadata_payload.get("feature_profile")
    if not feature_profile:
        feature_profile = infer_feature_profile(metadata_payload)

    return {
        "ticker": ticker,
        "forecast_model": summary_payload["forecast_model"],
        "forecast_model_label": forecast_payload["forecast_model_label"],
        "last_close_date": forecast_payload["last_close_date"],
        "last_close": last_close,
        "next_forecast_date": next_step["date"],
        "next_predicted_close": next_close,
        "next_predicted_change_pct": ((next_close / last_close) - 1.0) * 100.0,
        "forecast_end_date": final_step["date"],
        "forecast_end_close": final_close,
        "forecast_horizon_change_pct": ((final_close / last_close) - 1.0) * 100.0,
        "forecast_days": int(summary_payload["forecast_days"]),
        "average_recent_rsi": summary_payload["average_recent_rsi"],
        "average_forecast_slope": summary_payload["average_forecast_slope"],
        "feature_profile": feature_profile,
        "feature_profile_label": PROFILE_DISPLAY_NAMES[feature_profile],
        "holdout_best_model": summary_payload["holdout_best_model"],
        "walk_forward_best_model": walk_forward_best_model,
        "walk_forward_best_rmse": walk_forward_overall[walk_forward_best_model]["rmse"],
        "walk_forward_baseline_rmse": walk_forward_overall["baseline_persistence"]["rmse"],
        "walk_forward_best_directional_accuracy": walk_forward_overall[walk_forward_best_model][
            "directional_accuracy"
        ],
        "beats_baseline_rmse": walk_forward_overall[walk_forward_best_model]["rmse"]
        < walk_forward_overall["baseline_persistence"]["rmse"],
        "data_start": metadata_payload["data_start"],
        "data_end": metadata_payload["data_end"],
        "forecast_path": forecast_path,
    }


def build_basket_summary_records(thesis_payload: dict[str, object]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    basket_configs = [
        (
            "core",
            "Bachelor Core",
            thesis_payload["headline_findings"]["core_best_profile"],
            thesis_payload["headline_findings"]["core_tickers_where_technical_extended_is_better"],
            thesis_payload["headline_findings"]["core_tickers_where_lag_only_is_better"],
        ),
        (
            "diversified",
            "Bachelor Diversified",
            thesis_payload["headline_findings"]["diversified_best_profile"],
            thesis_payload["headline_findings"]["diversified_tickers_where_technical_extended_is_better"],
            thesis_payload["headline_findings"]["diversified_tickers_where_lag_only_is_better"],
        ),
    ]

    for basket_key, basket_label, best_profile, technical_better, lag_better in basket_configs:
        records.append(
            {
                "basket_key": basket_key,
                "basket_label": basket_label,
                "best_profile": best_profile["feature_profile"],
                "best_profile_label": best_profile["feature_profile_label"],
                "mean_best_learned_rmse": best_profile["mean_best_learned_rmse"],
                "mean_walk_forward_baseline_rmse": best_profile["mean_walk_forward_baseline_rmse"],
                "mean_gap_vs_baseline": best_profile["mean_best_learned_minus_baseline_rmse"],
                "dominant_best_model": best_profile["dominant_best_model"],
                "dominant_best_model_label": best_profile["dominant_best_model_label"],
                "technical_extended_better_count": len(technical_better),
                "lag_only_better_count": len(lag_better),
                "technical_extended_better_tickers": technical_better,
                "lag_only_better_tickers": lag_better,
            }
        )

    return records


def build_payload(
    thesis_payload: dict[str, object],
    featured_records: list[dict[str, object]],
    basket_summary_records: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "ui_contract_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_runs": {
            "thesis_run": thesis_payload["run_name"],
            **thesis_payload["source_runs"],
        },
        "summary_cards": {
            "starter_best_experiment": thesis_payload["headline_findings"]["starter_best_experiment"],
            "starter_tickers_beating_baseline": thesis_payload["headline_findings"][
                "starter_tickers_beating_baseline"
            ],
            "best_core_profile": thesis_payload["headline_findings"]["core_best_profile"],
            "best_diversified_profile": thesis_payload["headline_findings"]["diversified_best_profile"],
        },
        "featured_tickers": featured_records,
        "basket_summaries": basket_summary_records,
        "notes": [
            "Die naive Persistence-Baseline bleibt ein wichtiger Referenzwert.",
            "technical_extended liegt im Mittel leicht vor lag_only, aber der Vorteil ist klein.",
            "Die besten Modelltypen wechseln je nach Ticker.",
        ],
    }


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    tickers = [ticker.upper() for ticker in (args.tickers or DEFAULT_TICKERS)]
    thesis_artifacts = get_thesis_artifact_paths(args.thesis_run)
    thesis_payload = load_json(thesis_artifacts.summary_json)
    featured_records = [build_featured_ticker_record(ticker) for ticker in tickers]
    basket_summary_records = build_basket_summary_records(thesis_payload)

    artifacts = get_dashboard_artifact_paths(args.run_name)
    featured_frame = pd.DataFrame(featured_records).drop(columns=["forecast_path"])
    basket_summary_frame = pd.DataFrame(basket_summary_records).drop(
        columns=["technical_extended_better_tickers", "lag_only_better_tickers"]
    )

    featured_frame.to_csv(artifacts.featured_tickers_csv, index=False)
    basket_summary_frame.to_csv(artifacts.basket_summary_csv, index=False)

    payload = build_payload(
        thesis_payload=thesis_payload,
        featured_records=featured_records,
        basket_summary_records=basket_summary_records,
    )
    artifacts.payload_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Dashboard payload run: {args.run_name}")
    print(f"Featured tickers: {', '.join(tickers)}")
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
