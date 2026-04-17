# Storage

Dieses Verzeichnis ist fuer lokale Laufzeitdaten vorgesehen.

Erwartete Unterordner:

- `trainingsdaten/<ticker>/` fuer LSTM-Modell, Scaler, Metadaten und Log
- `classical/<source>/` fuer klassische Mehrmodell-Artefakte
- `benchmarks/<run>/` fuer vergleichende Multi-Ticker-Auswertungen
- `experiments/<run>/` fuer ganze Experiment-Suiten ueber mehrere Profile und Lag-Werte
- `thesis/<run>/` fuer konsolidierte BA-taugliche Ergebnispakete
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

Typische Artefakte des Thesis-Exports:

- `starter_model_results.csv`
- `starter_suite_results.csv`
- `core_profile_summary.csv`
- `core_profile_per_ticker.csv`
- `thesis_results_report.md`
- `thesis_results_summary.json`
- mehrere zusammenfassende PNG-Grafiken

Die eigentlichen Modellartefakte sind in Git ignoriert.
