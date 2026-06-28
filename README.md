# Stock Predictor

Stand: 2026-05-05

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
- im klassischen Pfad ein gemeinsames Multi-Asset-Training ueber mehrere Ticker mit einem geteilten Modell ausfuehren
- Multi-Asset-Forecasts und Per-Ticker-Auswertungen aus einem gemeinsamen Modell erzeugen
- eine kompakte Multi-Asset-Experimentsuite fuer `mixed_assets` und `etf_core` ausfuehren
- mehrere Ticker im Dashboard-Export gleichzeitig betrachten und daraus ein Unternehmensranking ableiten
- die besten Multi-Asset-Konfigurationen im Dashboard-Export und in der App sichtbar machen
- feste Ticker-Koerbe wie `starter`, `bachelor_core`, `bachelor_diversified`, `etf_core`, `etf_sectors` und `mixed_assets` verwenden
- ganze Experiment-Suiten ueber mehrere Feature-Profile und Lag-Werte ausfuehren
- vorhandene Benchmark-Runs zu Profilvergleichen zusammenfassen
- aus vorhandenen Benchmark- und Experiment-Runs BA-taugliche Ergebnis-Pakete erzeugen
- Modell, Metriken, Vorhersagen und Prognoseartefakte lokal speichern
- Kursdaten per `yfinance` laden
- pro Ticker ein LSTM-Modell auf Basis von Schlusskursen trainieren
- Modell, Scaler, Metadaten und Trainingslog persistent speichern
- bei neueren Marktdaten ein inkrementelles Weitertraining ausfuehren
- historische Vorhersagen, Zukunftsprognosen, RSI, durchschnittliche Prognose-Steigung sowie einfache Guetemasse ausgeben
- zusaetzlich den durchschnittlichen Preisabstand des Forecast-Pfads zum letzten realen Schlusskurs ausgeben

Der Webteil in `StockPredictor.App/` trennt jetzt zwei Ebenen klar voneinander: einen `Market Data Layer` für echte historische Kursdaten und einen `Forecast / Research Layer` für lokale ML-Artefakte aus `dashboard_payload.json`. Dadurch kann die App nicht nur vorbereitete Payload-Ticker anzeigen, sondern auch bekannte Aktien und ETFs wie `AAPL`, `TSLA`, `MSFT`, `NVDA`, `SIE.DE` oder `ENR.DE` direkt suchen, echte Kursverläufe laden und auf der Detailseite als historischen Chart mit `1T`, `1W`, `1M`, `6M`, `1J` und `MAX` darstellen. Forecasts bleiben davon getrennt: Für Prognosen werden Datenstand, Exportzeitpunkt, Prognosehorizont, gewähltes Modell und ein kompakter Modellvergleich sichtbar gemacht. Die UI zeigt bewusst den zuletzt exportierten ML-Stand und keinen garantierten Live-Datenstrom. Wichtige Fachbegriffe lassen sich zusätzlich direkt über kleine Fragezeichen-Tooltips und eine FAQ-/Glossar-Seite erklären. Ergänzend gibt es jetzt einen News-Bereich mit konfigurierbaren externen Quellen. Wenn externe Feeds nicht erreichbar sind, zeigt die App einen sauberen Leerzustand oder klar markierten Demo-Modus statt erfundener Artikel. Lokale Profile speichern Watchlist, Dashboard-Assets, Chart-Zeitraum, Forecast-Anzeige, News-Kategorien und Benachrichtigungseinstellungen nur im Browser. Optional kann die App lokale Browser-Benachrichtigungen für neue Exportstände und Watchlist-Updates auslösen, ohne daraus Handlungsempfehlungen abzuleiten.

Ergaenzend steht jetzt ein lokaler FAQ-Chat zur Verfuegung, der bei erreichbarem Ollama lokal antwortet und sonst automatisch auf einen eingebauten FAQ-/Glossar-Fallback zurueckfaellt.

## Repository-Struktur

- `StockPredictor.App/`: Blazor-Frontend auf .NET 10
- `StockPredictor.ML/`: Python-Modul mit Training, Prognose und Notebook-Ablage
- `StockPredictor.ML/core/`: fachliche Kernlogik fuer Datenzugriff, Vorverarbeitung, Modellbau und Persistenz
- `StockPredictor.ML/notebooks/legacy/`: archivierte Colab-Quellen
- `StockPredictor.ML/storage/`: lokale Laufzeitdaten wie Modelle, Scaler und Logs
- `docs/project-context.md`: dauerhaftes Projektgedaechtnis fuer spaetere Sessions
- `docs/thesis-notes.md`: BA-relevante Notizen, Forschungsfragen und methodische Hinweise
- `docs/development-history.md`: dokumentierter Entwicklungsverlauf mit frueheren Zwischenstaenden
- `docs/ui-handoff.md`: Uebergabedokument fuer die spaetere Blazor-Oberflaeche
- `docs/future-integrations.md`: konzeptionelle Notiz fuer spaetere Profile, Watchlists und moegliche Integrationen ohne Trading-Implementierung

