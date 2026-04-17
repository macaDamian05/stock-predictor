from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from core.paths import (
    EXPERIMENT_DATA_DIR,
    ensure_runtime_directories,
    get_thesis_artifact_paths,
)
from run_classical_pipeline import MODEL_DISPLAY_NAMES


DEFAULT_STARTER_SUITE_RUN = "BACHELOR_SUITE_STARTER"
DEFAULT_CORE_PROFILE_RUN = "BACHELOR_CORE_PROFILE_COMPARISON"
MODEL_WIN_ORDER = ["ridge_regression", "decision_tree", "random_forest"]
PROFILE_DISPLAY_NAMES = {
    "lag_only": "Lag Only",
    "technical_basic": "Technical Basic",
    "technical_extended": "Technical Extended",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a thesis-ready result pack from existing benchmark and experiment artifacts."
    )
    parser.add_argument(
        "--starter-suite-run",
        default=DEFAULT_STARTER_SUITE_RUN,
        help="Experiment-suite run used for the starter basket summary.",
    )
    parser.add_argument(
        "--core-profile-run",
        default=DEFAULT_CORE_PROFILE_RUN,
        help="Experiment run that compares feature profiles on the bachelor_core basket.",
    )
    parser.add_argument(
        "--run-name",
        default="bachelor_thesis_results",
        help="Output folder name below storage/thesis/.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Required artifact file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def coerce_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return float("nan")

    return float(text.replace(",", "."))


def normalize_numeric_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    normalized = frame.copy()
    for column in columns:
        normalized[column] = normalized[column].map(coerce_float)
    return normalized


def cast_int_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    normalized = frame.copy()
    for column in columns:
        normalized[column] = normalized[column].round().astype(int)
    return normalized


def build_starter_suite_frames(starter_payload: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    starter_suite_frame = pd.DataFrame(starter_payload["summary"])
    starter_models_frame = pd.DataFrame(starter_payload["ticker_best_configs"])

    starter_suite_frame = normalize_numeric_columns(
        starter_suite_frame,
        [
            "lags",
            "ticker_count",
            "successful_tickers",
            "failed_tickers",
            "mean_walk_forward_baseline_rmse",
            "mean_best_learned_rmse",
            "mean_best_learned_directional_accuracy",
            "mean_best_learned_minus_baseline_rmse",
            "ridge_wins",
            "decision_tree_wins",
            "random_forest_wins",
        ],
    ).sort_values("mean_best_learned_rmse")
    starter_suite_frame = cast_int_columns(
        starter_suite_frame,
        [
            "lags",
            "ticker_count",
            "successful_tickers",
            "failed_tickers",
            "ridge_wins",
            "decision_tree_wins",
            "random_forest_wins",
        ],
    )
    starter_suite_frame["dominant_best_model_label"] = starter_suite_frame["dominant_best_model"].map(
        MODEL_DISPLAY_NAMES
    )

    starter_models_frame = normalize_numeric_columns(
        starter_models_frame,
        [
            "lags",
            "data_rows",
            "best_learned_rmse",
            "best_learned_directional_accuracy",
            "best_learned_minus_baseline_rmse",
            "walk_forward_fold_count",
            "walk_forward_baseline_persistence_rmse",
            "walk_forward_baseline_persistence_directional_accuracy",
        ],
    ).sort_values("best_learned_rmse")
    starter_models_frame = cast_int_columns(
        starter_models_frame,
        [
            "lags",
            "data_rows",
            "walk_forward_fold_count",
        ],
    )
    starter_models_frame["best_learned_model_label"] = starter_models_frame["best_learned_model"].map(
        MODEL_DISPLAY_NAMES
    )
    starter_models_frame["baseline_rmse"] = starter_models_frame[
        "walk_forward_baseline_persistence_rmse"
    ]
    starter_models_frame["rmse_gap_vs_baseline"] = (
        starter_models_frame["best_learned_rmse"] - starter_models_frame["baseline_rmse"]
    )
    starter_models_frame["beats_baseline"] = starter_models_frame["rmse_gap_vs_baseline"] < 0.0

    return starter_suite_frame, starter_models_frame


def build_core_profile_frames(core_payload: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_summary_frame = pd.DataFrame(core_payload["summary"])
    core_per_ticker_frame = pd.DataFrame(core_payload["per_ticker"])

    core_summary_frame = normalize_numeric_columns(
        core_summary_frame,
        [
            "ticker_count",
            "mean_walk_forward_baseline_rmse",
            "mean_best_learned_rmse",
            "mean_best_learned_directional_accuracy",
            "mean_best_learned_minus_baseline_rmse",
        ],
    ).sort_values("mean_best_learned_rmse")
    core_summary_frame = cast_int_columns(core_summary_frame, ["ticker_count"])
    core_summary_frame["feature_profile_label"] = core_summary_frame["feature_profile"].map(
        PROFILE_DISPLAY_NAMES
    )
    core_summary_frame["dominant_best_model_label"] = core_summary_frame["dominant_best_model"].map(
        MODEL_DISPLAY_NAMES
    )

    core_per_ticker_frame = normalize_numeric_columns(
        core_per_ticker_frame,
        [
            "lag_only_best_rmse",
            "technical_extended_best_rmse",
            "technical_minus_lag_rmse",
        ],
    ).sort_values("technical_minus_lag_rmse")
    core_per_ticker_frame["lag_only_best_model_label"] = core_per_ticker_frame[
        "lag_only_best_model"
    ].map(MODEL_DISPLAY_NAMES)
    core_per_ticker_frame["technical_extended_best_model_label"] = core_per_ticker_frame[
        "technical_extended_best_model"
    ].map(MODEL_DISPLAY_NAMES)
    core_per_ticker_frame["better_profile"] = core_per_ticker_frame["technical_minus_lag_rmse"].map(
        lambda delta: "technical_extended" if delta < 0 else ("lag_only" if delta > 0 else "tie")
    )

    return core_summary_frame, core_per_ticker_frame


def build_model_win_counts(core_per_ticker_frame: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for feature_profile, column_name in [
        ("lag_only", "lag_only_best_model"),
        ("technical_extended", "technical_extended_best_model"),
    ]:
        counts = Counter(core_per_ticker_frame[column_name].tolist())
        for model_name in MODEL_WIN_ORDER:
            records.append(
                {
                    "feature_profile": feature_profile,
                    "feature_profile_label": PROFILE_DISPLAY_NAMES[feature_profile],
                    "model_name": model_name,
                    "model_label": MODEL_DISPLAY_NAMES[model_name],
                    "win_count": counts.get(model_name, 0),
                }
            )

    model_wins_frame = pd.DataFrame(records)
    model_wins_frame = cast_int_columns(model_wins_frame, ["win_count"])
    return model_wins_frame


def save_starter_rmse_plot(artifact_path: Path, starter_models_frame: pd.DataFrame) -> None:
    tickers = starter_models_frame["ticker"].tolist()
    x_positions = list(range(len(tickers)))

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.bar(
        [position - 0.2 for position in x_positions],
        starter_models_frame["baseline_rmse"],
        width=0.4,
        label="Baseline RMSE",
    )
    axis.bar(
        [position + 0.2 for position in x_positions],
        starter_models_frame["best_learned_rmse"],
        width=0.4,
        label="Best learned RMSE",
    )
    axis.set_title("Starter basket: baseline vs. best learned RMSE")
    axis.set_xlabel("Ticker")
    axis.set_ylabel("Walk-forward RMSE")
    axis.set_xticks(x_positions)
    axis.set_xticklabels(tickers)
    axis.grid(True, axis="y")
    axis.legend()

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def save_core_profile_plot(artifact_path: Path, core_summary_frame: pd.DataFrame) -> None:
    labels = core_summary_frame["feature_profile_label"].tolist()
    x_positions = list(range(len(labels)))

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.bar(
        [position - 0.2 for position in x_positions],
        core_summary_frame["mean_walk_forward_baseline_rmse"],
        width=0.4,
        label="Baseline RMSE",
    )
    axis.bar(
        [position + 0.2 for position in x_positions],
        core_summary_frame["mean_best_learned_rmse"],
        width=0.4,
        label="Best learned RMSE",
    )
    axis.set_title("Bachelor core: mean RMSE by feature profile")
    axis.set_xlabel("Feature profile")
    axis.set_ylabel("Mean walk-forward RMSE")
    axis.set_xticks(x_positions)
    axis.set_xticklabels(labels)
    axis.grid(True, axis="y")
    axis.legend()

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def save_core_profile_delta_plot(artifact_path: Path, core_per_ticker_frame: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(11, 7))
    colors = [
        "tab:green" if delta < 0 else ("tab:red" if delta > 0 else "tab:gray")
        for delta in core_per_ticker_frame["technical_minus_lag_rmse"]
    ]

    axis.barh(
        core_per_ticker_frame["ticker"],
        core_per_ticker_frame["technical_minus_lag_rmse"],
        color=colors,
    )
    axis.axvline(0.0, color="black", linewidth=1)
    axis.set_title("Bachelor core: technical_extended minus lag_only RMSE")
    axis.set_xlabel("RMSE delta (negative means technical_extended is better)")
    axis.set_ylabel("Ticker")
    axis.grid(True, axis="x")

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def save_model_wins_plot(artifact_path: Path, model_wins_frame: pd.DataFrame) -> None:
    profiles = ["lag_only", "technical_extended"]
    x_positions = list(range(len(profiles)))
    width = 0.22
    offsets = [-width, 0.0, width]

    figure, axis = plt.subplots(figsize=(10, 6))
    for offset, model_name in zip(offsets, MODEL_WIN_ORDER):
        subset = (
            model_wins_frame.loc[model_wins_frame["model_name"] == model_name]
            .set_index("feature_profile")
            .reindex(profiles)
        )
        axis.bar(
            [position + offset for position in x_positions],
            subset["win_count"],
            width=width,
            label=MODEL_DISPLAY_NAMES[model_name],
        )

    axis.set_title("Bachelor core: best-model wins by feature profile")
    axis.set_xlabel("Feature profile")
    axis.set_ylabel("Number of tickers")
    axis.set_xticks(x_positions)
    axis.set_xticklabels([PROFILE_DISPLAY_NAMES[profile] for profile in profiles])
    axis.grid(True, axis="y")
    axis.legend()

    figure.tight_layout()
    figure.savefig(artifact_path, dpi=150)
    plt.close(figure)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *body_lines])


def build_report(
    run_name: str,
    starter_suite_run: str,
    core_profile_run: str,
    starter_suite_frame: pd.DataFrame,
    starter_models_frame: pd.DataFrame,
    core_summary_frame: pd.DataFrame,
    core_per_ticker_frame: pd.DataFrame,
    model_wins_frame: pd.DataFrame,
) -> str:
    best_starter_experiment = starter_suite_frame.iloc[0]
    best_core_profile = core_summary_frame.iloc[0]
    technical_better = core_per_ticker_frame.loc[
        core_per_ticker_frame["better_profile"] == "technical_extended", "ticker"
    ].tolist()
    lag_better = core_per_ticker_frame.loc[
        core_per_ticker_frame["better_profile"] == "lag_only", "ticker"
    ].tolist()
    tie_tickers = core_per_ticker_frame.loc[
        core_per_ticker_frame["better_profile"] == "tie", "ticker"
    ].tolist()
    starter_beats_baseline = starter_models_frame.loc[
        starter_models_frame["beats_baseline"], "ticker"
    ].tolist()

    lines = [
        f"# Thesis Results Pack: {run_name}",
        "",
        f"Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Quellen",
        "",
        f"- Starter-Suite: `storage/experiments/{starter_suite_run}/experiment_summary.json`",
        f"- Bachelor-Core-Profilvergleich: `storage/experiments/{core_profile_run}/profile_comparison_summary.json`",
        "",
        "## Kurzfazit",
        "",
        (
            f"- Beste Starter-Konfiguration: `{best_starter_experiment['experiment_id']}` mit "
            f"mittlerem bestem gelernten Walk-Forward-RMSE von "
            f"{best_starter_experiment['mean_best_learned_rmse']:.4f}."
        ),
        (
            f"- Im `bachelor_core`-Vergleich ist `{best_core_profile['feature_profile']}` "
            f"bei den besten gelernten Modellen im Mittel vorne "
            f"({best_core_profile['mean_best_learned_rmse']:.4f} RMSE)."
        ),
        (
            f"- Gegenueber `lag_only` ist `technical_extended` fuer "
            f"{len(technical_better)} von {len(core_per_ticker_frame)} Tickers besser, "
            f"fuer {len(lag_better)} schlechter."
        ),
        (
            f"- Im Starter-Korb schlagen die besten gelernten Modelle die Baseline aktuell "
            f"bei {len(starter_beats_baseline)} von {len(starter_models_frame)} Tickern."
        ),
        "",
        "## Starter-Korb: beste Konfigurationen pro Ticker",
        "",
        markdown_table(
            headers=["Ticker", "Beste Konfiguration", "Bestes Modell", "Bestes RMSE", "Baseline RMSE", "Gap"],
            rows=[
                [
                    row.ticker,
                    row.experiment_id,
                    row.best_learned_model_label,
                    f"{row.best_learned_rmse:.4f}",
                    f"{row.baseline_rmse:.4f}",
                    f"{row.rmse_gap_vs_baseline:+.4f}",
                ]
                for row in starter_models_frame.itertuples(index=False)
            ],
        ),
        "",
        "## Starter-Suite: Profilranking",
        "",
        markdown_table(
            headers=[
                "Konfiguration",
                "Profil",
                "Bestes RMSE",
                "Baseline RMSE",
                "Gap",
                "Dominantes Modell",
            ],
            rows=[
                [
                    row.experiment_id,
                    row.feature_profile,
                    f"{row.mean_best_learned_rmse:.4f}",
                    f"{row.mean_walk_forward_baseline_rmse:.4f}",
                    f"{row.mean_best_learned_minus_baseline_rmse:+.4f}",
                    row.dominant_best_model_label,
                ]
                for row in starter_suite_frame.itertuples(index=False)
            ],
        ),
        "",
        "## Bachelor Core: Profilvergleich",
        "",
        markdown_table(
            headers=["Profil", "Bestes RMSE", "Baseline RMSE", "Gap", "Richtung", "Dominantes Modell"],
            rows=[
                [
                    row.feature_profile,
                    f"{row.mean_best_learned_rmse:.4f}",
                    f"{row.mean_walk_forward_baseline_rmse:.4f}",
                    f"{row.mean_best_learned_minus_baseline_rmse:+.4f}",
                    f"{row.mean_best_learned_directional_accuracy:.2%}",
                    row.dominant_best_model_label,
                ]
                for row in core_summary_frame.itertuples(index=False)
            ],
        ),
        "",
        "## Bachelor Core: Tickerweise Differenzen",
        "",
        markdown_table(
            headers=["Ticker", "Lag-Only Modell", "Lag-Only RMSE", "Technical Modell", "Technical RMSE", "Technical minus Lag"],
            rows=[
                [
                    row.ticker,
                    row.lag_only_best_model_label,
                    f"{row.lag_only_best_rmse:.4f}",
                    row.technical_extended_best_model_label,
                    f"{row.technical_extended_best_rmse:.4f}",
                    f"{row.technical_minus_lag_rmse:+.4f}",
                ]
                for row in core_per_ticker_frame.itertuples(index=False)
            ],
        ),
        "",
        "## Interpretation",
        "",
        (
            "- Die naive Persistence-Baseline bleibt in beiden Koerben ein harter Referenzwert. "
            "Das ist fuer die Bachelorarbeit methodisch wertvoll, weil dadurch klar wird, "
            "dass komplexere Modelle nicht automatisch bessere Punktprognosen liefern."
        ),
        (
            "- `technical_extended` verbessert den `bachelor_core`-Durchschnitt nur leicht. "
            "Die Feature-Erweiterung ist damit eher ein kontrollierter Feinschliff als ein grosser Leistungssprung."
        ),
        (
            "- Die besten Modelltypen wechseln weiterhin je nach Ticker. "
            "Das spricht gegen eine pauschale Modellwahl und fuer einen empirischen Vergleich pro Datenszenario."
        ),
        (
            f"- Ticker mit Vorteil fuer `technical_extended`: {', '.join(technical_better) if technical_better else 'keine'}."
        ),
        (
            f"- Ticker mit Vorteil fuer `lag_only`: {', '.join(lag_better) if lag_better else 'keine'}."
        ),
    ]

    if tie_tickers:
        lines.append(f"- Unentschieden: {', '.join(tie_tickers)}.")

    lines.extend(
        [
            "",
            "## Modellgewinne im Bachelor-Core-Korb",
            "",
            markdown_table(
                headers=["Profil", "Ridge", "Decision Tree", "Random Forest"],
                rows=[
                    [
                        PROFILE_DISPLAY_NAMES[profile],
                        str(
                            int(
                                model_wins_frame.loc[
                                    (model_wins_frame["feature_profile"] == profile)
                                    & (model_wins_frame["model_name"] == "ridge_regression"),
                                    "win_count",
                                ].iloc[0]
                            )
                        ),
                        str(
                            int(
                                model_wins_frame.loc[
                                    (model_wins_frame["feature_profile"] == profile)
                                    & (model_wins_frame["model_name"] == "decision_tree"),
                                    "win_count",
                                ].iloc[0]
                            )
                        ),
                        str(
                            int(
                                model_wins_frame.loc[
                                    (model_wins_frame["feature_profile"] == profile)
                                    & (model_wins_frame["model_name"] == "random_forest"),
                                    "win_count",
                                ].iloc[0]
                            )
                        ),
                    ]
                    for profile in ["lag_only", "technical_extended"]
                ],
            ),
            "",
        ]
    )

    return "\n".join(lines) + "\n"


def build_summary_payload(
    run_name: str,
    starter_suite_run: str,
    core_profile_run: str,
    starter_suite_frame: pd.DataFrame,
    starter_models_frame: pd.DataFrame,
    core_summary_frame: pd.DataFrame,
    core_per_ticker_frame: pd.DataFrame,
    model_wins_frame: pd.DataFrame,
) -> dict[str, object]:
    best_starter_experiment = starter_suite_frame.iloc[0].to_dict()
    best_core_profile = core_summary_frame.iloc[0].to_dict()

    return {
        "run_name": run_name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_runs": {
            "starter_suite": starter_suite_run,
            "core_profile_comparison": core_profile_run,
        },
        "headline_findings": {
            "starter_best_experiment": best_starter_experiment,
            "core_best_profile": best_core_profile,
            "starter_tickers_beating_baseline": starter_models_frame.loc[
                starter_models_frame["beats_baseline"], "ticker"
            ].tolist(),
            "core_tickers_where_technical_extended_is_better": core_per_ticker_frame.loc[
                core_per_ticker_frame["better_profile"] == "technical_extended", "ticker"
            ].tolist(),
            "core_tickers_where_lag_only_is_better": core_per_ticker_frame.loc[
                core_per_ticker_frame["better_profile"] == "lag_only", "ticker"
            ].tolist(),
        },
        "starter_suite": starter_suite_frame.to_dict(orient="records"),
        "starter_ticker_best_configs": starter_models_frame.to_dict(orient="records"),
        "core_profile_summary": core_summary_frame.to_dict(orient="records"),
        "core_profile_per_ticker": core_per_ticker_frame.to_dict(orient="records"),
        "core_model_wins": model_wins_frame.to_dict(orient="records"),
    }


def main() -> None:
    args = parse_args()
    ensure_runtime_directories()

    starter_suite_path = (
        EXPERIMENT_DATA_DIR / args.starter_suite_run.upper() / "experiment_summary.json"
    )
    core_profile_path = (
        EXPERIMENT_DATA_DIR / args.core_profile_run.upper() / "profile_comparison_summary.json"
    )

    starter_suite_payload = load_json(starter_suite_path)
    core_profile_payload = load_json(core_profile_path)

    starter_suite_frame, starter_models_frame = build_starter_suite_frames(starter_suite_payload)
    core_summary_frame, core_per_ticker_frame = build_core_profile_frames(core_profile_payload)
    model_wins_frame = build_model_win_counts(core_per_ticker_frame)

    artifacts = get_thesis_artifact_paths(args.run_name)
    starter_models_frame.to_csv(artifacts.starter_models_csv, index=False)
    starter_suite_frame.to_csv(artifacts.starter_suite_csv, index=False)
    core_summary_frame.to_csv(artifacts.core_profile_summary_csv, index=False)
    core_per_ticker_frame.to_csv(artifacts.core_profile_per_ticker_csv, index=False)

    save_starter_rmse_plot(artifacts.starter_rmse_plot, starter_models_frame)
    save_core_profile_plot(artifacts.core_profile_plot, core_summary_frame)
    save_core_profile_delta_plot(artifacts.core_profile_delta_plot, core_per_ticker_frame)
    save_model_wins_plot(artifacts.model_wins_plot, model_wins_frame)

    report_text = build_report(
        run_name=args.run_name,
        starter_suite_run=args.starter_suite_run.upper(),
        core_profile_run=args.core_profile_run.upper(),
        starter_suite_frame=starter_suite_frame,
        starter_models_frame=starter_models_frame,
        core_summary_frame=core_summary_frame,
        core_per_ticker_frame=core_per_ticker_frame,
        model_wins_frame=model_wins_frame,
    )
    artifacts.report.write_text(report_text, encoding="utf-8")

    summary_payload = build_summary_payload(
        run_name=args.run_name,
        starter_suite_run=args.starter_suite_run.upper(),
        core_profile_run=args.core_profile_run.upper(),
        starter_suite_frame=starter_suite_frame,
        starter_models_frame=starter_models_frame,
        core_summary_frame=core_summary_frame,
        core_per_ticker_frame=core_per_ticker_frame,
        model_wins_frame=model_wins_frame,
    )
    artifacts.summary_json.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    best_starter_experiment = starter_suite_frame.iloc[0]
    best_core_profile = core_summary_frame.iloc[0]
    technical_better_count = int((core_per_ticker_frame["better_profile"] == "technical_extended").sum())
    lag_better_count = int((core_per_ticker_frame["better_profile"] == "lag_only").sum())

    print(f"Thesis results pack: {args.run_name}")
    print(
        f"Starter best experiment: {best_starter_experiment['experiment_id']} "
        f"(RMSE {best_starter_experiment['mean_best_learned_rmse']:.4f})"
    )
    print(
        f"Best bachelor_core profile: {best_core_profile['feature_profile']} "
        f"(RMSE {best_core_profile['mean_best_learned_rmse']:.4f})"
    )
    print(
        f"technical_extended better for {technical_better_count} tickers, "
        f"lag_only better for {lag_better_count} tickers"
    )
    print(f"Artifacts written to: {artifacts.base_dir}")


if __name__ == "__main__":
    main()
