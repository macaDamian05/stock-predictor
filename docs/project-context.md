# Project Context

Stand: 2026-04-21

## Kanonische Entscheidungen

- `stock-predictor/` ist das einzige aktive Hauptprojekt.
- Die urspruenglichen Notebooks liegen als Archivkopie in `StockPredictor.ML/notebooks/legacy/`.
- Die aktive ML-Logik lebt in `StockPredictor.ML/`.
- Die aktive App-Logik lebt in `StockPredictor.App/`.
- Modelle, Scaler und Logs werden lokal unter `StockPredictor.ML/storage/trainingsdaten/` abgelegt und nicht committed.
- `credentials.json` aus dem alten lokalen Ordner wird nicht mehr benoetigt.
- feste Ticker-Koerbe liegen in `StockPredictor.ML/core/benchmark_presets.py`

## Aktueller fachlicher Scope

- klassische Zeitreihen-Pipeline fuer den ersten Modellvergleich
- Persistence-Baseline, `Ridge Regression`, `Decision Tree` und `RandomForestRegressor` mit Lag-Features
- Trainingsziel im klassischen Pfad: naechste Tagesrendite, Ausgabe weiterhin als naechster Schlusskurs
- mehrere Feature-Profile: `lag_only`, `technical_basic`, `technical_extended`
- zusaetzliche Features im klassischen Pfad: Momentum, gleitende Durchschnitte, EMA-Gaps, Volatilitaet, Breakout-/Drawdown-Abstaende, Preis-Z-Score und RSI
- CSV- oder Ticker-basierter Datenimport fuer den klassischen Pfad
- chronologischer Train/Test-Split ohne Shuffling
- Walk-Forward-Backtesting mit expandierendem Trainingsfenster fuer den klassischen Pfad
- gespeicherte Diagramme fuer Kurshistorie, Testperiode und Zukunftsforecast
- zusaetzliche gespeicherte Walk-Forward-Metriken, Fold-Ergebnisse und ein Walk-Forward-Plot
- Mehrfachvergleich mehrerer Ticker mit gemeinsamer Benchmark-Zusammenfassung
- reproduzierbare Experiment-Suite ueber mehrere Profile und Lag-Werte
- wiederverwendbarer Profilvergleich ueber mehrere Benchmark-Runs
- konsolidierter Thesis-Export fuer Tabellen, Grafiken und Ergebnisberichte aus vorhandenen Runs
- Dashboard-Handover und erste umgesetzte Blazor-UI unter `storage/dashboard/LATEST/dashboard_payload.json`
- Unternehmensranking fuer die im Dashboard exportierten Ticker auf Basis von Forecast und Modellguete
- rekursiver Forecast im klassischen Pfad baut Features nun konsistent aus der fortgeschriebenen Close-Historie neu auf
- Single-Ticker-Training und -Prognose mit einem LSTM auf Basis historischer Schlusskurse
- persistente Speicherung pro Ticker
- inkrementelles Weitertraining bei neuen Marktdaten
- zusaetzliche Bewertung ueber RSI, durchschnittliche Prognose-Steigung, MAE, RMSE und Directional Accuracy

Noch nicht umgesetzt:

- gemeinsames Training ueber mehrere Aktien
- ETF-Unterstuetzung
- News- oder Sentimentdaten
- Backtesting ueber mehrere Assets und Marktphasen auf Forschungsniveau

Aktuelle empirische Beobachtung:

- Im Benchmark-Korb `AAPL`, `TSLA`, `DOU.DE` bleibt die naive Baseline bei der RMSE insgesamt sehr stark.
- Unter den gelernten Modellen ist aktuell `Ridge Regression` fuer `DOU.DE` und `TSLA` am besten, waehrend bei `AAPL` der `Random Forest` fuehrt.
- In der ersten Experimentsuite auf dem `starter`-Korb war `lag_only` mit `10` Lags die beste Konfiguration im Mittel.
- Im groesseren `bachelor_core`-Vergleich war `technical_extended` bei den besten gelernten Modellen im Mittel leicht besser als `lag_only`, aber nur mit kleinem Abstand.
- Im `bachelor_diversified`-Vergleich zeigt sich dasselbe Muster: `technical_extended` ist im Mittel leicht besser als `lag_only`, obwohl der Vorteil tickerweise nicht einheitlich ist.
- Fuer die App steht jetzt eine kompakte JSON-Schicht bereit. Die UI muss daher nicht direkt mit rohen Benchmark- oder Experimentdateien arbeiten.
- Die erste Blazor-Startseite nutzt diese JSON-Schicht bereits direkt fuer ein dunkles Dashboard mit Kennzahlen, Tickerkarten und Korbvergleich.

## Lokale Umgebungsannahmen

- bevorzugte Python-Version: 3.11
- am Rechner vorhanden am 2026-04-17: Python 3.14.3 global, .NET SDK 10.0.201
- `StockPredictor.App` wurde auf `net10.0` gesetzt, damit der lokale Build funktioniert
- die alte Python-3.9-Umgebung im Archiv ist nicht mehr die Referenz
- fuer den unmittelbar lauffaehigen klassischen Pfad existiert `StockPredictor.ML/requirements-classical.txt`

## Regeln fuer spaetere Aenderungen

- neue fachliche Entscheidungen immer in `README.md` und bei Bedarf in `docs/thesis-notes.md` nachziehen
- groessere Entwicklungsspruenge und verworfene Zwischenstaende auch in `docs/development-history.md` festhalten
- keine Entwicklung mehr direkt im Archivordner `ki-projekt-legacy`
- keine Modelle, Scaler, virtuellen Umgebungen oder Rohdaten in Git committen
- neue Experimente zuerst in `StockPredictor.ML/notebooks/exploration.ipynb`, danach in Python-Module ueberfuehren

## Naechste technische Schritte

- Ergebnisbasis auf weitere Koerbe und eventuell Zeitabschnitte ausdehnen
- Feature-Set weiter testen und dokumentieren
- Thesis-Ergebnispaket nach groesseren neuen Runs aktualisieren
- Dashboard-UI um weitere Detailansichten, Filter und spaetere API-Anbindung erweitern
