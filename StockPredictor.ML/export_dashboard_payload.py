from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.paths import (
    ensure_runtime_directories,
    get_artifact_paths,
    get_classical_artifact_paths,
    get_dashboard_artifact_paths,
    get_multi_asset_suite_artifact_paths,
    get_thesis_artifact_paths,
)
from core.predictor import average_distance_pct_to_reference, average_distance_to_reference


DEFAULT_DASHBOARD_RUN = "latest"
DEFAULT_THESIS_RUN = "BACHELOR_THESIS_RESULTS"
DEFAULT_MULTI_ASSET_SUITE_RUN = "latest"
DEFAULT_TICKERS = ["AAPL", "TSLA", "DOU.DE"]
DEFAULT_STALE_AFTER_DAYS = 3
PROFILE_DISPLAY_NAMES = {
    "lag_only": "Lag Only",
    "technical_basic": "Technical Basic",
    "technical_extended": "Technical Extended",
}
MODEL_DISPLAY_NAMES = {
    "baseline_persistence": "Persistence-Baseline",
    "ridge_regression": "Ridge Regression",
    "decision_tree": "Decision Tree",
    "random_forest": "Random Forest",
    "lstm": "LSTM",
}
MULTI_ASSET_BASKET_DISPLAY_NAMES = {
    "starter": "Starter Basket",
    "bachelor_core": "Bachelor Core",
    "bachelor_diversified": "Bachelor Diversified",
    "etf_core": "ETF Core",
    "etf_sectors": "ETF Sectors",
    "mixed_assets": "Mixed Assets",
}
MODEL_DISPLAY_ORDER = [
    "baseline_persistence",
    "ridge_regression",
    "decision_tree",
    "random_forest",
    "lstm",
]
COMPANY_RANKING_WEIGHTS = {
    "forecast_horizon_change_pct": 0.45,
    "walk_forward_best_directional_accuracy": 0.25,
    "relative_rmse_pct": 0.20,
    "relative_gap_vs_baseline_pct": 0.10,
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
    parser.add_argument(
        "--multi-asset-suite-run",
        default=DEFAULT_MULTI_ASSET_SUITE_RUN,
        help="Optional multi-asset suite run folder below storage/multi_asset_suites/.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Required artifact file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def try_load_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
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


def format_model_label(model_key: str) -> str:
    return MODEL_DISPLAY_NAMES.get(model_key, model_key.replace("_", " ").title())


def get_artifact_timestamp(*paths: Path) -> str:
    existing_paths = [path for path in paths if path.exists()]
    if not existing_paths:
        return datetime.now().isoformat(timespec="seconds")

    latest_mtime = max(path.stat().st_mtime for path in existing_paths)
    return datetime.fromtimestamp(latest_mtime).isoformat(timespec="seconds")


def build_selected_model_record(model_key: str) -> dict[str, object]:
    return {
        "model_key": model_key,
        "model_label": format_model_label(model_key),
    }


def try_build_lstm_model_metric_record(ticker: str) -> dict[str, object] | None:
    lstm_artifacts = get_artifact_paths(ticker)
    if not all(path.exists() for path in (lstm_artifacts.model, lstm_artifacts.scaler, lstm_artifacts.metadata)):
        return None

    lstm_metadata = try_load_json(lstm_artifacts.metadata) or {}

    return {
        "model_key": "lstm",
        "model_label": "LSTM",
        "is_selected": False,
        "has_next_step_prediction": False,
        "next_predicted_close": None,
        "next_predicted_change_pct": None,
        "holdout_mae": None,
        "holdout_rmse": None,
        "holdout_directional_accuracy": None,
        "walk_forward_mae": None,
        "walk_forward_rmse": None,
        "walk_forward_directional_accuracy": None,
        "walk_forward_rmse_gap_vs_baseline": None,
        "walk_forward_mae_gap_vs_baseline": None,
        "walk_forward_directional_accuracy_gap_vs_baseline": None,
        "metadata_available": True,
        "notes": "LSTM-Artefakte lokal vorhanden, aber nicht im klassischen Modellvergleich ausgewertet.",
        "data_until": lstm_metadata.get("last_data_date"),
    }


def build_model_metric_records(
    ticker: str,
    summary_payload: dict[str, object],
    last_close: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    holdout_metrics = summary_payload.get("metrics", {}).get("holdout", {})
    walk_forward_overall = summary_payload.get("metrics", {}).get("walk_forward", {}).get("overall", {})
    model_predictions = summary_payload.get("next_forecast", {}).get("model_predictions", {})
    selected_model_key = str(summary_payload["forecast_model"])

    available_model_keys = {
        *holdout_metrics.keys(),
        *walk_forward_overall.keys(),
        *model_predictions.keys(),
        selected_model_key,
    }
    ordered_model_keys = [
        model_key
        for model_key in MODEL_DISPLAY_ORDER
        if model_key in available_model_keys
    ]
    remaining_model_keys = sorted(available_model_keys.difference(ordered_model_keys))

    baseline_holdout = holdout_metrics.get("baseline_persistence", {})
    baseline_walk_forward = walk_forward_overall.get("baseline_persistence", {})

    available_models = []
    model_metrics = []

    for model_key in [*ordered_model_keys, *remaining_model_keys]:
        holdout_entry = holdout_metrics.get(model_key, {})
        walk_forward_entry = walk_forward_overall.get(model_key, {})
        prediction_entry = model_predictions.get(model_key, {})
        predicted_close = prediction_entry.get("predicted_close")
        predicted_return = prediction_entry.get("predicted_return")

        available_models.append(build_selected_model_record(model_key))
        model_metrics.append(
            {
                "model_key": model_key,
                "model_label": format_model_label(model_key),
                "is_selected": model_key == selected_model_key,
                "has_next_step_prediction": predicted_close is not None,
                "next_predicted_close": predicted_close,
                "next_predicted_change_pct": (
                    ((float(predicted_close) / last_close) - 1.0) * 100.0
                    if predicted_close is not None
                    else (
                        float(predicted_return) * 100.0 if predicted_return is not None else None
                    )
                ),
                "holdout_mae": holdout_entry.get("mae"),
                "holdout_rmse": holdout_entry.get("rmse"),
                "holdout_directional_accuracy": holdout_entry.get("directional_accuracy"),
                "walk_forward_mae": walk_forward_entry.get("mae"),
                "walk_forward_rmse": walk_forward_entry.get("rmse"),
                "walk_forward_directional_accuracy": walk_forward_entry.get("directional_accuracy"),
                "walk_forward_rmse_gap_vs_baseline": (
                    None
                    if walk_forward_entry.get("rmse") is None or baseline_walk_forward.get("rmse") is None
                    else float(walk_forward_entry["rmse"]) - float(baseline_walk_forward["rmse"])
                ),
                "walk_forward_mae_gap_vs_baseline": (
                    None
                    if walk_forward_entry.get("mae") is None or baseline_walk_forward.get("mae") is None
                    else float(walk_forward_entry["mae"]) - float(baseline_walk_forward["mae"])
                ),
                "walk_forward_directional_accuracy_gap_vs_baseline": (
                    None
                    if walk_forward_entry.get("directional_accuracy") is None
                    or baseline_walk_forward.get("directional_accuracy") is None
                    else float(walk_forward_entry["directional_accuracy"])
                    - float(baseline_walk_forward["directional_accuracy"])
                ),
                "holdout_rmse_gap_vs_baseline": (
                    None
                    if holdout_entry.get("rmse") is None or baseline_holdout.get("rmse") is None
                    else float(holdout_entry["rmse"]) - float(baseline_holdout["rmse"])
                ),
                "holdout_mae_gap_vs_baseline": (
                    None
                    if holdout_entry.get("mae") is None or baseline_holdout.get("mae") is None
                    else float(holdout_entry["mae"]) - float(baseline_holdout["mae"])
                ),
            }
        )

    lstm_metric_record = try_build_lstm_model_metric_record(ticker)
    if lstm_metric_record:
        available_models.append(build_selected_model_record("lstm"))
        model_metrics.append(lstm_metric_record)

    return available_models, model_metrics


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
    forecast_prices = [float(point["predicted_close"]) for point in forecast_path]
    walk_forward_overall = summary_payload["metrics"]["walk_forward"]["overall"]
    walk_forward_best_model = summary_payload["walk_forward_best_model"]
    feature_profile = summary_payload.get("feature_profile") or metadata_payload.get("feature_profile")
    if not feature_profile:
        feature_profile = infer_feature_profile(metadata_payload)
    average_forecast_distance_to_last_close = summary_payload.get(
        "average_forecast_distance_to_last_close"
    )
    if average_forecast_distance_to_last_close is None:
        average_forecast_distance_to_last_close = average_distance_to_reference(
            forecast_prices,
            reference_value=last_close,
        )
    average_forecast_distance_pct_to_last_close = summary_payload.get(
        "average_forecast_distance_pct_to_last_close"
    )
    if average_forecast_distance_pct_to_last_close is None:
        average_forecast_distance_pct_to_last_close = average_distance_pct_to_reference(
            forecast_prices,
            reference_value=last_close,
        )
    available_models, model_metrics = build_model_metric_records(
        ticker=ticker,
        summary_payload=summary_payload,
        last_close=last_close,
    )
    forecast_generated_at = get_artifact_timestamp(
        artifacts.summary,
        artifacts.forecast,
        artifacts.metadata,
        artifacts.metrics,
        artifacts.walk_forward_metrics,
    )
    data_until = metadata_payload.get("data_end") or forecast_payload["last_close_date"]

    return {
        "ticker": ticker,
        "forecast_generated_at": forecast_generated_at,
        "data_until": data_until,
        "forecast_model": summary_payload["forecast_model"],
        "forecast_model_label": forecast_payload["forecast_model_label"],
        "selected_model": build_selected_model_record(summary_payload["forecast_model"]),
        "available_models": available_models,
        "model_metrics": model_metrics,
        "last_close_date": forecast_payload["last_close_date"],
        "last_close": last_close,
        "next_forecast_date": next_step["date"],
        "next_predicted_close": next_close,
        "next_predicted_change_pct": ((next_close / last_close) - 1.0) * 100.0,
        "forecast_end_date": final_step["date"],
        "forecast_end_close": final_close,
        "forecast_horizon_change_pct": ((final_close / last_close) - 1.0) * 100.0,
        "forecast_days": int(summary_payload["forecast_days"]),
        "forecast_horizon_days": int(summary_payload["forecast_days"]),
        "average_recent_rsi": summary_payload["average_recent_rsi"],
        "average_forecast_slope": summary_payload["average_forecast_slope"],
        "average_forecast_distance_to_last_close": average_forecast_distance_to_last_close,
        "average_forecast_distance_pct_to_last_close": average_forecast_distance_pct_to_last_close,
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


def normalize_metric(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0.0)
    minimum = float(numeric.min())
    maximum = float(numeric.max())

    if abs(maximum - minimum) < 1e-12:
        normalized = pd.Series(1.0, index=numeric.index, dtype=float)
    else:
        normalized = (numeric - minimum) / (maximum - minimum)

    return normalized if higher_is_better else 1.0 - normalized


def build_company_ranking_records(featured_records: list[dict[str, object]]) -> list[dict[str, object]]:
    ranking_frame = pd.DataFrame(featured_records).copy()
    if ranking_frame.empty:
        return []

    ranking_frame["relative_rmse_pct"] = (
        ranking_frame["walk_forward_best_rmse"] / ranking_frame["last_close"]
    ) * 100.0
    ranking_frame["relative_gap_vs_baseline_pct"] = (
        (ranking_frame["walk_forward_best_rmse"] - ranking_frame["walk_forward_baseline_rmse"])
        / ranking_frame["last_close"]
    ) * 100.0

    ranking_frame["forecast_component"] = normalize_metric(
        ranking_frame["forecast_horizon_change_pct"],
        higher_is_better=True,
    )
    ranking_frame["direction_component"] = normalize_metric(
        ranking_frame["walk_forward_best_directional_accuracy"],
        higher_is_better=True,
    )
    ranking_frame["rmse_component"] = normalize_metric(
        ranking_frame["relative_rmse_pct"],
        higher_is_better=False,
    )
    ranking_frame["baseline_component"] = normalize_metric(
        ranking_frame["relative_gap_vs_baseline_pct"],
        higher_is_better=False,
    )

    ranking_frame["ranking_score"] = (
        ranking_frame["forecast_component"] * COMPANY_RANKING_WEIGHTS["forecast_horizon_change_pct"]
        + ranking_frame["direction_component"]
        * COMPANY_RANKING_WEIGHTS["walk_forward_best_directional_accuracy"]
        + ranking_frame["rmse_component"] * COMPANY_RANKING_WEIGHTS["relative_rmse_pct"]
        + ranking_frame["baseline_component"] * COMPANY_RANKING_WEIGHTS["relative_gap_vs_baseline_pct"]
    ) * 100.0

    ranking_frame = ranking_frame.sort_values(
        by=[
            "ranking_score",
            "forecast_horizon_change_pct",
            "walk_forward_best_directional_accuracy",
        ],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    ranking_frame["rank"] = ranking_frame.index + 1

    columns = [
        "rank",
        "ticker",
        "ranking_score",
        "forecast_model",
        "forecast_model_label",
        "feature_profile",
        "feature_profile_label",
        "last_close",
        "next_predicted_change_pct",
        "forecast_horizon_change_pct",
        "average_forecast_distance_to_last_close",
        "average_forecast_distance_pct_to_last_close",
        "walk_forward_best_directional_accuracy",
        "walk_forward_best_rmse",
        "walk_forward_baseline_rmse",
        "relative_rmse_pct",
        "relative_gap_vs_baseline_pct",
        "average_recent_rsi",
        "beats_baseline_rmse",
    ]
    return ranking_frame[columns].to_dict(orient="records")


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


def build_multi_asset_summary_records(
    multi_asset_suite_payload: dict[str, object] | None,
) -> list[dict[str, object]]:
    if not multi_asset_suite_payload:
        return []

    summary_records = []
    for record in multi_asset_suite_payload.get("basket_best_configs", []):
        tickers = str(record.get("tickers", "")).split(",")
        summary_records.append(
            {
                "basket_preset": record["basket_preset"],
                "basket_label": MULTI_ASSET_BASKET_DISPLAY_NAMES.get(
                    record["basket_preset"],
                    record["basket_preset"].replace("_", " ").title(),
                ),
                "experiment_id": record["experiment_id"],
                "feature_profile": record["feature_profile"],
                "feature_profile_label": PROFILE_DISPLAY_NAMES[record["feature_profile"]],
                "lags": int(record["lags"]),
                "shared_model_name": record["shared_model_name"],
                "shared_model_label": record["shared_model_label"],
                "shared_model_rmse": record["shared_model_rmse"],
                "baseline_rmse": record["baseline_rmse"],
                "shared_model_minus_baseline_rmse": record["shared_model_minus_baseline_rmse"],
                "shared_model_directional_accuracy": record["shared_model_directional_accuracy"],
                "ticker_count": int(record["ticker_count"]),
                "mean_forecast_horizon_change_pct": record["mean_forecast_horizon_change_pct"],
                "mean_average_forecast_distance_pct_to_last_close": record[
                    "mean_average_forecast_distance_pct_to_last_close"
                ],
                "top_forecast_ticker": record["top_forecast_ticker"],
                "top_forecast_horizon_change_pct": record["top_forecast_horizon_change_pct"],
                "tickers": [ticker for ticker in tickers if ticker],
            }
        )

    return summary_records


def build_payload(
    thesis_payload: dict[str, object],
    featured_records: list[dict[str, object]],
    basket_summary_records: list[dict[str, object]],
    company_ranking_records: list[dict[str, object]],
    multi_asset_summary_records: list[dict[str, object]],
    multi_asset_suite_run: str | None,
) -> dict[str, object]:
    notes = [
        "Die naive Persistence-Baseline bleibt ein wichtiger Referenzwert.",
        "technical_extended liegt im Mittel leicht vor lag_only, aber der Vorteil ist klein.",
        "Die besten Modelltypen wechseln je nach Ticker.",
        "Das Unternehmensranking kombiniert 5-Tage-Ausblick, relative Walk-Forward-Guete, Richtungstreffer und Abstand zur Baseline.",
    ]
    if multi_asset_summary_records:
        notes.append(
            "Zusaetzlich werden gemeinsame Multi-Asset-Laeufe fuer Aktien- und ETF-Koerbe separat zusammengefasst."
        )
    notes.append(
        "Die UI zeigt den zuletzt exportierten ML-Stand und keine garantierte Live-Prognose."
    )

    data_until_candidates = [
        str(record.get("data_until"))
        for record in featured_records
        if record.get("data_until")
    ]
    payload_data_until = max(data_until_candidates) if data_until_candidates else ""

    return {
        "ui_contract_version": "1.3",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_until": payload_data_until,
        "stale_after_days": DEFAULT_STALE_AFTER_DAYS,
        "source_runs": {
            "thesis_run": thesis_payload["run_name"],
            "multi_asset_suite_run": multi_asset_suite_run or "",
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
        "company_ranking": company_ranking_records,
        "multi_asset_summaries": multi_asset_summary_records,
        "basket_summaries": basket_summary_records,
        "notes": notes,
    }


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    tickers = [ticker.upper() for ticker in (args.tickers or DEFAULT_TICKERS)]
    thesis_artifacts = get_thesis_artifact_paths(args.thesis_run)
    thesis_payload = load_json(thesis_artifacts.summary_json)
    multi_asset_suite_artifacts = get_multi_asset_suite_artifact_paths(args.multi_asset_suite_run)
    multi_asset_suite_payload = try_load_json(multi_asset_suite_artifacts.summary_json)
    featured_records = [build_featured_ticker_record(ticker) for ticker in tickers]
    company_ranking_records = build_company_ranking_records(featured_records)
    basket_summary_records = build_basket_summary_records(thesis_payload)
    multi_asset_summary_records = build_multi_asset_summary_records(multi_asset_suite_payload)

    artifacts = get_dashboard_artifact_paths(args.run_name)
    featured_frame = pd.DataFrame(featured_records).drop(columns=["forecast_path"])
    company_ranking_frame = pd.DataFrame(company_ranking_records)
    basket_summary_frame = pd.DataFrame(basket_summary_records).drop(
        columns=["technical_extended_better_tickers", "lag_only_better_tickers"]
    )
    multi_asset_summary_frame = pd.DataFrame(multi_asset_summary_records).drop(
        columns=["tickers"],
        errors="ignore",
    )

    featured_frame.to_csv(artifacts.featured_tickers_csv, index=False)
    company_ranking_frame.to_csv(artifacts.company_ranking_csv, index=False)
    basket_summary_frame.to_csv(artifacts.basket_summary_csv, index=False)
    multi_asset_summary_frame.to_csv(artifacts.multi_asset_summary_csv, index=False)

    payload = build_payload(
        thesis_payload=thesis_payload,
        featured_records=featured_records,
        basket_summary_records=basket_summary_records,
        company_ranking_records=company_ranking_records,
        multi_asset_summary_records=multi_asset_summary_records,
        multi_asset_suite_run=multi_asset_suite_payload["run_name"] if multi_asset_suite_payload else None,
    )
    artifacts.payload_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Dashboard payload run: {args.run_name}")
    print(f"Featured tickers: {', '.join(tickers)}")
    print("Company ranking:")
    for ranking_entry in company_ranking_records:
        print(
            f"  #{ranking_entry['rank']} {ranking_entry['ticker']}: "
            f"score={ranking_entry['ranking_score']:.1f} | "
            f"5T={ranking_entry['forecast_horizon_change_pct']:+.2f}% | "
            f"rel.RMSE={ranking_entry['relative_rmse_pct']:.2f}%"
        )
    if multi_asset_summary_records:
        print("Multi-asset best configs:")
        for multi_asset_summary in multi_asset_summary_records:
            print(
                f"  {multi_asset_summary['basket_preset']}: "
                f"{multi_asset_summary['feature_profile']} lag{multi_asset_summary['lags']} | "
                f"{multi_asset_summary['shared_model_label']} RMSE={multi_asset_summary['shared_model_rmse']:.4f}"
            )
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