## Lokales Setup

### Python / ML

Empfohlen ist Python 3.11, wenn der volle Pfad inklusive LSTM/TensorFlow genutzt werden soll.
Fuer den klassischen Pfad mit `requirements-classical.txt` hat in einem frischen Rechnerwechsel-Setup auch Python 3.13 funktioniert.
Wichtig: Ein `venv` aendert die Python-Version nicht, sondern uebernimmt genau die Python-Version, mit der es erstellt wurde.

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

Wenn auf einem anderen Rechner kein `py -3.11` vorhanden ist, ist das der sicherste Einstieg, um wenigstens den klassischen Pfad reproduzierbar zum Laufen zu bringen.

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
python run_multi_asset_pipeline.py --basket-preset mixed_assets
python run_multi_asset_pipeline.py --basket-preset etf_core --feature-profile technical_basic
python run_multi_asset_experiment_suite.py --basket-presets mixed_assets etf_core
python run_experiment_suite.py --basket-preset starter
python run_experiment_suite.py --basket-preset bachelor_core --feature-profiles lag_only technical_basic technical_extended --lag-values 5 10
python generate_profile_comparison.py BACHELOR_DIVERSIFIED_LAG_ONLY BACHELOR_DIVERSIFIED_TECHNICAL_EXTENDED_PART1 BACHELOR_DIVERSIFIED_TECHNICAL_EXTENDED_PART2 --run-name bachelor_diversified_profile_comparison --basket-name bachelor_diversified
python generate_thesis_results.py
python export_dashboard_payload.py
python export_dashboard_payload.py --multi-asset-suite-run latest
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

Die Startseite liest den aktuellen Export aus:

- `StockPredictor.ML/storage/dashboard/LATEST/dashboard_payload.json`

Zusätzlich lädt die App für Suchtreffer, Watchlist und Detailseiten echte historische Kursdaten über den lokalen Python-Helfer `StockPredictor.ML/export_market_data.py`. Die UI garantiert weiterhin keine Live-Prognose und kennzeichnet ältere Exporte sichtbar.

### Optional: lokaler FAQ-Chat mit Ollama

Der Chat unter `/chat` funktioniert auch ohne lokales LLM. Standardmaessig nutzt die App `ChatAssistant:Mode = auto` und faellt automatisch auf einen lokalen FAQ-Fallback zurueck, wenn unter `ChatAssistant:OllamaBaseUrl` kein nutzbares Ollama-Modell erreichbar ist.

Typischer lokaler Setup-Pfad:

```powershell
ollama pull llama3.2
ollama serve
dotnet run --project StockPredictor.App
```

Relevante Konfiguration in `StockPredictor.App/appsettings.json`:

- `ChatAssistant:Mode = auto`: bevorzugt Ollama, faellt sonst lokal zurueck
- `ChatAssistant:Mode = ollama`: erwartet ein lokal erreichbares Ollama-Modell
- `ChatAssistant:Mode = mock`: erzwingt den FAQ-Fallback ohne Ollama
- `ChatAssistant:OllamaBaseUrl`: Standard `http://127.0.0.1:11434/`
- `ChatAssistant:OllamaModel`: Standard `llama3.2`

### Frischer Clone: Dashboard wieder befuellen

Wenn die Blazor-App nach einem frischen Clone leer startet, ist meist nicht die UI kaputt, sondern die lokale Datei
`StockPredictor.ML/storage/dashboard/LATEST/dashboard_payload.json` fehlt auf diesem Rechner.

Typischer Minimalablauf:

```powershell
cd StockPredictor.ML
.\.venv\Scripts\python.exe export_dashboard_payload.py
cd ..
dotnet run --project StockPredictor.App
```

Die App zeigt bei fehlender Datei jetzt bewusst einen klaren Leerzustand mit:

- dem erwarteten Dateipfad
- dem Hinweis auf lokal zu erzeugende ML-Artefakte
- den typischen Befehlen `cd StockPredictor.ML` und `.\.venv\Scripts\python.exe export_dashboard_payload.py`
- einem Button `Datenstatus prüfen`

