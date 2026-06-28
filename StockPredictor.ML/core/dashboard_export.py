from __future__ import annotations

import csv
from dataclasses import asdict
from datetime import datetime
import json
from statistics import mean

from .model_registry import (
    CoreModelMetric,
    CoreModelRegistryRecord,
    discover_registries,
    model_label,
    utc_now_iso,
)
from .paths import get_dashboard_artifact_paths
from .prediction_service import CorePredictionResult, load_prediction, predict_saved_model


def export_core_dashboard_payload(
    symbols: list[str] | None = None,
    horizon: int | None = None,
    run_name: str = "LATEST",
    stale_after_days: int = 5,
    refresh_missing_predictions: bool = True,
) -> dict:
    registries = discover_registries(symbols=symbols, horizon=horizon)
    featured_records: list[dict] = []
    failures: list[str] = []

    for registry in registries:
        try:
            try:
                prediction = load_prediction(registry.symbol, registry.horizon)
            except FileNotFoundError:
                if not refresh_missing_predictions:
                    raise

                prediction = predict_saved_model(
                    symbol=registry.symbol,
                    horizon=registry.horizon,
                    persist=True,
                )

            featured_records.append(build_featured_ticker_record(registry, prediction))
        except Exception as exception:
            failures.append(f"{registry.symbol}: {exception}")

    payload = build_dashboard_payload(
        registries=registries,
        featured_records=featured_records,
        failures=failures,
        stale_after_days=stale_after_days,
    )

    paths = get_dashboard_artifact_paths(run_name)
    paths.payload_json.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_featured_tickers_csv(paths.featured_tickers_csv, featured_records)
    write_company_ranking_csv(paths.company_ranking_csv, payload["company_ranking"])
    paths.basket_summary_csv.write_text("basket_key,basket_label\n", encoding="utf-8")
    paths.multi_asset_summary_csv.write_text("basket_preset,basket_label\n", encoding="utf-8")
    return payload


def build_dashboard_payload(
    registries: list[CoreModelRegistryRecord],
    featured_records: list[dict],
    failures: list[str],
    stale_after_days: int,
) -> dict:
    generated_at = utc_now_iso()
    data_until_values = [record["data_until"] for record in featured_records if record.get("data_until")]
    data_until = max(data_until_values) if data_until_values else None
    selected_metrics = [
        _selected_metric(registry)
        for registry in registries
        if _selected_metric(registry) is not None
    ]
    baseline_metrics = [
        _metric_by_key(registry, "baseline_persistence")
        for registry in registries
        if _metric_by_key(registry, "baseline_persistence") is not None
    ]

    notes = [
        "Core-Rebuild-Payload: Modelle werden offline trainiert und beim App-Besuch nur geladen.",
        "Forecasts sind forschungsbasierte Schaetzungen und keine Anlageberatung.",
        "Profile, Watchlist, News, Notifications und Chat bleiben Legacy/Experimental.",
    ]
    notes.extend(failures)

    return {
        "ui_contract_version": "core-v1",
        "generated_at": generated_at,
        "data_until": data_until,
        "stale_after_days": stale_after_days,
        "source_runs": {
            "thesis_run": "core-rebuild",
            "multi_asset_suite_run": "",
            "starter_suite": "core-model-suite",
            "core_profile_comparison": "core-registry",
            "diversified_profile_comparison": "",
        },
        "summary_cards": build_summary_cards(selected_metrics, baseline_metrics, featured_records),
        "featured_tickers": featured_records,
        "company_ranking": build_company_ranking(featured_records),
        "multi_asset_summaries": [],
        "basket_summaries": [],
        "notes": notes,
    }


