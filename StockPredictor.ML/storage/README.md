# Storage

Dieses Verzeichnis ist fuer lokale Laufzeitdaten vorgesehen.

Nach einem frischen Clone kann dieses Verzeichnis auf einem neuen Rechner teilweise oder ganz fehlen. Das ist erwartetes Verhalten, weil viele Laufzeitdaten lokal erzeugt werden.

Erwartete Unterordner:

- `trainingsdaten/<ticker>/` fuer LSTM-Modell, Scaler, Metadaten und Log
- `classical/<source>/` fuer klassische Mehrmodell-Artefakte
- `benchmarks/<run>/` fuer vergleichende Multi-Ticker-Auswertungen
- `experiments/<run>/` fuer ganze Experiment-Suiten ueber mehrere Profile und Lag-Werte
- `experiments/<run>/` auch fuer konsolidierte Profilvergleiche ueber mehrere Benchmark-Runs
- `thesis/<run>/` fuer konsolidierte BA-taugliche Ergebnispakete
- `dashboard/<run>/` fuer UI-freundliche JSON- und CSV-Exports
- `model_registry/<ticker>/horizon_<n>/` fuer Core-Registry-Dateien mit Modellwahl und Metriken
- `trained_models/<ticker>/horizon_<n>/` fuer gespeicherte Core-Untermodelle
- `predictions/<ticker>/horizon_<n>/` fuer Forecasts aus gespeicherten Core-Modellen
- `plots/` falls spaeter gespeicherte Diagramme abgelegt werden sollen
- `yfinance-cache/` fuer lokale Paket-Caches, damit Datenabrufe reproduzierbar im Projektordner bleiben

Typische Artefakte der klassischen Pipeline:

- `classical_models.joblib`
- `metrics.json`
- `walk_forward_metrics.json`
- `summary.json`
- `predictions.csv`
- `walk_forward_predictions.csv`
- `forecast.json`
- `price_history.png`
- `test_predictions.png`
- `walk_forward_predictions.png`
- `future_forecast.png`

Typische Artefakte des Benchmark-Skripts:

- `benchmark_summary.csv`
- `benchmark_summary.json`
- `benchmark_report.md`
- `benchmark_comparison.png`

Typische Artefakte der Experimentsuite:

- `experiment_summary.csv`
- `experiment_summary.json`
- `experiment_report.md`
- `experiment_comparison.png`
- `ticker_best_configs.csv`

Typische Artefakte eines Profilvergleichs:

- `profile_comparison_summary.csv`
- `profile_comparison_summary.json`
- `profile_comparison_per_ticker.csv`
- `profile_comparison_report.md`
- `profile_comparison_mean_rmse.png`
- `profile_comparison_delta_per_ticker.png`

Typische Artefakte des Thesis-Exports:

- `starter_model_results.csv`
- `starter_suite_results.csv`
- `core_profile_summary.csv`
- `core_profile_per_ticker.csv`
- `thesis_results_report.md`
- `thesis_results_summary.json`
- mehrere zusammenfassende PNG-Grafiken

Typische Artefakte des Dashboard-Exports:

- `dashboard_payload.json`
- `featured_tickers.csv`
- `basket_summary.csv`
- `company_ranking.csv`
- `multi_asset_summary.csv`

Der Payload ist fuer die Blazor-UI gedacht und enthaelt inzwischen neben Kennzahlen auch Prognose-Metadaten wie `generated_at`, `data_until`, `stale_after_days`, `selected_model`, `available_models` und kompakte `model_metrics`.

Typische Artefakte des neuen Core-Rebuild-Pfads:

- `model_registry/<ticker>/horizon_<n>/registry.json`
- `trained_models/<ticker>/horizon_<n>/baseline_persistence.joblib`
- `trained_models/<ticker>/horizon_<n>/ridge_regression.joblib`
- `trained_models/<ticker>/horizon_<n>/random_forest.joblib`
- `predictions/<ticker>/horizon_<n>/latest_prediction.json`

## Blazor-App nach frischem Clone wieder befuellen

Die Blazor-App erwartet standardmaessig:

- `StockPredictor.ML/storage/dashboard/LATEST/dashboard_payload.json`

Wenn diese Datei auf dem aktuellen Rechner fehlt, muss der Dashboard-Export lokal erneut erzeugt werden:

```powershell
cd StockPredictor.ML
.\.venv\Scripts\python.exe export_dashboard_payload.py
```

Wenn der Export danach immer noch nichts schreibt, fehlen typischerweise vorherige lokale Eingaben wie:

- `storage/classical/<ticker>/...`
- `storage/thesis/<run>/thesis_results_summary.json`
- optional `storage/multi_asset_suites/<run>/...`

## Versionierungsregel

Kleine Dokumentationsdateien oder bewusst mitgenommene Demo-/Referenzdaten koennen unter `storage/` versioniert werden.
Lokale Modellartefakte, Scaler, Python-Umgebungen, Cache-Dateien und grosse Laufzeitoutputs sollen dagegen standardmaessig nicht neu Git-ready werden.