Die App bietet zusätzlich:

- eine Asset-Suche über bekannte Ticker- und Alias-Namen, nicht nur über den vorhandenen Dashboard-Payload
- eine lokale Watchlist im Browser für Favoriten
- Detailseiten unter `/assets/<ticker>`
- einen historischen Kurschart pro Asset mit `1T`, `1W`, `1M`, `6M`, `1J` und `MAX`
- einen stabilen Kursmodus auch für Ticker ohne vorbereitete Prognosedaten statt einer Platzhalter-Sackgasse
- eine lokale Aktion `Prognose für dieses Asset erzeugen` oder `Forecast aktualisieren` inklusive Fallback-Befehlen
- automatische Hintergrund-Aktualisierung für veraltete Forecasts, ohne die App zu blockieren
- sichtbare Prognose-Metadaten wie Datenstand, `Prognose erzeugt am`, Horizont und Modell/Methode
- einen Toggle für `Nur Kurse`, `Kurse + Prognose` und `Modellvergleich`
- einen Warnhinweis, wenn eine Prognose auf einem älteren Export basiert
- kleine Fragezeichen-Tooltips für wichtige Kennzahlen und Modellbegriffe
- eine erweiterte `Hinweise`-Seite als FAQ- und Glossar-Bereich in einfacher Sprache, dort direkt mit Volltext statt überlagerndem Tooltip
- einen News-Bereich mit Kategorie- und optionalem Ticker-Filter
- konfigurierbare externe RSS-/Atom-Quellen ohne hardcodierte API-Schlüssel
- einen sauberen Leerzustand oder klar markierten Demo-Modus, wenn externe Quellen nicht erreichbar sind
- den Hinweis, dass News aktuell nur als Kontext dienen und noch nicht im Modell verwendet werden
- ein lokales Profil unter `/profile` fuer Watchlist, bevorzugte Dashboard-Assets, Standard-Chart-Zeitraum, Forecast-Anzeige, News-Kategorien und Notification-Praeferenzen
- Profil-Export und -Import als JSON fuer manuelle Rechnerwechsel ohne Login oder Cloud
- optionale lokale Browser-Benachrichtigungen für neue Payloads, aktualisierte Prognosedaten und Watchlist-Änderungen
- neutrale In-App-Toasts als Fallback, wenn Browser-Benachrichtigungen nicht erlaubt sind
- eine Testbenachrichtigung, die immer zusaetzlich als In-App-Hinweis sichtbar bleibt
- einen lokalen FAQ-Chat unter `/chat` mit thematischer Begrenzung auf Dashboard, Kennzahlen, Modelle, Methoden und Bachelorarbeitskontext
- automatischen Fallback auf lokale FAQ-Antworten, wenn Ollama fehlt oder nicht erreichbar ist

Nach einem frischen Clone oder einem Rechnerwechsel ist die Web-App oft zunaechst leer.
Der Grund ist in der Regel nicht Blazor, sondern fehlende lokale Laufzeit-Artefakte unter `StockPredictor.ML/storage/`.
Viele dieser lokalen Laufzeit-Artefakte sind standardmaessig in Git ignoriert und werden deshalb nicht automatisch auf einen zweiten Rechner mitgenommen.

Wenn die App keine Daten findet oder die UI aktualisiert werden soll und die benoetigten ML-Artefakte bereits lokal vorhanden sind:

```powershell
cd StockPredictor.ML
.\.venv\Scripts\python.exe export_dashboard_payload.py
```

Der reine Dashboard-Export setzt vorher mindestens diese lokalen Eingaben voraus:

- `StockPredictor.ML/storage/classical/<ticker>/...` fuer die Featured Ticker
- `StockPredictor.ML/storage/thesis/<run>/thesis_results_summary.json` fuer die Korb- und Thesis-Zusammenfassung
- optional `StockPredictor.ML/storage/multi_asset_suites/<run>/...` fuer den Multi-Asset-Abschnitt

Wenn diese Ordner auf dem aktuellen Rechner fehlen, muss zuerst die ML-Pipeline lokal neu ausgefuehrt oder ein bereits erzeugter `storage/`-Stand uebernommen werden.

Wenn nur die Kursdatenansicht fuer ein Asset getestet werden soll, ohne gleich einen kompletten Dashboard-Export anzufassen:

```powershell
cd StockPredictor.ML
.\.venv\Scripts\python.exe export_market_data.py AAPL MSFT ENR.DE
```