def build_featured_ticker_record(
    registry: CoreModelRegistryRecord,
    prediction: CorePredictionResult,
) -> dict:
    selected_metric = _selected_metric(registry)
    baseline_metric = _metric_by_key(registry, "baseline_persistence")
    selected_model = {
        "model_key": registry.selected_model_key,
        "model_label": registry.selected_model_label,
    }
    available_models = [
        {
            "model_key": metric.model_key,
            "model_label": metric.model_label,
        }
        for metric in registry.metrics
    ]

    return {
        "ticker": registry.symbol,
        "forecast_generated_at": prediction.generated_at,
        "data_until": prediction.data_until,
        "forecast_model": registry.selected_model_key,
        "forecast_model_label": registry.selected_model_label,
        "selected_model": selected_model,
        "available_models": available_models,
        "model_metrics": [build_model_metric_record(metric) for metric in registry.metrics],
        "last_close_date": prediction.last_close_date,
        "last_close": prediction.last_close,
        "next_forecast_date": prediction.next_forecast_date,
        "next_predicted_close": prediction.next_predicted_close,
        "next_predicted_change_pct": prediction.next_predicted_change_pct,
        "forecast_end_date": prediction.forecast_end_date,
        "forecast_end_close": prediction.forecast_end_close,
        "forecast_horizon_change_pct": prediction.forecast_horizon_change_pct,
        "forecast_days": registry.horizon,
        "forecast_horizon_days": registry.horizon,
        "average_recent_rsi": 0.0,
        "average_forecast_slope": prediction.average_forecast_slope,
        "average_forecast_distance_to_last_close": prediction.average_forecast_distance_to_last_close,
        "average_forecast_distance_pct_to_last_close": (
            prediction.average_forecast_distance_pct_to_last_close
        ),
        "feature_profile": registry.feature_profile,
        "feature_profile_label": format_feature_profile_label(registry.feature_profile),
        "holdout_best_model": registry.selected_model_key,
        "walk_forward_best_model": registry.selected_model_key,
        "walk_forward_best_rmse": selected_metric.rmse if selected_metric else 0.0,
        "walk_forward_baseline_rmse": baseline_metric.rmse if baseline_metric else 0.0,
        "walk_forward_best_directional_accuracy": (
            selected_metric.directional_accuracy if selected_metric else 0.0
        ),
        "beats_baseline_rmse": (
            selected_metric is not None
            and baseline_metric is not None
            and selected_metric.rmse < baseline_metric.rmse
        ),
        "data_start": prediction.data_start,
        "data_end": prediction.data_until,
        "model_trained_at": registry.trained_at,
        "validation_start": registry.validation_start,
        "validation_end": registry.validation_end,
        "forecast_path": [asdict(point) for point in prediction.forecast_path],
    }


def build_model_metric_record(metric: CoreModelMetric) -> dict:
    return {
        "model_key": metric.model_key,
        "model_label": metric.model_label,
        "is_selected": metric.is_selected,
        "has_next_step_prediction": metric.is_selected,
        "next_predicted_close": None,
        "next_predicted_change_pct": None,
        "holdout_mae": metric.mae,
        "holdout_rmse": metric.rmse,
        "holdout_directional_accuracy": metric.directional_accuracy,
        "walk_forward_mae": metric.mae,
        "walk_forward_rmse": metric.rmse,
        "walk_forward_directional_accuracy": metric.directional_accuracy,
        "walk_forward_rmse_gap_vs_baseline": metric.rmse_gap_vs_baseline,
        "walk_forward_mae_gap_vs_baseline": metric.mae_gap_vs_baseline,
        "walk_forward_directional_accuracy_gap_vs_baseline": (
            metric.directional_accuracy_gap_vs_baseline
        ),
        "holdout_rmse_gap_vs_baseline": metric.rmse_gap_vs_baseline,
        "holdout_mae_gap_vs_baseline": metric.mae_gap_vs_baseline,
        "metadata_available": True,
        "notes": "Chronologische Validierung im Core-Orchestrator.",
        "data_until": None,
    }


def build_summary_cards(
    selected_metrics: list[CoreModelMetric | None],
    baseline_metrics: list[CoreModelMetric | None],
    featured_records: list[dict],
) -> dict:
    selected = [metric for metric in selected_metrics if metric is not None]
    baselines = [metric for metric in baseline_metrics if metric is not None]
    dominant_model_key = _dominant_model_key(featured_records)

    return {
        "starter_best_experiment": {
            "experiment_id": "core-rebuild",
            "feature_profile": "core-model-suite",
            "lags": 0,
            "ticker_count": len(featured_records),
            "successful_tickers": len(featured_records),
            "failed_tickers": 0,
            "mean_walk_forward_baseline_rmse": _mean_or_zero([metric.rmse for metric in baselines]),
            "mean_best_learned_rmse": _mean_or_zero([metric.rmse for metric in selected]),
            "mean_best_learned_directional_accuracy": _mean_or_zero(
                [metric.directional_accuracy for metric in selected]
            ),
            "mean_best_learned_minus_baseline_rmse": _mean_or_zero(
                [
                    metric.rmse_gap_vs_baseline
                    for metric in selected
                    if metric.rmse_gap_vs_baseline is not None
                ]
            ),
            "dominant_best_model": dominant_model_key,
            "ridge_wins": _model_win_count(featured_records, "ridge_regression"),
            "decision_tree_wins": 0,
            "random_forest_wins": _model_win_count(featured_records, "random_forest"),
            "dominant_best_model_label": model_label(dominant_model_key),
        },
        "starter_tickers_beating_baseline": [
            record["ticker"] for record in featured_records if record.get("beats_baseline_rmse")
        ],
        "best_core_profile": build_profile_summary_card(selected, baselines, dominant_model_key),
        "best_diversified_profile": build_profile_summary_card(selected, baselines, dominant_model_key),
    }


