# StockPredictor.ML

## Zweck

Dieses Modul ueberfuehrt den frueheren Colab-Prototyp in eine reproduzierbare Python-Struktur innerhalb des Hauptrepositories. Es ist fuer Training, Aktualisierung, Prognose und Auswertung der Modelle verantwortlich.

## Enthaltene Bausteine

- `main.py`: CLI-Einstiegspunkt
- `run_classical_pipeline.py`: erster Bachelorarbeits-tauglicher Einstieg fuer den Vergleich mehrerer klassischer Modelle
- `run_walk_forward_benchmark.py`: Vergleich mehrerer Ticker mit gemeinsamer Walk-Forward-Auswertung
- `run_experiment_suite.py`: reproduzierbare Experimentsuite ueber Koerbe, Feature-Profile und Lag-Werte
- `generate_profile_comparison.py`: konsolidiert mehrere Benchmark-Runs zu einem Profilvergleich
- `generate_thesis_results.py`: konsolidiert vorhandene Experimente zu BA-tauglichen Tabellen, Grafiken und einem Kurzreport
- `export_dashboard_payload.py`: erstellt einen UI-freundlichen JSON- und CSV-Handover fuer die spaetere App
- `core/benchmark_presets.py`: feste Ticker-Koerbe fuer Starter- und Bachelor-Laeufe
- `core/data_loader.py`: Download und Bereinigung der Marktdaten
- `core/preprocessing.py`: Sequenzbildung und Skalierung
- `core/model_factory.py`: Aufbau des LSTM-Modells
- `core/trainer.py`: Persistenz, Metadaten und inkrementelles Weitertraining
- `core/predictor.py`: historische Vorhersagen, Zukunftsprognosen und Metriken
- `core/indicators.py`: RSI-Berechnung
- `core/tabular_features.py`: Lag-Feature-Erzeugung fuer klassische Modelle
- `core/classical_models.py`: Persistence-Baseline, Ridge Regression, Decision Tree und Random Forest

## Erster sinnvoller Startpfad

Da lokal aktuell nur Python 3.14 vorhanden ist, ist der klassische Pfad der direkt lauffaehige Einstieg:

```powershell
cd StockPredictor.ML
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-classical.txt
python run_classical_pipeline.py AAPL
```

Beispiel mit CSV:

```powershell
python run_classical_pipeline.py --csv-path .\data\aapl.csv --date-column Date --close-column Close
```

Der Lauf erzeugt:

- `storage/classical/<source>/classical_models.joblib`
- `storage/classical/<source>/metrics.json`
- `storage/classical/<source>/walk_forward_metrics.json`
- `storage/classical/<source>/summary.json`
- `storage/classical/<source>/predictions.csv`
- `storage/classical/<source>/walk_forward_predictions.csv`
- `storage/classical/<source>/forecast.json`
- `storage/classical/<source>/price_history.png`
- `storage/classical/<source>/test_predictions.png`
- `storage/classical/<source>/walk_forward_predictions.png`
- `storage/classical/<source>/future_forecast.png`

Der klassische Pfad trainiert auf der naechsten Tagesrendite und rechnet diese Vorhersage fuer Reporting und Visualisierung wieder in einen naechsten Schlusskurs um. Das ist fuer lange Kursreihen stabiler als ein direktes Lernen auf absoluten Preisniveaus. Standardmaessig werden sowohl ein einfacher Holdout-Test als auch ein Walk-Forward-Backtesting gerechnet.

## Schnellstart

Empfohlen ist Python 3.11:

```powershell
cd StockPredictor.ML
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py AAPL
```

## Wichtige CLI-Optionen

```powershell
python run_classical_pipeline.py AAPL
python run_classical_pipeline.py TSLA --lags 20 --test-size 0.25
python run_classical_pipeline.py DOU.DE --forecast-days 5 --show-plot
python run_classical_pipeline.py AAPL --walk-forward-folds 6 --walk-forward-train-size 0.75
python run_classical_pipeline.py AAPL --feature-profile technical_basic
python run_walk_forward_benchmark.py --basket-preset starter
python run_walk_forward_benchmark.py --basket-preset bachelor_core --feature-profile technical_extended
python run_experiment_suite.py --basket-preset starter
python run_experiment_suite.py --basket-preset bachelor_core --feature-profiles lag_only technical_basic technical_extended --lag-values 5 10
python generate_profile_comparison.py BACHELOR_DIVERSIFIED_LAG_ONLY BACHELOR_DIVERSIFIED_TECHNICAL_EXTENDED_PART1 BACHELOR_DIVERSIFIED_TECHNICAL_EXTENDED_PART2 --run-name bachelor_diversified_profile_comparison --basket-name bachelor_diversified
python generate_thesis_results.py
python export_dashboard_payload.py
python run_classical_pipeline.py --csv-path .\data\aapl.csv --date-column Date --close-column Close
python main.py AAPL
python main.py TSLA --retrain
python main.py ENR.DE --forecast-days 10 --lookback-days 120
python main.py AAPL --no-plots
```

