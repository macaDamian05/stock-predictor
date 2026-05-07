# StockPredictor.ML

## Zweck

Dieses Modul ueberfuehrt den frueheren Colab-Prototyp in eine reproduzierbare Python-Struktur innerhalb des Hauptrepositories. Es ist fuer Training, Aktualisierung, Prognose und Auswertung der Modelle verantwortlich.

## Enthaltene Bausteine

- `main.py`: CLI-Einstiegspunkt
- `run_classical_pipeline.py`: erster Bachelorarbeits-tauglicher Einstieg fuer den Vergleich mehrerer klassischer Modelle
- `run_multi_asset_pipeline.py`: gemeinsames klassisches Training ueber mehrere Ticker oder ETFs mit einem geteilten Modell
- `run_multi_asset_experiment_suite.py`: kompakte Vergleichssuite fuer gemeinsame Multi-Asset-Laeufe ueber mehrere Koerbe
- `run_walk_forward_benchmark.py`: Vergleich mehrerer Ticker mit gemeinsamer Walk-Forward-Auswertung
- `run_experiment_suite.py`: reproduzierbare Experimentsuite ueber Koerbe, Feature-Profile und Lag-Werte
- `generate_profile_comparison.py`: konsolidiert mehrere Benchmark-Runs zu einem Profilvergleich
- `generate_thesis_results.py`: konsolidiert vorhandene Experimente zu BA-tauglichen Tabellen, Grafiken und einem Kurzreport
- `export_dashboard_payload.py`: erstellt einen UI-freundlichen JSON- und CSV-Handover fuer die spaetere App, inklusive Datenstand, Prognosezeitpunkt, Modellwahl und Modellvergleich
- `export_market_data.py`: erstellt lokale Markt-Snapshots fuer echte Kursverlaeufe in der Blazor-App, auch ohne vorhandenen Forecast
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

Wenn auf einem anderen Rechner noch kein passendes Python-3.11-Setup vorhanden ist, ist der klassische Pfad der direkt lauffaehige Einstieg:

```powershell
cd StockPredictor.ML
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-classical.txt
python run_classical_pipeline.py AAPL
```

Wichtig: Ein `venv` aendert die Python-Version nicht. Es verwendet immer genau die Python-Version, mit der es angelegt wurde.
Fuer `requirements-classical.txt` hat in einem frischen Rechnerwechsel-Setup auch Python 3.13 funktioniert.
Fuer `requirements.txt` und den LSTM-/TensorFlow-Pfad bleibt Python 3.11 weiterhin die sicherere Wahl.

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

## Schnellstart fuer den vollen LSTM-Pfad

Empfohlen ist Python 3.11:

```powershell
cd StockPredictor.ML
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py AAPL
```

## Hinweise fuer frisches Setup und Rechnerwechsel

- Ein frischer Clone enthaelt standardmaessig nicht alle lokalen Laufzeit-Artefakte unter `storage/`, weil grosse oder klar lokale Outputs in Git ignoriert werden.
- Wenn auf dem neuen Rechner zwar der Code vorhanden ist, aber `storage/classical/`, `storage/thesis/` oder `storage/dashboard/` leer sind, ist das erwartetes Verhalten.
- Fuer einen schnellen Funktionstest zuerst immer den klassischen Einzel-Lauf starten, zum Beispiel `python run_classical_pipeline.py AAPL`.
- Der Dashboard-Export funktioniert erst dann vollstaendig, wenn die benoetigten klassischen Artefakte und der zugehoerige Thesis-Export bereits lokal vorliegen.
- Wenn Marktdaten nicht lokal per CSV geliefert werden, haengen Benchmarks und Experimentsuiten von einer funktionierenden `yfinance`-/Internet-Verbindung ab.
- Bei Netz- oder DNS-Problemen koennen einzelne Ticker in Benchmark-Laeufen fehlschlagen, waehrend andere Ticker desselben Laufs erfolgreich gespeichert werden.

## Blazor-Dashboard nach frischem Clone

Die Blazor-App liest standardmaessig:

- `storage/dashboard/LATEST/dashboard_payload.json`

Wenn diese Datei auf dem aktuellen Rechner fehlt, startet die App jetzt mit einer klaren Leerzustandsmeldung statt mit einer scheinbar kaputten oder leeren Oberflaeche. Fuer echte Kurscharts kann die App zusaetzlich lokale Markt-Snapshots ueber `export_market_data.py` erzeugen, auch wenn noch kein Forecast-Payload vorhanden ist.

Wenn die Datei vorhanden ist, zeigt die UI den zuletzt exportierten ML-Stand. Es gibt bewusst keine garantierte Live-Prognose, sondern eine Leseschicht ueber vorhandene Artefakte.
Wichtige Kennzahlen und Modellbegriffe werden in der App zusaetzlich ueber kleine Tooltips sowie eine FAQ-/Glossar-Seite erklaert.
Ein separater News-Bereich in der App liefert derzeit nur Kontext ueber Demo-Daten und wird noch nicht in die Modelllogik eingespeist.
Zusätzlich kann die App lokale Browser-Benachrichtigungen für neue Exporte und Watchlist-Updates anzeigen; auch diese Hinweise bleiben rein statusbezogen und greifen nicht in die Modelllogik ein.

