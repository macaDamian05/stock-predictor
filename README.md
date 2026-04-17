# Stock Predictor

Stand: 2026-04-17

## Projektziel

Dieses Repository ist das aktive Hauptprojekt fuer die Bachelorarbeit. Ziel ist ein System, das historische Boersendaten verarbeitet, daraus Modelle trainiert und fuer ausgewaehlte Aktienkurse Prognosen ableitet. Die aktuelle v1 konzentriert sich auf einen reproduzierbaren Python-ML-Prototyp plus eine spaetere Weboberflaeche in Blazor.

Wichtige Leitlinien:

- `stock-predictor/` ist die einzige aktive Codebasis.
- Die urspruenglichen Colab-Notebooks wurden nach `StockPredictor.ML/notebooks/legacy/` uebernommen und bleiben dort nur als Referenz.
- Persistente Modelle und Scaler werden lokal gespeichert, aber nicht nach Git committed.

## Aktueller Funktionsumfang

Der ML-Prototyp in `StockPredictor.ML/` kann derzeit:

- eine klassische Zeitreihen-Pipeline mit `Persistence-Baseline`, `Ridge Regression`, `Decision Tree` und `RandomForestRegressor` ausfuehren
- historische Kursdaten per CSV oder `yfinance` laden
- Lag-Features ohne Data Leakage erzeugen
- zwischen mehreren Feature-Profilen wie `lag_only`, `technical_basic` und `technical_extended` wechseln
- fuer den klassischen Pfad die naechste Tagesrendite modellieren und daraus den naechsten Schlusskurs ableiten
- einen chronologischen Train/Test-Split fuer die Auswertung nutzen
- technische Features wie Momentum, gleitende Durchschnitte, Volatilitaet und RSI als Eingaben verwenden
- zusaetzlich EMA-Gaps, Breakout-/Drawdown-Abstaende und Preis-Z-Score nutzen
- MSE, RMSE, MAE und Directional Accuracy fuer die Testperiode berechnen
- zusaetzlich ein Walk-Forward-Backtesting mit expandierendem Trainingsfenster durchfuehren
- mehrere gespeicherte Grafiken erzeugen: Kurshistorie, Testvorhersagen und Zukunftsforecast
- zusaetzlich Walk-Forward-Vorhersagen, Fold-Metriken und einen eigenen Walk-Forward-Plot speichern
- mehrere Ticker in einem Benchmark-Lauf vergleichen und gemeinsame Ergebnisdateien erzeugen
- feste Ticker-Koerbe wie `starter`, `bachelor_core` und `bachelor_diversified` verwenden
- ganze Experiment-Suiten ueber mehrere Feature-Profile und Lag-Werte ausfuehren
- aus vorhandenen Benchmark- und Experiment-Runs BA-taugliche Ergebnis-Pakete erzeugen
- Modell, Metriken, Vorhersagen und Prognoseartefakte lokal speichern
- Kursdaten per `yfinance` laden
- pro Ticker ein LSTM-Modell auf Basis von Schlusskursen trainieren
- Modell, Scaler, Metadaten und Trainingslog persistent speichern
- bei neueren Marktdaten ein inkrementelles Weitertraining ausfuehren
- historische Vorhersagen, Zukunftsprognosen, RSI, durchschnittliche Prognose-Steigung sowie einfache Guetemasse ausgeben

Der Webteil in `StockPredictor.App/` ist aktuell noch Projektgeruest und dient als Ziel fuer die spaetere Integration.

## Repository-Struktur

- `StockPredictor.App/`: Blazor-Frontend auf .NET 10
- `StockPredictor.ML/`: Python-Modul mit Training, Prognose und Notebook-Ablage
- `StockPredictor.ML/core/`: fachliche Kernlogik fuer Datenzugriff, Vorverarbeitung, Modellbau und Persistenz
- `StockPredictor.ML/notebooks/legacy/`: archivierte Colab-Quellen
- `StockPredictor.ML/storage/`: lokale Laufzeitdaten wie Modelle, Scaler und Logs
- `docs/project-context.md`: dauerhaftes Projektgedaechtnis fuer spaetere Sessions
- `docs/thesis-notes.md`: BA-relevante Notizen, Forschungsfragen und methodische Hinweise
- `docs/development-history.md`: dokumentierter Entwicklungsverlauf mit frueheren Zwischenstaenden

## Lokales Setup

### Python / ML

Empfohlen ist Python 3.11. Die auf diesem Rechner vorhandene Python-3.14-Installation ist fuer TensorFlow derzeit nicht vorbereitet.

Schnellster Weg fuer den ersten wissenschaftlich sauberen Modellvergleich:

