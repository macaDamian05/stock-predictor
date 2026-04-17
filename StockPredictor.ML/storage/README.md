# Storage

Dieses Verzeichnis ist fuer lokale Laufzeitdaten vorgesehen.

Erwartete Unterordner:

- `trainingsdaten/<ticker>/` fuer Modell, Scaler, Metadaten und Log
- `classical/<source>/` fuer Baseline- und Random-Forest-Artefakte
- `benchmarks/<run>/` fuer vergleichende Multi-Ticker-Auswertungen
- `plots/` falls spaeter gespeicherte Diagramme abgelegt werden sollen
- `yfinance-cache/` fuer lokale Paket-Caches, damit Datenabrufe reproduzierbar im Projektordner bleiben

Typische Artefakte der klassischen Pipeline:

- `random_forest.joblib`
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

Die eigentlichen Modellartefakte sind in Git ignoriert.