Wenn die neuen gemeinsamen Aktien-/ETF-Laeufe mit im Dashboard auftauchen sollen:

```powershell
cd StockPredictor.ML
.\.venv\Scripts\python.exe run_multi_asset_experiment_suite.py --basket-presets mixed_assets etf_core --run-name latest
.\.venv\Scripts\python.exe export_dashboard_payload.py --multi-asset-suite-run latest
```

## Bekannte Stolpersteine beim Rechnerwechsel

- `.gitignore` versteckt keine Dateien im Explorer. Wenn `StockPredictor.ML/storage/dashboard/` oder `storage/thesis/` lokal fehlen, wurden sie auf diesem Rechner schlicht noch nicht erzeugt oder kopiert.
- Die Web-App kann erfolgreich starten und trotzdem leer sein, wenn `StockPredictor.ML/storage/dashboard/LATEST/dashboard_payload.json` noch nicht existiert.
- Ein `venv` loest kein Versionsproblem von selbst. Wer ein `venv` mit `Python 3.13` erstellt, bekommt auch ein `Python-3.13-venv`; fuer den LSTM-/TensorFlow-Pfad bleibt `Python 3.11` vorerst die sicherere Wahl.
- Die klassischen Benchmark- und Experiment-Skripte laden Marktdaten ueber `yfinance`. Bei instabilem Internet oder DNS-Problemen koennen einzelne Ticker fehlschlagen, waehrend der Rest des Laufs trotzdem Artefakte schreibt.
- Teilfehlschlaege durch `yfinance` stehen danach in den jeweiligen Summary-Dateien unter `failed_tickers`, zum Beispiel in `storage/benchmarks/<run>/benchmark_summary.json`.
- Wenn das Dashboard auf mehreren Rechnern sofort sichtbar sein soll, muessen die benoetigten Exportdateien entweder lokal neu erzeugt oder gezielt ausserhalb des Standard-Ignore-Verhaltens mitgenommen werden.

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
- `docs/ui-handoff.md`
- `docs/future-integrations.md`

Diese Dateien sollten bei jeder groesseren fachlichen oder technischen Aenderung aktualisiert werden, damit die Projektgeschichte und die Begruendungen nachvollziehbar bleiben.

## Aktuelle Grenzen

- das Walk-Forward-Backtesting ist aktuell nur fuer den klassischen Pfad umgesetzt
- der klassische Pfad nutzt bisher nur Kurs- und Technikfeatures, noch keine Nachrichten-, Sentiment- oder Fundamentaldaten
- der LSTM-Pfad trainiert weiterhin pro Ticker separat
- das Training nutzt aktuell nur den Schlusskurs als Modell-Input
- RSI wird momentan fuer Interpretation genutzt, nicht als Eingangsfeature des Netzes
- spezielle ETF-Detaildarstellungen im Dashboard sowie Nachrichten, Sentiment und Intraday-Daten sind noch Zukunftsthemen

## Aktuelle Beobachtung

Im aktuellen Mehrfachvergleich ueber `AAPL`, `TSLA` und `DOU.DE` ist die naive Persistence-Baseline bei der RMSE weiterhin sehr stark. In der ersten Experimentsuite mit dem `starter`-Korb war `lag_only` mit `10` Lags die beste Konfiguration im Mittel. Im groesseren `bachelor_core`-Vergleich ist `technical_extended` bei den besten gelernten Modellen im Mittel leicht besser als `lag_only`, aber der Abstand ist klein und die Baseline bleibt weiterhin sehr konkurrenzfaehig. Dieses Muster bestaetigt sich auch im `bachelor_diversified`-Korb: `technical_extended` ist im Mittel leicht besser als `lag_only`, obwohl es tickerweise nur bei `4` von `10` Werten vorne liegt. Diese Ergebnisse koennen jetzt ueber `generate_thesis_results.py`, `generate_profile_comparison.py` und `export_dashboard_payload.py` sauber weiterverarbeitet werden. Fuer die spaetere App steht damit ein eigener Handover unter `StockPredictor.ML/storage/dashboard/LATEST/dashboard_payload.json` bereit.

## Naechste sinnvolle Schritte

- Dashboard um weitere Detailansichten, Filter und spaetere API-Anbindung erweitern
- saubere Train/Validation/Test-Aufteilung nach Zeitachsen weiter verfeinern
- Feature-Sets und Hyperparameter kontrolliert vergleichen
- BA-Ergebnispaket und Dashboard-Export nach groesseren neuen Runs aktualisieren
