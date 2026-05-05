# UI Handoff

Stand: 2026-05-05

## Zweck

Dieses Dokument markiert den Uebergang zwischen ML-/Auswertungsteil und der spaeteren Blazor-Oberflaeche.

Die UI muss nicht mehr direkt mit einzelnen Benchmark-, Experiment- oder Forecast-Dateien arbeiten. Stattdessen steht ein kompakter Export bereit, der genau fuer die Oberflaeche gedacht ist.

## Kanonische UI-Datenquelle

Primare Datei fuer die spaetere App:

- `StockPredictor.ML/storage/dashboard/LATEST/dashboard_payload.json`

Ergaenzende Tabellen:

- `StockPredictor.ML/storage/dashboard/LATEST/featured_tickers.csv`
- `StockPredictor.ML/storage/dashboard/LATEST/basket_summary.csv`
- `StockPredictor.ML/storage/dashboard/LATEST/company_ranking.csv`
- `StockPredictor.ML/storage/dashboard/LATEST/multi_asset_summary.csv`

## Inhalt von `dashboard_payload.json`

Die JSON-Datei ist bewusst in wenige Bereiche gegliedert:

- `summary_cards`
  - komprimierte Kernaussagen fuer obere Kennzahlenkarten
  - enthaelt u. a. bestes Starter-Experiment sowie bestes Profil fuer `core` und `diversified`

- `featured_tickers`
  - einzelne Tickerkarten fuer den Einstieg in die App
  - aktuell vorbereitet fuer `AAPL`, `TSLA`, `DOU.DE`
  - enthaelt u. a.:
    - Datenstand je Asset
    - Prognose erzeugt am
    - letzter Schlusskurs
    - naechster prognostizierter Schlusskurs
    - 5-Tage-Horizont
    - Prognosehorizont in Handelstagen
    - durchschnittlicher Forecast-Abstand zum letzten Schlusskurs
    - ausgewaehltes Forecast-Modell
    - verfuegbare Alternativmodelle
    - kompakte Modellmetriken fuer Holdout und Walk-Forward
    - Walk-Forward-RMSE
    - Baseline-RMSE
    - RSI
    - Forecast-Pfad

- `company_ranking`
  - Ranking ueber die exportierten Ticker fuer die direkte Mehrfachbetrachtung
  - kombiniert 5-Tage-Ausblick, relative Walk-Forward-RMSE, Richtungstrefferquote und Abstand zur Baseline
  - enthaelt u. a.:
    - Rang
    - Ranking-Score
    - 5-Tage-Prognoseveraenderung
    - relative RMSE
    - relative Baseline-Differenz
    - RSI

- `multi_asset_summaries`
  - beste gefundene gemeinsame Multi-Asset-Konfiguration pro Korb aus der Multi-Asset-Suite
  - aktuell sinnvoll fuer `mixed_assets` und `etf_core`
  - enthaelt u. a.:
    - bestes Feature-Profil und Lag-Zahl
    - gemeinsames Sieger-Modell
    - gemeinsame RMSE gegen Baseline
    - mittlere 5-Tage-Prognoseveraenderung
    - mittlerer Forecast-Abstand zum letzten Schlusskurs
    - enthaltene Assets im Korb

- `basket_summaries`
  - zusammengefasste Korbvergleiche fuer `bachelor_core` und `bachelor_diversified`
  - sinnvoll fuer Vergleichskarten oder kleine Balkendiagramme

- `notes`
  - kurze methodische Hinweise fuer die UI oder spaetere Beschriftungen

## Empfohlene erste UI-Bausteine

Wenn die Blazor-App als naechstes umgesetzt wird, ist diese Reihenfolge sinnvoll:

1. Kompakter Hero-Bereich ohne lange Theorie
2. Markt-/Watchlist-Kacheln aus `featured_tickers`
3. Umschaltbare Detailflaeche fuer `Kurse` vs. `Prognosen`
4. Optionaler `Modellvergleich` fuer Baseline und gelernte Modelle
5. Benchmark- und Modelluebersicht aus `summary_cards`
6. Multi-Asset- und Korbvergleiche aus `multi_asset_summaries` und `basket_summaries`
7. Methodik nur noch als kompakter Teaser mit Link auf `hinweise`

## Technische Empfehlung fuer die App