Ebenfalls rein UI-seitig gibt es jetzt einen lokalen FAQ-Chat mit optionaler Ollama-Anbindung; ohne lokales Modell faellt die App auf einen eingebauten Erklaer-Fallback zurueck.

Typische Befehle zum Wiederbefuellen:

```powershell
cd StockPredictor.ML
.\.venv\Scripts\python.exe export_dashboard_payload.py
.\.venv\Scripts\python.exe export_market_data.py AAPL MSFT ENR.DE
```

Wenn der Export danach immer noch nichts schreibt, fehlen in der Regel vorher lokale Eingaben wie:

- `storage/classical/<ticker>/...`
- `storage/thesis/<run>/thesis_results_summary.json`
- optional `storage/multi_asset_suites/<run>/...`

## Wichtige CLI-Optionen

```powershell
python run_classical_pipeline.py AAPL
python run_classical_pipeline.py TSLA --lags 20 --test-size 0.25
python run_classical_pipeline.py DOU.DE --forecast-days 5 --show-plot
python run_classical_pipeline.py AAPL --walk-forward-folds 6 --walk-forward-train-size 0.75
python run_classical_pipeline.py AAPL --feature-profile technical_basic
python run_multi_asset_pipeline.py --basket-preset mixed_assets
python run_multi_asset_pipeline.py --basket-preset etf_core --feature-profile technical_basic
python run_multi_asset_experiment_suite.py --basket-presets mixed_assets etf_core
python run_walk_forward_benchmark.py --basket-preset starter
python run_walk_forward_benchmark.py --basket-preset bachelor_core --feature-profile technical_extended
python run_experiment_suite.py --basket-preset starter
python run_experiment_suite.py --basket-preset bachelor_core --feature-profiles lag_only technical_basic technical_extended --lag-values 5 10
python generate_profile_comparison.py BACHELOR_DIVERSIFIED_LAG_ONLY BACHELOR_DIVERSIFIED_TECHNICAL_EXTENDED_PART1 BACHELOR_DIVERSIFIED_TECHNICAL_EXTENDED_PART2 --run-name bachelor_diversified_profile_comparison --basket-name bachelor_diversified
python generate_thesis_results.py
python export_dashboard_payload.py
python export_dashboard_payload.py --multi-asset-suite-run latest
python export_dashboard_payload.py AAPL TSLA DOU.DE NVDA SAP.DE
python export_market_data.py AAPL TSLA MSFT NVDA ENR.DE
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
- `--basket-preset`: `starter`, `bachelor_core`, `bachelor_diversified`, `etf_core`, `etf_sectors` oder `mixed_assets`
- `--feature-profile`: Feature-Profil fuer den Benchmark
- `--run-name`: eigener Name fuer den Benchmark-Ordner
- `--walk-forward-folds`, `--walk-forward-train-size`: gleiche Bedeutung wie im Einzel-Lauf
- `--n-estimators`, `--max-depth`, `--min-samples-leaf`: Random-Forest-Konfiguration
- `run_multi_asset_pipeline.py`
- `tickers`: Tickerliste, alternativ ueber `--basket-preset`
- `--basket-preset`: `starter`, `bachelor_core`, `bachelor_diversified`, `etf_core`, `etf_sectors` oder `mixed_assets`
- `--feature-profile`: gemeinsames Feature-Profil fuer alle Assets
- `--lags`: gemeinsame Lag-Zahl fuer alle Assets
- `--forecast-days`: gemeinsamer Forecast-Horizont pro Asset
- `--walk-forward-folds`, `--walk-forward-train-size`: zeitblockbasierte Walk-Forward-Auswertung ueber gemeinsame Zieldaten
- `--run-name`: Zielordner unter `storage/multi_asset/`
- `run_experiment_suite.py`
- `--basket-preset`: fester Ticker-Korb fuer die Suite
- `--feature-profiles`: mehrere Profile in einem Lauf vergleichen
- `--lag-values`: mehrere Lag-Zahlen in einem Lauf vergleichen
- `--run-name`: eigener Name fuer den Suite-Ordner
- `run_multi_asset_experiment_suite.py`
- `--basket-presets`: mehrere Multi-Asset-Koerbe wie `mixed_assets` und `etf_core` in einem Lauf vergleichen
- `--feature-profiles`: gemeinsame Feature-Profile fuer die gepoolten Modelle
- `--lag-values`: gemeinsame Lag-Zahlen fuer die Suite
- `--run-name`: Zielordner unter `storage/multi_asset_suites/`
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
- `--multi-asset-suite-run`: optionaler Multi-Asset-Suite-Stand fuer die Dashboard-Zusammenfassung
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
Dazu gehoert jetzt auch ein Unternehmensranking ueber die exportierten Ticker in `company_ranking.csv` und im JSON-Payload.
Der Payload enthaelt inzwischen zusaetzlich Felder wie `generated_at`, `data_until`, `stale_after_days`, `selected_model`, `available_models`, `model_metrics` und `forecast_horizon_days`, damit die UI Aktualitaet, Methode und Backtest-Qualitaet sichtbar machen kann.
Der neue Multi-Asset-Pfad speichert unter `storage/multi_asset/<run>/` sein gemeinsames Modell, gepoolte Vorhersagen, Per-Ticker-Metriken, Forecast-Zusammenfassungen und einen Report.
Die neue Multi-Asset-Suite speichert unter `storage/multi_asset_suites/<run>/` eine kompakte Vergleichstabelle, Bestkonfigurationen pro Korb, einen Plot und einen Kurzreport.
Der Dashboard-Export uebernimmt diese Bestkonfigurationen optional als `multi_asset_summaries` und als `multi_asset_summary.csv`.

Wichtig fuer den Rechnerwechsel:

- `storage/`-Artefakte sind lokale Laufzeitdaten und werden standardmaessig nicht ueber Git zwischen Rechnern transportiert.
- Eine leere Web-App bedeutet deshalb meist nicht, dass der Export kaputt ist, sondern dass `storage/dashboard/LATEST/dashboard_payload.json` auf diesem Rechner noch nicht erzeugt wurde.
- Benchmark- und Experiment-Zusammenfassungen dokumentieren Teilfehlschlaege in ihren JSON-Dateien, typischerweise unter `failed_tickers`.

## Derzeitiger Modellzuschnitt

- Klassischer Pfad: Persistence-Baseline, `Ridge Regression`, `DecisionTreeRegressor` und `RandomForestRegressor`
- Klassischer Trainingszielwert: naechste Tagesrendite, danach Rueckrechnung in naechsten Schlusskurs
- Klassische Eingabefeatures: je nach Profil nur Lags oder zusaetzlich Momentum, gleitende Durchschnitte, EMA-Gaps, Volatilitaet, Breakout-/Drawdown-Abstaende, Preis-Z-Score und RSI
- Klassische Evaluation: Holdout-Test plus Walk-Forward-Backtesting mit expandierendem Trainingsfenster
- Benchmark-Evaluation: mehrere Ticker mit gemeinsamer Ranking-Tabelle auf Basis der Walk-Forward-Metriken
- Multi-Asset-Evaluation: ein gemeinsames klassisches Modell ueber mehrere Assets mit tickerkodierten Identitaetsmerkmalen und datumsgesteuertem Holdout/Walk-Forward
- Dashboard-Export: Unternehmensranking ueber mehrere Ticker plus Multi-Asset-Bestkonfigurationen auf Basis vorhandener Suite-Runs
- Experimentsuite: Kombinationen aus Koerben, Feature-Profilen und Lag-Werten mit aggregiertem Vergleich
- Klassische Zusatzwerte: RSI, durchschnittliche Forecast-Steigung, durchschnittlicher Forecast-Abstand zum letzten Schlusskurs und 5-Tage-Prognosepfad
- Modelltyp: Single-Layer-LSTM fuer den neuralen Einzelwertpfad
- Trainingssignal: Schlusskurse
- Prognosehorizont: standardmaessig 5 Boersenwerktage
- Zusatzwerte: RSI, durchschnittliche Prognose-Steigung, durchschnittlicher Forecast-Abstand zum letzten Schlusskurs, MAE, RMSE, Directional Accuracy

## Archivierte Notebook-Quellen

Die Original-Notebooks aus dem frueheren lokalen Arbeitsstand liegen unter `notebooks/legacy/`. Neue Experimente sollten in `notebooks/exploration.ipynb` beginnen und danach in die Python-Module ueberfuehrt werden.

## Letzte technische Beobachtung

Der mehrfache Walk-Forward-Vergleich zeigt aktuell: Die naive Persistence-Baseline bleibt bei der RMSE sehr stark, aber die besten gelernten Modelle wechseln je nach Aktie. In der ersten Experimentsuite auf dem `starter`-Korb war `lag_only` mit `10` Lags im Mittel die beste Konfiguration. Im groesseren `bachelor_core`-Vergleich war `technical_extended` bei den besten gelernten Modellen im Mittel leicht besser als `lag_only`, der Vorsprung fiel aber klein aus. Dasselbe Muster zeigt sich inzwischen auch im `bachelor_diversified`-Korb. Der rekursive Forecast-Pfad wurde technisch bereinigt und baut Zukunftsfeatures jetzt konsistent aus der fortgeschriebenen Close-Historie neu auf. Diese Zwischenstaende lassen sich nun mit `generate_profile_comparison.py`, `generate_thesis_results.py` und `export_dashboard_payload.py` in eine BA- und UI-taugliche Ergebniszusammenfassung ueberfuehren.