def build_profile_summary_card(
    selected: list[CoreModelMetric],
    baselines: list[CoreModelMetric],
    dominant_model_key: str,
) -> dict:
    return {
        "feature_profile": "core-model-suite",
        "ticker_count": len(selected),
        "mean_walk_forward_baseline_rmse": _mean_or_zero([metric.rmse for metric in baselines]),
        "mean_best_learned_rmse": _mean_or_zero([metric.rmse for metric in selected]),
        "mean_best_learned_directional_accuracy": _mean_or_zero(
            [metric.directional_accuracy for metric in selected]
        ),
        "mean_best_learned_minus_baseline_rmse": _mean_or_zero(
            [
                metric.rmse_gap_vs_baseline
                for metric in selected
                if metric.rmse_gap_vs_baseline is not None
            ]
        ),
        "dominant_best_model": dominant_model_key,
        "feature_profile_label": "Core-Modellsuite",
        "dominant_best_model_label": model_label(dominant_model_key),
    }


def build_company_ranking(featured_records: list[dict]) -> list[dict]:
    ranked = []
    for record in featured_records:
        best_rmse = float(record.get("walk_forward_best_rmse") or 0.0)
        baseline_rmse = float(record.get("walk_forward_baseline_rmse") or 0.0)
        last_close = float(record.get("last_close") or 0.0)
        directional_accuracy = float(record.get("walk_forward_best_directional_accuracy") or 0.0)
        relative_rmse_pct = (best_rmse / last_close) * 100.0 if last_close else 0.0
        relative_gap_vs_baseline_pct = (
            ((best_rmse - baseline_rmse) / baseline_rmse) * 100.0 if baseline_rmse else 0.0
        )
        ranking_score = (directional_accuracy * 100.0) - relative_rmse_pct
        ranked.append(
            {
                "rank": 0,
                "ticker": record["ticker"],
                "ranking_score": ranking_score,
                "forecast_model": record["forecast_model"],
                "forecast_model_label": record["forecast_model_label"],
                "feature_profile": record["feature_profile"],
                "feature_profile_label": record["feature_profile_label"],
                "last_close": record["last_close"],
                "next_predicted_change_pct": record["next_predicted_change_pct"],
                "forecast_horizon_change_pct": record["forecast_horizon_change_pct"],
                "average_forecast_distance_to_last_close": (
                    record["average_forecast_distance_to_last_close"]
                ),
                "average_forecast_distance_pct_to_last_close": (
                    record["average_forecast_distance_pct_to_last_close"]
                ),
                "walk_forward_best_directional_accuracy": directional_accuracy,
                "walk_forward_best_rmse": best_rmse,
                "walk_forward_baseline_rmse": baseline_rmse,
                "relative_rmse_pct": relative_rmse_pct,
                "relative_gap_vs_baseline_pct": relative_gap_vs_baseline_pct,
                "average_recent_rsi": record["average_recent_rsi"],
                "beats_baseline_rmse": record["beats_baseline_rmse"],
            }
        )

    ranked.sort(key=lambda item: item["ranking_score"], reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
    return ranked


def write_featured_tickers_csv(path, featured_records: list[dict]) -> None:
    columns = [
        "ticker",
        "data_until",
        "model_trained_at",
        "forecast_generated_at",
        "forecast_model",
        "last_close",
        "forecast_horizon_change_pct",
        "walk_forward_best_rmse",
        "walk_forward_baseline_rmse",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in featured_records:
            writer.writerow({column: record.get(column) for column in columns})


def write_company_ranking_csv(path, ranking_records: list[dict]) -> None:
    columns = [
        "rank",
        "ticker",
        "ranking_score",
        "forecast_model",
        "last_close",
        "forecast_horizon_change_pct",
        "walk_forward_best_rmse",
        "walk_forward_baseline_rmse",
        "relative_rmse_pct",
        "relative_gap_vs_baseline_pct",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in ranking_records:
            writer.writerow({column: record.get(column) for column in columns})


def format_feature_profile_label(value: str) -> str:
    return {
        "technical_extended": "Technisch erweitert",
        "technical_basic": "Technisch grundlegend",
        "lag_only": "Nur Lags",
    }.get(value, value.replace("_", " "))


def _selected_metric(registry: CoreModelRegistryRecord) -> CoreModelMetric | None:
    return _metric_by_key(registry, registry.selected_model_key)


def _metric_by_key(registry: CoreModelRegistryRecord, model_key: str) -> CoreModelMetric | None:
    return next((metric for metric in registry.metrics if metric.model_key == model_key), None)


def _mean_or_zero(values: list[float | None]) -> float:
    clean_values = [float(value) for value in values if value is not None]
    return float(mean(clean_values)) if clean_values else 0.0


def _dominant_model_key(featured_records: list[dict]) -> str:
    if not featured_records:
        return "baseline_persistence"

    counts: dict[str, int] = {}
    for record in featured_records:
        counts[record["forecast_model"]] = counts.get(record["forecast_model"], 0) + 1

    return max(counts, key=counts.get)


def _model_win_count(featured_records: list[dict], model_key: str) -> int:
    return sum(1 for record in featured_records if record["forecast_model"] == model_key)