- Die Blazor-App sollte zunaechst nur lesend auf `dashboard_payload.json` zugreifen.
- Kein direktes Parsen der rohen Benchmark- oder Thesis-Dateien in der UI.
- Wenn spaeter Live-Aktualisierung gebraucht wird, kann um diese JSON-Datei herum eine API gelegt werden.
- Wenn `dashboard_payload.json` lokal fehlt oder unlesbar ist, sollte die UI einen klaren Leerzustand mit Dateipfad und Export-Befehlen anzeigen statt einfach leer zu wirken.
- Die UI sollte Prognosen immer als zuletzt exportierten Forschungsstand kennzeichnen, nicht als Live-Datenstrom oder Trading-Signal.
- Ein aelterer Export sollte ueber `data_until` und `stale_after_days` sichtbar markiert werden.

## Aktueller Status

Die erste UI-Umsetzung in `StockPredictor.App/` ist erfolgt:

- dunkles Dashboard statt Blazor-Template
- Startseite jetzt marktzentriert statt textlastig
- Asset-Suche direkt auf Basis des vorhandenen Payloads
- lokale Watchlist im Browser für Favoriten
- eigene Detailroute `/assets/<ticker>` für vorbereitete und fehlende Assets
- Watchlist-/Ticker-Kacheln aus `featured_tickers` stehen vor den langen Benchmark-Bloecken
- Toggle fuer `Nur Kurse`, `Kurse + Prognosen` und `Modellvergleich` auf Start- und Detailansicht
- Prognosen sind optisch als Forschungsblock markiert und nicht wie Trading-Signale aufgebaut
- Benchmark- und Multi-Asset-Bloecke bleiben vorhanden, aber weiter unten in der Hierarchie
- direkter Dateizugriff der App auf `dashboard_payload.json` ueber einen kleinen C#-Datendienst
- klarer Fehler-/Leerzustand mit Hinweis auf `cd StockPredictor.ML` und `.\.venv\Scripts\python.exe export_dashboard_payload.py`, falls die lokale Payload fehlt
- unbekannte Ticker werden in der Detailansicht als Platzhalter erklärt, statt ein Training zu erzwingen
- sichtbare Prognose-Metadaten wie Datenstand, Prognosezeitpunkt, Modell/Methode und Prognosehorizont
- kompakter Modellvergleich mit Baseline, Ridge Regression, Decision Tree und Random Forest, falls im Payload vorhanden
- Warnhinweis fuer aeltere Exporte statt stillschweigend veralteter Prognosen
- zentrales Erklaersystem fuer Fachbegriffe ueber kleine Fragezeichen-Tooltips
- ausgebaute `hinweise`-Seite als FAQ- und Glossar-Bereich fuer Kennzahlen, Methoden und Modellbegriffe, dort mit ausgeschriebenen Volltexten statt zusaetzlicher Tooltip-Ueberlagerung
- eigener News-Bereich mit kompakter Startseiten-Vorschau und separater News-Seite
- Mock-News aus serioesen Quellenmustern funktionieren ohne API-Key und sind klar als Demo markiert
- News werden aktuell nur als Kontext gezeigt und nicht automatisch in die Modellprognose uebernommen
- lokale Notification-Schicht fuer optionale Browser-Benachrichtigungen und In-App-Toasts
- Erkennung neuer Exportstaende ueber `generated_at` sowie kompakte Watchlist-Statusmeldungen
- manuelle Testbenachrichtigung bleibt immer zusaetzlich als In-App-Hinweis sichtbar
- keine Server-Push-Infrastruktur und keine Trading-Signale in Benachrichtigungen
- neuer lokaler FAQ-Chat unter `/chat` mit optionaler Ollama-Anbindung
- Fallback auf eingebettete FAQ-/Glossar-Antworten, wenn lokal kein Ollama-Modell verfuegbar ist
- deaktivierter Zukunftsblock fuer `Profile: geplant`, `TradingView-Export: geplant` und `Broker-Anbindung: Zukunftsthema`
- keine funktionalen Trading-APIs oder Broker-Schnittstellen in der aktuellen UI

Die naechsten UI-Schritte sind damit nicht mehr Grundintegration, sondern Ausbau:

- spaetere API-Schicht statt direktem Dateizugriff
- spaetere echte News-API kann ueber die neue Provider-Schnittstelle angeschlossen werden
- Filter, Sortierung und eventuell Chart-Erweiterungen
- spaetere Erweiterung der Suche ueber den aktuellen Payload hinaus