```powershell
cd StockPredictor.ML
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-classical.txt
python run_classical_pipeline.py AAPL
```

Artefakte landen danach unter `StockPredictor.ML/storage/classical/AAPL/`.

PowerShell-Beispiel:

```powershell
cd StockPredictor.ML
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py AAPL
```

Nutzliche Varianten:

```powershell
python run_classical_pipeline.py TSLA --lags 20 --test-size 0.25
python run_classical_pipeline.py DOU.DE --forecast-days 5 --show-plot
python run_classical_pipeline.py AAPL --walk-forward-folds 6 --walk-forward-train-size 0.75
python run_classical_pipeline.py AAPL --feature-profile technical_basic
python run_walk_forward_benchmark.py --basket-preset starter
python run_walk_forward_benchmark.py --basket-preset bachelor_core --feature-profile technical_extended
python run_experiment_suite.py --basket-preset starter
python run_experiment_suite.py --basket-preset bachelor_core --feature-profiles lag_only technical_basic technical_extended --lag-values 5 10
python generate_thesis_results.py
python run_classical_pipeline.py --csv-path .\data\aapl.csv --date-column Date --close-column Close
python main.py TSLA --retrain --forecast-days 10
python main.py ENR.DE --no-plots
```

### .NET / App

Die Blazor-App wurde auf `net10.0` ausgerichtet, damit sie mit dem lokal installierten .NET SDK `10.0.201` gebaut werden kann.

```powershell
dotnet build StockPredictor.slnx
dotnet run --project StockPredictor.App
```

## Persistente Daten

Laufzeit-Artefakte werden pro Ticker unter `StockPredictor.ML/storage/trainingsdaten/<ticker>/` abgelegt:

- `*_lstm_model.keras`: gespeichertes Modell
- `*_scaler.save`: gespeicherter `MinMaxScaler`
- `*_meta.json`: Konfiguration und letzter Datenstand
- `training_log.txt`: Verlauf der Trainings- und Ladeereignisse

Diese Daten bleiben lokal, sind aber in Git ignoriert.

## Dokumentation fuer die Bachelorarbeit

Die aktuell wichtigsten BA-Notizen liegen in:

- `docs/thesis-notes.md`
- `docs/project-context.md`
- `docs/development-history.md`
- `StockPredictor.ML/README.md`
- `StockPredictor.ML/storage/thesis/<run>/thesis_results_report.md`

Diese Dateien sollten bei jeder groesseren fachlichen oder technischen Aenderung aktualisiert werden, damit die Projektgeschichte und die Begruendungen nachvollziehbar bleiben.

## Aktuelle Grenzen

- das Walk-Forward-Backtesting ist aktuell nur fuer den klassischen Pfad umgesetzt
- der klassische Pfad nutzt bisher nur Kurs- und Technikfeatures, noch keine Nachrichten-, Sentiment- oder Fundamentaldaten
- der Benchmark vergleicht aktuell nur einzelne Ticker nacheinander, noch keine gemeinsamen Mehrfachmodelle
- v1 trainiert pro Ticker ein separates Modell
- das Training nutzt aktuell nur den Schlusskurs als Modell-Input
- RSI wird momentan fuer Interpretation genutzt, nicht als Eingangsfeature des Netzes
- ein unternehmensuebergreifendes Ranking ist noch nicht umgesetzt
- ETFs, Nachrichten, Sentiment und Intraday-Daten sind noch Zukunftsthemen

## Aktuelle Beobachtung

Im aktuellen Mehrfachvergleich ueber `AAPL`, `TSLA` und `DOU.DE` ist die naive Persistence-Baseline bei der RMSE weiterhin sehr stark. In der ersten Experimentsuite mit dem `starter`-Korb war `lag_only` mit `10` Lags die beste Konfiguration im Mittel. Im groesseren `bachelor_core`-Vergleich ist `technical_extended` bei den besten gelernten Modellen im Mittel leicht besser als `lag_only`, aber der Abstand ist klein und die Baseline bleibt weiterhin sehr konkurrenzfaehig. Diese Ergebnisse koennen jetzt ueber `generate_thesis_results.py` in ein kompaktes BA-Ergebnispaket ueberfuehrt werden.

## Naechste sinnvolle Schritte

- Experimentsuite auf `bachelor_diversified` ausdehnen
- saubere Train/Validation/Test-Aufteilung nach Zeitachsen weiter verfeinern
- Feature-Sets und Hyperparameter kontrolliert vergleichen
- BA-Ergebnispaket nach groesseren neuen Runs aktualisieren
- Definition einer Schnittstelle zwischen `StockPredictor.ML/` und `StockPredictor.App/`
