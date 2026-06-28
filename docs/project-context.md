# Project Context

Stand: 2026-06-28

## Kanonische Entscheidungen

- `stock-predictor/` ist das einzige aktive Hauptprojekt.
- Die urspruenglichen Notebooks liegen als Archivkopie in `StockPredictor.ML/notebooks/legacy/`.
- Die aktive ML-Logik lebt in `StockPredictor.ML/`.
- Die aktive App-Logik lebt in `StockPredictor.App/`.
- Modelle, Scaler und Logs werden lokal unter `StockPredictor.ML/storage/trainingsdaten/` abgelegt und nicht committed.
- `credentials.json` aus dem alten lokalen Ordner wird nicht mehr benoetigt.
- feste Ticker-Koerbe liegen in `StockPredictor.ML/core/benchmark_presets.py`
- fuer den stabilen Hauptpfad wird auf Branch `core-rebuild` eine Core-Version aufgebaut
- halb integrierte Features bleiben als Legacy/Experimental erhalten, sollen aber den Core-Hauptflow nicht bestimmen

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
- gemeinsames klassisches Training ueber mehrere Aktien oder ETFs mit tickerkodierten Identitaetsmerkmalen
- kompakte Multi-Asset-Experimentsuite fuer `mixed_assets`, `etf_core` und weitere feste Koerbe
- reproduzierbare Experiment-Suite ueber mehrere Profile und Lag-Werte
- wiederverwendbarer Profilvergleich ueber mehrere Benchmark-Runs
- konsolidierter Thesis-Export fuer Tabellen, Grafiken und Ergebnisberichte aus vorhandenen Runs
- Dashboard-Handover und erste umgesetzte Blazor-UI unter `storage/dashboard/LATEST/dashboard_payload.json`
- robuster Leerzustand in der Blazor-App, falls `storage/dashboard/LATEST/dashboard_payload.json` auf dem aktuellen Rechner fehlt
- marktzentrierte Startseite mit Watchlist-/Ticker-Kacheln vor den laengeren Forschungs- und Benchmark-Bloecken
- Asset-Suche ueber bekannte Ticker- und Alias-Namen, nicht nur ueber den vorhandenen Dashboard-Payload
- lokale Watchlist im Browser fuer gespeicherte Favoriten
- echte Kursdatenebene fuer Detailseiten, Watchlist und Startkarten ueber einen lokalen Markt-Snapshot-Pfad
- eigene Asset-Detailroute mit historischem Kurschart auch fuer Ticker ohne vorbereitete Prognosedaten
- Toggle auf der Startseite fuer `Kurse` vs. `Prognosen`, wobei Prognosen bewusst als Forschungsblock markiert bleiben
- sichtbarer Prognosekontext in Start- und Detailansicht mit Datenstand, Prognosezeitpunkt, Prognosehorizont und Modell/Methode
- optionaler Modellvergleich fuer Persistence-Baseline und vorhandene gelernte Modelle
- Warnhinweis fuer aeltere Exporte auf Basis von `data_until` und `stale_after_days`
- zentrales Erklaersystem fuer Fachbegriffe, Kennzahlen und Modellnamen in der Blazor-App
- ausgebaute Hinweise-Seite als FAQ- und Glossar-Bereich in einfacher Sprache
- eigener News-Bereich in der Blazor-App mit konfigurierbaren externen RSS-/Atom-Quellen, sauberem Leerzustand und optionalem Demo-Modus
- News dienen aktuell nur als Kontext und fliessen noch nicht in die ML-Prognose ein
- optionale lokale Browser-Benachrichtigungen fuer neue Payloads, aktualisierte Prognosedaten und Watchlist-Assets
- Fallback auf neutrale In-App-Toasts, wenn Browser-Benachrichtigungen nicht erlaubt sind
- Testbenachrichtigung bleibt zusaetzlich immer als sichtbarer In-App-Hinweis erhalten
- lokaler FAQ-Chat mit optionaler Ollama-Anbindung und automatischem Fallback auf eingebettete FAQ-/Glossar-Antworten
- lokaler Profil- und Preference-Layer im Browser fuer Watchlist, Dashboard-Assets, Chart-Zeitraum, Forecast-Anzeige, News-Kategorien und Notification-Praeferenzen
- Profil-Export und -Import als JSON fuer manuelle Rechnerwechsel ohne Login, Datenbank oder Cloud-Synchronisation
- deaktivierter Platzhalter fuer Broker-/TradingView-Zukunftsthemen ohne aktive API-Anbindung
- Unternehmensranking fuer die im Dashboard exportierten Ticker auf Basis von Forecast und Modellguete
- Multi-Asset-Bestkonfigurationen aus der Suite im Dashboard-Export und auf der Startseite sichtbar
- lokale Forecast-Jobs aus der Web-App heraus vorbereitet, inklusive Fallback-Befehlen fuer `run_classical_pipeline.py` und `export_dashboard_payload.py`
- automatische Hintergrund-Aktualisierung fuer veraltete Forecasts, ohne die App zu blockieren
- rekursiver Forecast im klassischen Pfad baut Features nun konsistent aus der fortgeschriebenen Close-Historie neu auf
- Single-Ticker-Training und -Prognose mit einem LSTM auf Basis historischer Schlusskurse
- persistente Speicherung pro Ticker
- inkrementelles Weitertraining bei neuen Marktdaten
- zusaetzliche Bewertung ueber RSI, durchschnittliche Prognose-Steigung, durchschnittlichen Forecast-Abstand zum letzten Schlusskurs, MAE, RMSE und Directional Accuracy
- ETF-Koerbe wie `etf_core` und `etf_sectors` sowie ein gemischter Korb `mixed_assets`
- neuer Core-Orchestrator unter `StockPredictor.ML/core/orchestrator.py`
- Core-Untermodelle unter `StockPredictor.ML/models/`
- Core-Skripte unter `StockPredictor.ML/scripts/` fuer Training, Prediction und Dashboard-Export
- Core-Registry unter `storage/model_registry/`, gespeicherte Modelle unter `storage/trained_models/`, Predictions unter `storage/predictions/`
- Blazor-Hauptnavigation konzentriert sich auf Dashboard, Suche, Kurse, Forecasts und Methodik
- Profile, Watchlist, News, Notifications und FAQ-Chat sind weiterhin vorhanden, aber als Legacy/Experimental vom Core-Hauptflow getrennt

