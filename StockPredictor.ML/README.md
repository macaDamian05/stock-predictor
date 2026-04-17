# StockPredictor.ML

## Zweck

Dieses Modul ueberfuehrt den frueheren Colab-Prototyp in eine reproduzierbare Python-Struktur innerhalb des Hauptrepositories. Es ist fuer Training, Aktualisierung, Prognose und Auswertung der Modelle verantwortlich.

## Enthaltene Bausteine

- `main.py`: CLI-Einstiegspunkt
- `run_classical_pipeline.py`: erster Bachelorarbeits-tauglicher Einstieg fuer Baseline + Random Forest
- `run_walk_forward_benchmark.py`: Vergleich mehrerer Ticker mit gemeinsamer Walk-Forward-Auswertung
- `core/data_loader.py`: Download und Bereinigung der Marktdaten
- `core/preprocessing.py`: Sequenzbildung und Skalierung
- `core/model_factory.py`: Aufbau des LSTM-Modells
- `core/trainer.py`: Persistenz, Metadaten und inkrementelles Weitertraining
- `core/predictor.py`: historische Vorhersagen, Zukunftsprognosen und Metriken
- `core/indicators.py`: RSI-Berechnung
- `core/tabular_features.py`: Lag-Feature-Erzeugung fuer klassische Modelle
- `core/classical_models.py`: Persistence-Baseline und Random Forest

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

- `storage/classical/<source>/random_forest.joblib`
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
python run_walk_forward_benchmark.py
python run_walk_forward_benchmark.py AAPL TSLA DOU.DE --walk-forward-folds 6
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
- `--forecast-days`: Anzahl der zusaetzlich berechneten Boersenwerktage
- `--display-days`: wie viele reale Tage in den Diagrammen sichtbar sein sollen
- `--rsi-window`: Fenster fuer den RSI im klassischen Pfad
- `--test-size`: Groesse des chronologischen Testfensters
- `--walk-forward-folds`: Anzahl der Walk-Forward-Testbloecke, `0` deaktiviert den Modus
- `--walk-forward-train-size`: Groesse des ersten Trainingsfensters fuer Walk-Forward
- `--n-estimators`, `--max-depth`, `--min-samples-leaf`: Random-Forest-Konfiguration
- `--show-plot`: zeigt die gespeicherten Diagramme interaktiv an
- `run_walk_forward_benchmark.py`
- `tickers`: Tickerliste, Standardkorb ist `AAPL`, `TSLA`, `DOU.DE`
- `--run-name`: eigener Name fuer den Benchmark-Ordner
- `--walk-forward-folds`, `--walk-forward-train-size`: gleiche Bedeutung wie im Einzel-Lauf
- `--n-estimators`, `--max-depth`, `--min-samples-leaf`: Random-Forest-Konfiguration
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

## Derzeitiger Modellzuschnitt

- Klassischer Pfad: Persistence-Baseline plus `RandomForestRegressor` auf Lag-Features
- Klassischer Trainingszielwert: naechste Tagesrendite, danach Rueckrechnung in naechsten Schlusskurs
- Klassische Eingabefeatures: Return-Lags, Momentum, gleitende Durchschnitte, Volatilitaet und RSI
- Klassische Evaluation: Holdout-Test plus Walk-Forward-Backtesting mit expandierendem Trainingsfenster
- Benchmark-Evaluation: mehrere Ticker mit gemeinsamer Ranking-Tabelle auf Basis der Walk-Forward-Metriken
- Klassische Zusatzwerte: RSI, durchschnittliche Forecast-Steigung und 5-Tage-Prognosepfad
- Modelltyp: Single-Layer-LSTM
- Trainingssignal: Schlusskurse
- Prognosehorizont: standardmaessig 5 Boersenwerktage
- Zusatzwerte: RSI, durchschnittliche Prognose-Steigung, MAE, RMSE, Directional Accuracy

## Archivierte Notebook-Quellen

Die Original-Notebooks aus dem frueheren lokalen Arbeitsstand liegen unter `notebooks/legacy/`. Neue Experimente sollten in `notebooks/exploration.ipynb` beginnen und danach in die Python-Module ueberfuehrt werden.
