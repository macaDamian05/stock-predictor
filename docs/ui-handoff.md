# UI Handoff

Stand: 2026-04-22

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
    - letzter Schlusskurs
    - naechster prognostizierter Schlusskurs
    - 5-Tage-Horizont
    - durchschnittlicher Forecast-Abstand zum letzten Schlusskurs
    - Forecast-Modell
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

1. Startseite mit 3 bis 5 Kennzahlenkarten aus `summary_cards`
2. Bereich "Unternehmensranking" aus `company_ranking`
3. Bereich "Gemeinsame Multi-Asset-Laeufe" aus `multi_asset_summaries`
4. Bereich "Featured Tickers" aus `featured_tickers`
5. Bereich "Basket Comparison" aus `basket_summaries`
6. Detailansicht fuer einen Ticker mit Forecast-Pfad

## Technische Empfehlung fuer die App

- Die Blazor-App sollte zunaechst nur lesend auf `dashboard_payload.json` zugreifen.
- Kein direktes Parsen der rohen Benchmark- oder Thesis-Dateien in der UI.
- Wenn spaeter Live-Aktualisierung gebraucht wird, kann um diese JSON-Datei herum eine API gelegt werden.

## Aktueller Status

Die erste UI-Umsetzung in `StockPredictor.App/` ist erfolgt:

- dunkles Dashboard statt Blazor-Template
- Startseite mit Kennzahlenkarten aus `summary_cards`
- Unternehmensranking aus `company_ranking`
- Multi-Asset-Bestkonfigurationen aus `multi_asset_summaries`
- Featured-Ticker-Bereich mit interaktiver Auswahl aus `featured_tickers`
- Korbvergleich fuer `bachelor_core` und `bachelor_diversified`
- direkter Dateizugriff der App auf `dashboard_payload.json` ueber einen kleinen C#-Datendienst

Die naechsten UI-Schritte sind damit nicht mehr Grundintegration, sondern Ausbau:

- weitere Detailansichten
- spaetere API-Schicht statt direktem Dateizugriff
- Filter, Sortierung und eventuell Chart-Erweiterungen