Noch nicht umgesetzt:

- gemeinsames Training im LSTM-Pfad
- LSTM ist noch nicht Teil der stabilen Core-Modellsuite, sondern bleibt Legacy/Research-Pfad
- spezielle ETF-Detaildarstellung im Dashboard jenseits der neuen Multi-Asset-Zusammenfassungen
- Sentimentdaten oder automatische News-Einbindung in die Prognose
- Backtesting ueber mehrere Assets und Marktphasen auf Forschungsniveau

Aktuelle empirische Beobachtung:

- Im Benchmark-Korb `AAPL`, `TSLA`, `DOU.DE` bleibt die naive Baseline bei der RMSE insgesamt sehr stark.
- Unter den gelernten Modellen ist aktuell `Ridge Regression` fuer `DOU.DE` und `TSLA` am besten, waehrend bei `AAPL` der `Random Forest` fuehrt.
- In der ersten Experimentsuite auf dem `starter`-Korb war `lag_only` mit `10` Lags die beste Konfiguration im Mittel.
- Im groesseren `bachelor_core`-Vergleich war `technical_extended` bei den besten gelernten Modellen im Mittel leicht besser als `lag_only`, aber nur mit kleinem Abstand.
- Im `bachelor_diversified`-Vergleich zeigt sich dasselbe Muster: `technical_extended` ist im Mittel leicht besser als `lag_only`, obwohl der Vorteil tickerweise nicht einheitlich ist.
- Fuer die App steht jetzt eine kompakte JSON-Schicht bereit. Die UI muss daher nicht direkt mit rohen Benchmark- oder Experimentdateien arbeiten.
- Die erste Blazor-Startseite nutzt diese JSON-Schicht bereits direkt fuer ein dunkles Dashboard mit Kennzahlen, Tickerkarten und Korbvergleich.
- Im ersten Core-Rebuild-Minilauf fuer `AAPL` wurde die Persistence-Baseline anhand der Validierungs-RMSE als bestes Modell gewaehlt; Ridge und Random Forest bleiben als Vergleichsmodelle mitgespeichert.

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
- Core-Suite fuer mehrere Assets vollstaendig neu trainieren und Dashboard-Payload mit allen gewuenschten Symbolen aktualisieren
- spaetere Integrationen nur getrennt von der Forschungslogik betrachten; siehe `docs/future-integrations.md`
