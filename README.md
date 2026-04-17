# Stock Predictor

Stand: 2026-04-17

## Projektziel

Dieses Repository ist das aktive Hauptprojekt fuer die Bachelorarbeit. Ziel ist ein System, das historische Boersendaten verarbeitet, daraus Modelle trainiert und fuer ausgewaehlte Aktienkurse Prognosen ableitet. Die aktuelle v1 konzentriert sich auf einen reproduzierbaren Python-ML-Prototyp plus eine spaetere Weboberflaeche in Blazor.

Wichtige Leitlinien:

- `stock-predictor/` ist die einzige aktive Codebasis.
- Der alte lokale Arbeitsstand wurde nach `../ki-projekt-legacy/` archiviert.
- Die urspruenglichen Colab-Notebooks wurden nach `StockPredictor.ML/notebooks/legacy/` uebernommen.
- Persistente Modelle und Scaler werden lokal gespeichert, aber nicht nach Git committed.

## Aktueller Funktionsumfang

Der ML-Prototyp in `StockPredictor.ML/` kann derzeit:

- eine klassische Zeitreihen-Pipeline mit `Persistence-Baseline` und `RandomForestRegressor` ausfuehren
- historische Kursdaten per CSV oder `yfinance` laden
- Lag-Features ohne Data Leakage erzeugen
- fuer den klassischen Pfad die naechste Tagesrendite modellieren und daraus den naechsten Schlusskurs ableiten
- einen chronologischen Train/Test-Split fuer die Auswertung nutzen
- MSE, RMSE, MAE und Directional Accuracy fuer die Testperiode berechnen
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
- `StockPredictor.ML/README.md`

Diese Dateien sollten bei jeder groesseren fachlichen oder technischen Aenderung aktualisiert werden, damit die Projektgeschichte und die Begruendungen nachvollziehbar bleiben.

## Aktuelle Grenzen

- der klassische Pfad nutzt aktuell einen einfachen Holdout-Split, noch kein Walk-Forward-Backtesting
- das erste klassische Modell nutzt nur Lag-Features der Rendite plus den aktuellen Schlusskurs
- v1 trainiert pro Ticker ein separates Modell
- das Training nutzt aktuell nur den Schlusskurs als Modell-Input
- RSI wird momentan fuer Interpretation genutzt, nicht als Eingangsfeature des Netzes
- es gibt noch kein sauberes Walk-Forward-Backtesting
- ein unternehmensuebergreifendes Ranking ist noch nicht umgesetzt
- ETFs, Nachrichten, Sentiment und Intraday-Daten sind noch Zukunftsthemen

## Naechste sinnvolle Schritte

- Walk-Forward-Evaluation fuer den klassischen Pfad
- saubere Train/Validation/Test-Aufteilung nach Zeitachsen
- Erweiterung des Feature-Sets um technische Indikatoren
- Mehrfachvergleich mehrerer Ticker und Aufbau eines Rankings
- Definition einer Schnittstelle zwischen `StockPredictor.ML/` und `StockPredictor.App/`
