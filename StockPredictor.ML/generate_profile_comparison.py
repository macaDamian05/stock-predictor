from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from core.paths import (
    BENCHMARK_DATA_DIR,
    ensure_runtime_directories,
    get_profile_comparison_artifact_paths,
)
from run_classical_pipeline import MODEL_DISPLAY_NAMES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare feature-profile benchmark runs and build a consolidated report."
    )
    parser.add_argument(
        "benchmark_runs",
        nargs="+",
        help="Benchmark run folders below storage/benchmarks/.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Target folder below storage/experiments/. Defaults to a timestamp-based name.",
    )
    parser.add_argument(
        "--basket-name",
        default=None,
        help="Optional display name for the compared ticker basket.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Required benchmark artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_benchmark_payload(run_name: str) -> dict[str, object]:
    return load_json(BENCHMARK_DATA_DIR / run_name.upper() / "benchmark_summary.json")


def build_summary_frame(profile_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for feature_profile, frame in profile_frames.items():
        dominant_best_model = Counter(frame["best_learned_model"].tolist()).most_common(1)[0][0]
        rows.append(
            {
                "feature_profile": feature_profile,
                "ticker_count": len(frame),
                "mean_walk_forward_baseline_rmse": frame[
                    "walk_forward_baseline_persistence_rmse"
                ].mean(),
                "mean_best_learned_rmse": frame["best_learned_rmse"].mean(),
                "mean_best_learned_directional_accuracy": frame[
                    "best_learned_directional_accuracy"
                ].mean(),
                "mean_best_learned_minus_baseline_rmse": frame[
                    "best_learned_minus_baseline_rmse"
                ].mean(),
                "dominant_best_model": dominant_best_model,
            }
        )

    return pd.DataFrame(rows).sort_values("mean_best_learned_rmse").reset_index(drop=True)


def build_per_ticker_frame(
    feature_profiles: list[str],
    profile_frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, str]:
    if len(feature_profiles) != 2:
        raise ValueError(
            "Per-ticker wide comparison currently requires exactly two feature profiles."
        )

    left_profile, right_profile = feature_profiles
    left_frame = (
        profile_frames[left_profile][["ticker", "best_learned_model", "best_learned_rmse"]]
        .rename(
            columns={
                "best_learned_model": f"{left_profile}_best_model",
                "best_learned_rmse": f"{left_profile}_best_rmse",
            }
        )
        .copy()
    )
    right_frame = (
        profile_frames[right_profile][["ticker", "best_learned_model", "best_learned_rmse"]]
        .rename(
            columns={
                "best_learned_model": f"{right_profile}_best_model",
                "best_learned_rmse": f"{right_profile}_best_rmse",
            }
        )
        .copy()
    )

    merged_frame = left_frame.merge(right_frame, on="ticker", how="inner")
    if len(merged_frame) != len(left_frame) or len(merged_frame) != len(right_frame):
        raise ValueError("Compared profiles do not cover the same ticker set.")

    delta_column = f"{right_profile}_minus_{left_profile}_rmse"
    merged_frame[delta_column] = (
        merged_frame[f"{right_profile}_best_rmse"] - merged_frame[f"{left_profile}_best_rmse"]
    )

    return merged_frame.sort_values(delta_column).reset_index(drop=True), delta_column


def save_mean_rmse_plot(artifact_path: Path, summary_frame: pd.DataFrame) -> None:
    labels = summary_frame["feature_profile"].tolist()
    x_positions = list(range(len(labels)))

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.bar(
        [position - 0.2 for position in x_positions],
        summary_frame["mean_walk_forward_baseline_rmse"],
        width=0.4,
        label="Baseline RMSE",
    )
    axis.bar(
        [position + 0.2 for position in x_positions],
        summary_frame["mean_best_learned_rmse"],
        width=0.4,
        label="Best learned RMSE",
    )
    axis.set_title("Mean walk-forward RMSE by feature profile")
    axis.set_xlabel("Feature profile")
    axis.set_ylabel("RMSE")
    axis.set_xticks(x_positions)
    axis.set_xticklabels(labels)
    axis.grid(True, axis="y")
    axis.legend()

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def save_delta_plot(artifact_path: Path, per_ticker_frame: pd.DataFrame, delta_column: str) -> None:
    figure, axis = plt.subplots(figsize=(11, 7))
    colors = [
        "tab:green" if delta < 0 else ("tab:red" if delta > 0 else "tab:gray")
        for delta in per_ticker_frame[delta_column]
    ]
    axis.barh(per_ticker_frame["ticker"], per_ticker_frame[delta_column], color=colors)
    axis.axvline(0.0, color="black", linewidth=1)
    axis.set_title("Per-ticker RMSE difference between compared feature profiles")
    axis.set_xlabel("RMSE delta (negative means the right profile is better)")
    axis.set_ylabel("Ticker")
    axis.grid(True, axis="x")

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def build_report(
    run_name: str,
    basket_name: str,
    source_runs: list[str],
    summary_frame: pd.DataFrame,
    per_ticker_frame: pd.DataFrame | None,
    delta_column: str | None,
) -> str:
    lines = [
        f"# Profile Comparison: {run_name}",
        "",
        f"Verglichen wurde der Korb `{basket_name}`.",
        "",
        f"Quellruns: {', '.join(f'`{run_name}`' for run_name in source_runs)}",
        "",
        "## Mittelwerte",
        "",
    ]

    for row in summary_frame.itertuples(index=False):
        lines.append(
            f"- `{row.feature_profile}`: bestes gelerntes Mittel-RMSE {row.mean_best_learned_rmse:.4f}, "
            f"Baseline-Mittel-RMSE {row.mean_walk_forward_baseline_rmse:.4f}, "
            f"dominantes Modell `{row.dominant_best_model}`."
        )

    lines.extend(["", "## Einordnung", ""])

    if len(summary_frame) >= 2:
        best_row = summary_frame.iloc[0]
        second_row = summary_frame.iloc[1]
        lines.append(
            f"- `{best_row['feature_profile']}` ist im Mittel um "
            f"{second_row['mean_best_learned_rmse'] - best_row['mean_best_learned_rmse']:.4f} RMSE "
            "besser als die naechstplatzierte Vergleichskonfiguration."
        )

    lines.append(
        "- Die naive Baseline bleibt weiterhin ein wichtiger Referenzwert fuer die Punktprognose."
    )

    if per_ticker_frame is not None and delta_column is not None:
        better_right = per_ticker_frame.loc[per_ticker_frame[delta_column] < 0, "ticker"].tolist()
        better_left = per_ticker_frame.loc[per_ticker_frame[delta_column] > 0, "ticker"].tolist()
        lines.append(
            f"- Profilvorteile je Ticker: rechter Vergleichsvorteil bei "
            f"{len(better_right)} Tickern, linker Vergleichsvorteil bei {len(better_left)} Tickern."
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    run_name = args.run_name or ("profile_comparison_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    artifacts = get_profile_comparison_artifact_paths(run_name)

    payloads = [load_benchmark_payload(run_name) for run_name in args.benchmark_runs]
    feature_profile_order: list[str] = []
    profile_frames: dict[str, pd.DataFrame] = {}
    basket_name = args.basket_name or str(payloads[0].get("basket_preset") or "custom")

    for payload, source_run in zip(payloads, args.benchmark_runs):
        feature_profile = payload.get("feature_profile")
        if not feature_profile:
            raise ValueError(
                f"Benchmark run '{source_run}' has no feature_profile in benchmark_summary.json."
            )

        if feature_profile not in feature_profile_order:
            feature_profile_order.append(str(feature_profile))
            profile_frames[str(feature_profile)] = pd.DataFrame()

        result_frame = pd.DataFrame(payload["results"]).copy()
        result_frame["source_run"] = source_run.upper()
        result_frame["feature_profile"] = str(feature_profile)
        profile_frames[str(feature_profile)] = pd.concat(
            [profile_frames[str(feature_profile)], result_frame],
            ignore_index=True,
        )

    for feature_profile, frame in profile_frames.items():
        if frame["ticker"].duplicated().any():
            duplicates = frame.loc[frame["ticker"].duplicated(), "ticker"].tolist()
            raise ValueError(
                f"Duplicate tickers found for feature profile '{feature_profile}': {duplicates}"
            )

    summary_frame = build_summary_frame(profile_frames)
    per_ticker_frame: pd.DataFrame | None = None
    delta_column: str | None = None
    if len(feature_profile_order) == 2:
        per_ticker_frame, delta_column = build_per_ticker_frame(feature_profile_order, profile_frames)

    summary_frame.to_csv(artifacts.summary_csv, index=False)
    if per_ticker_frame is not None:
        per_ticker_frame.to_csv(artifacts.per_ticker_csv, index=False)

    save_mean_rmse_plot(artifacts.mean_rmse_plot, summary_frame)
    if per_ticker_frame is not None and delta_column is not None:
        save_delta_plot(artifacts.delta_plot, per_ticker_frame, delta_column)

    summary_payload = {
        "basket": basket_name,
        "compared_profiles": feature_profile_order,
        "source_runs": [run_name.upper() for run_name in args.benchmark_runs],
        "summary": summary_frame.to_dict(orient="records"),
        "per_ticker": [] if per_ticker_frame is None else per_ticker_frame.to_dict(orient="records"),
    }
    artifacts.summary_json.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    artifacts.report.write_text(
        build_report(
            run_name=run_name,
            basket_name=basket_name,
            source_runs=[run_name.upper() for run_name in args.benchmark_runs],
            summary_frame=summary_frame,
            per_ticker_frame=per_ticker_frame,
            delta_column=delta_column,
        ),
        encoding="utf-8",
    )

    print(f"Profile comparison run: {run_name}")
    for row in summary_frame.itertuples(index=False):
        print(
            f"  {row.feature_profile}: "
            f"best mean RMSE={row.mean_best_learned_rmse:.4f} | "
            f"baseline mean RMSE={row.mean_walk_forward_baseline_rmse:.4f} | "
            f"dominant model={MODEL_DISPLAY_NAMES[row.dominant_best_model]}"
        )
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
