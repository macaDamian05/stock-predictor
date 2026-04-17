# Project Context

Stand: 2026-04-17

## Kanonische Entscheidungen

- `stock-predictor/` ist das einzige aktive Hauptprojekt.
- Die urspruenglichen Notebooks liegen als Archivkopie in `StockPredictor.ML/notebooks/legacy/`.
- Die aktive ML-Logik lebt in `StockPredictor.ML/`.
- Die aktive App-Logik lebt in `StockPredictor.App/`.
- Modelle, Scaler und Logs werden lokal unter `StockPredictor.ML/storage/trainingsdaten/` abgelegt und nicht committed.
- `credentials.json` aus dem alten lokalen Ordner wird nicht mehr benoetigt.

## Aktueller fachlicher Scope

- klassische Zeitreihen-Pipeline fuer den ersten Modellvergleich
- Persistence-Baseline und `RandomForestRegressor` mit Lag-Features
- Trainingsziel im klassischen Pfad: naechste Tagesrendite, Ausgabe weiterhin als naechster Schlusskurs
- zusaetzliche Features im klassischen Pfad: Momentum, gleitende Durchschnitte, Volatilitaet und RSI
- CSV- oder Ticker-basierter Datenimport fuer den klassischen Pfad
- chronologischer Train/Test-Split ohne Shuffling
- Walk-Forward-Backtesting mit expandierendem Trainingsfenster fuer den klassischen Pfad
- gespeicherte Diagramme fuer Kurshistorie, Testperiode und Zukunftsforecast
- zusaetzliche gespeicherte Walk-Forward-Metriken, Fold-Ergebnisse und ein Walk-Forward-Plot
- Mehrfachvergleich mehrerer Ticker mit gemeinsamer Benchmark-Zusammenfassung
- Single-Ticker-Training und -Prognose mit einem LSTM auf Basis historischer Schlusskurse
- persistente Speicherung pro Ticker
- inkrementelles Weitertraining bei neuen Marktdaten
- zusaetzliche Bewertung ueber RSI, durchschnittliche Prognose-Steigung, MAE, RMSE und Directional Accuracy

Noch nicht umgesetzt:

- gemeinsames Training ueber mehrere Aktien
- Unternehmensranking
- ETF-Unterstuetzung
- News- oder Sentimentdaten
- Backtesting ueber mehrere Assets und Marktphasen auf Forschungsniveau

## Lokale Umgebungsannahmen

- bevorzugte Python-Version: 3.11
- am Rechner vorhanden am 2026-04-17: Python 3.14.3 global, .NET SDK 10.0.201
- `StockPredictor.App` wurde auf `net10.0` gesetzt, damit der lokale Build funktioniert
- die alte Python-3.9-Umgebung im Archiv ist nicht mehr die Referenz
- fuer den unmittelbar lauffaehigen klassischen Pfad existiert `StockPredictor.ML/requirements-classical.txt`

## Regeln fuer spaetere Aenderungen

- neue fachliche Entscheidungen immer in `README.md` und bei Bedarf in `docs/thesis-notes.md` nachziehen
- keine Entwicklung mehr direkt im Archivordner `ki-projekt-legacy`
- keine Modelle, Scaler, virtuellen Umgebungen oder Rohdaten in Git committen
- neue Experimente zuerst in `StockPredictor.ML/notebooks/exploration.ipynb`, danach in Python-Module ueberfuehren

## Naechste technische Schritte

- Walk-Forward-Ergebnisse ueber mehrere Ticker vergleichen
- Feature-Set weiter testen und dokumentieren
- Benchmark auf groessere Asset-Koerbe erweitern
- Datenaustausch zwischen Python und Blazor sauber definieren