Verfuegbare Parameter:

- `run_classical_pipeline.py`
- `ticker` oder `--csv-path`: Datenquelle
- `--lags`: Anzahl verwendeter Lag-Features
- `--feature-profile`: `lag_only`, `technical_basic` oder `technical_extended`
- `--forecast-days`: Anzahl der zusaetzlich berechneten Boersenwerktage
- `--display-days`: wie viele reale Tage in den Diagrammen sichtbar sein sollen
- `--rsi-window`: Fenster fuer den RSI im klassischen Pfad
- `--test-size`: Groesse des chronologischen Testfensters
- `--walk-forward-folds`: Anzahl der Walk-Forward-Testbloecke, `0` deaktiviert den Modus
- `--walk-forward-train-size`: Groesse des ersten Trainingsfensters fuer Walk-Forward
- `--ridge-alpha`: Regularisierung fuer Ridge Regression
- `--tree-max-depth`, `--tree-min-samples-leaf`: Konfiguration des Decision Tree
- `--n-estimators`, `--max-depth`, `--min-samples-leaf`: Random-Forest-Konfiguration
- `--show-plot`: zeigt die gespeicherten Diagramme interaktiv an
- `run_walk_forward_benchmark.py`
- `tickers`: Tickerliste, alternativ ueber `--basket-preset`
- `--basket-preset`: `starter`, `bachelor_core` oder `bachelor_diversified`
- `--feature-profile`: Feature-Profil fuer den Benchmark
- `--run-name`: eigener Name fuer den Benchmark-Ordner
- `--walk-forward-folds`, `--walk-forward-train-size`: gleiche Bedeutung wie im Einzel-Lauf
- `--n-estimators`, `--max-depth`, `--min-samples-leaf`: Random-Forest-Konfiguration
- `run_experiment_suite.py`
- `--basket-preset`: fester Ticker-Korb fuer die Suite
- `--feature-profiles`: mehrere Profile in einem Lauf vergleichen
- `--lag-values`: mehrere Lag-Zahlen in einem Lauf vergleichen
- `--run-name`: eigener Name fuer den Suite-Ordner
- `generate_profile_comparison.py`
- `benchmark_runs`: eine oder mehrere Benchmark-Run-Ordner unter `storage/benchmarks/`
- `--run-name`: Zielordner unter `storage/experiments/`
- `--basket-name`: Anzeigename fuer den verglichenen Korb
- `generate_thesis_results.py`
- `--starter-suite-run`: Quellexperiment fuer die Starter-Zusammenfassung
- `--core-profile-run`: Quelle fuer den `bachelor_core`-Profilvergleich
- `--diversified-profile-run`: Quelle fuer den `bachelor_diversified`-Profilvergleich
- `--run-name`: Zielordner unter `storage/thesis/`
- `export_dashboard_payload.py`
- `tickers`: Featured-Ticker fuer den spaeteren App-Einstieg
- `--thesis-run`: Quelle fuer den konsolidierten Thesis-Stand
- `--run-name`: Zielordner unter `storage/dashboard/`
- `ticker`: Tickersymbol, optional auch interaktiv
- `--retrain`: neues Volltraining statt Laden/Weitertrainieren
- `--start-date` und `--end-date`: Datenbereich
- `--lookback-days`: Eingabefenster fuer das Modell
- `--forecast-days`: Prognosehorizont in Boersenwerktagen
- `--display-days`: Anzahl der Tage im Verlauf-Plot
- `--lstm-units`: Groesse der LSTM-Schicht
- `--epochs` und `--batch-size`: Trainingsparameter
- `--rsi-window`: Fenster fuer den RSI
- `--no-plots`: deaktiviert Matplotlib-Fenster

## Laufzeit-Artefakte

Pro Ticker werden gespeichert:

- `*_lstm_model.keras`
- `*_scaler.save`
- `*_meta.json`
- `training_log.txt`

Alle diese Dateien landen in `storage/trainingsdaten/<ticker>/`.

Zusatzlich speichert die klassische Pipeline unter `storage/classical/<source>/` ihr Modell, Metriken, Testvorhersagen, eine Forecast-Zusammenfassung und mehrere Diagramme.

Das Benchmark-Skript speichert unter `storage/benchmarks/<run>/` eine CSV-, JSON- und Markdown-Zusammenfassung sowie einen Vergleichsplot ueber mehrere Ticker.

Die Experimentsuite speichert unter `storage/experiments/<run>/` aggregierte Ergebnis-CSV/JSON-Dateien, einen BA-tauglichen Markdown-Report, einen Vergleichsplot und eine Tabelle mit den besten Konfigurationen pro Ticker.

Der Profilvergleich speichert ebenfalls unter `storage/experiments/<run>/` eine zusammengefuehrte CSV-/JSON-Zusammenfassung, eine tickerweise Differenztabelle, einen Kurzreport und passende Vergleichsplots.

Der Thesis-Export speichert unter `storage/thesis/<run>/` eine kompakte Ergebnisbasis fuer die Arbeit: konsolidierte CSV-Dateien, einen Markdown-Report, eine JSON-Zusammenfassung und mehrere zusammenfassende Diagramme.

Der Dashboard-Export speichert unter `storage/dashboard/<run>/` eine UI-freundliche JSON-Datei sowie ergaenzende CSVs. Diese Schicht dient als Handover fuer die spaetere Blazor-App.

## Derzeitiger Modellzuschnitt

- Klassischer Pfad: Persistence-Baseline, `Ridge Regression`, `DecisionTreeRegressor` und `RandomForestRegressor`
- Klassischer Trainingszielwert: naechste Tagesrendite, danach Rueckrechnung in naechsten Schlusskurs
- Klassische Eingabefeatures: je nach Profil nur Lags oder zusaetzlich Momentum, gleitende Durchschnitte, EMA-Gaps, Volatilitaet, Breakout-/Drawdown-Abstaende, Preis-Z-Score und RSI
- Klassische Evaluation: Holdout-Test plus Walk-Forward-Backtesting mit expandierendem Trainingsfenster
- Benchmark-Evaluation: mehrere Ticker mit gemeinsamer Ranking-Tabelle auf Basis der Walk-Forward-Metriken
- Experimentsuite: Kombinationen aus Koerben, Feature-Profilen und Lag-Werten mit aggregiertem Vergleich
- Klassische Zusatzwerte: RSI, durchschnittliche Forecast-Steigung und 5-Tage-Prognosepfad
- Modelltyp: Single-Layer-LSTM
- Trainingssignal: Schlusskurse
- Prognosehorizont: standardmaessig 5 Boersenwerktage
- Zusatzwerte: RSI, durchschnittliche Prognose-Steigung, MAE, RMSE, Directional Accuracy

## Archivierte Notebook-Quellen

Die Original-Notebooks aus dem frueheren lokalen Arbeitsstand liegen unter `notebooks/legacy/`. Neue Experimente sollten in `notebooks/exploration.ipynb` beginnen und danach in die Python-Module ueberfuehrt werden.

## Letzte technische Beobachtung

Der mehrfache Walk-Forward-Vergleich zeigt aktuell: Die naive Persistence-Baseline bleibt bei der RMSE sehr stark, aber die besten gelernten Modelle wechseln je nach Aktie. In der ersten Experimentsuite auf dem `starter`-Korb war `lag_only` mit `10` Lags im Mittel die beste Konfiguration. Im groesseren `bachelor_core`-Vergleich war `technical_extended` bei den besten gelernten Modellen im Mittel leicht besser als `lag_only`, der Vorsprung fiel aber klein aus. Dasselbe Muster zeigt sich inzwischen auch im `bachelor_diversified`-Korb. Der rekursive Forecast-Pfad wurde technisch bereinigt und baut Zukunftsfeatures jetzt konsistent aus der fortgeschriebenen Close-Historie neu auf. Diese Zwischenstaende lassen sich nun mit `generate_profile_comparison.py`, `generate_thesis_results.py` und `export_dashboard_payload.py` in eine BA- und UI-taugliche Ergebniszusammenfassung ueberfuehren.
