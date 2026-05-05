# Future Integrations

Stand: 2026-05-05

## Zweck

Dieses Dokument beschreibt nur konzeptionelle Ausbaupfade fuer spaetere Iterationen des Projekts.
Es ist bewusst keine Anleitung fuer automatisiertes Trading und keine aktive Implementierungszusage fuer Broker-Anbindungen.

## Leitplanken

- aktuell keine Anlageberatung
- aktuell kein automatisches Trading
- aktuell keine Broker-Orders
- aktuell keine TradingView-Webhooks mit echten Kauf- oder Verkaufssignalen
- keine API-Keys oder Secrets im Repository
- ML-Ergebnisse dienen Forschungs- und Demonstrationszwecken

## Moegliche spaetere Erweiterungen

### Nutzerprofile

Moegliche spaetere Profilfunktionen:

- persoenliche Startansicht pro Nutzer
- eigene Watchlists pro Nutzerkonto
- gespeicherte Filter fuer News, Modelle und Dashboard-Ansichten
- persoenliche Einblendung oder Ausblendung einzelner Forschungsbloecke

Technische Konsequenz:

- dafuer waeren spaeter Authentifizierung, Persistenz und ein Datenschutzkonzept noetig
- im aktuellen Bachelorarbeitsstand ist bewusst noch keine Nutzerverwaltung enthalten

### Gespeicherte Watchlists pro Nutzer

Aktuell speichert die App Watchlists nur lokal im Browser.
Ein spaeterer Ausbau koennte ermoeglichen:

- geraeteuebergreifende Watchlists
- manuelle Gruppierung und Sortierung
- Notizen pro Asset

Dafuer waeren mindestens noetig:

- Nutzeridentitaet
- serverseitige Speicherung
- Rechte- und Datenschutzkonzept

### Persoenliche Dashboard-Einstellungen

Moegliche spaetere Einstellungen:

- bevorzugte Surface-Ansicht wie `Nur Kurse` oder `Kurse + Prognose`
- kompakte oder erweiterte Methodikdarstellung
- bevorzugte Ticker- oder ETF-Koerbe
- persoenliche Notification-Praeferenzen

Wichtig:

- diese Einstellungen waeren reine UI-Praeferenzen
- sie duerften keine ML-Logik oder Trainingspfade stillschweigend veraendern

### TradingView-Export oder Watchlist-Export

Ein spaeterer, relativ unkritischer Ausbau koennte sich auf reine Exportfunktionen beschraenken:

- Export vorbereiteter Tickerlisten
- Export lokaler Watchlists in neutrale Formate wie CSV oder TXT
- spaetere Mapping-Schicht fuer TradingView-Watchlists, sofern sie ohne Signallogik bleibt

Wichtig:

- solche Exporte waeren reine Komfortfunktionen fuer Beobachtungslisten
- keine Kauf-, Verkauf- oder Alert-Logik

### Broker-Anbindung nur nach rechtlicher Pruefung

Eine Broker-Anbindung ist im aktuellen Projektstand ausdruecklich nicht enthalten.
Falls so etwas spaeter ueberhaupt betrachtet wird, waere vorher mindestens zu klaeren:

- rechtliche Einordnung der Anwendung
- Abgrenzung zu Anlageberatung und Handelssystemen
- Haftungsfragen
- sichere Secret-Verwaltung
- Audit- und Logging-Konzept
- Nutzerzustimmung und Risikohinweise

Fachliche Konsequenz:

- selbst spaeter waere hoechstens eine passive Depot- oder Beobachtungsintegration ein erster Schritt
- aktive Orderaufgabe waere ein eigenes, deutlich strengeres Teilprojekt

## Empfohlene Architektur fuer spaetere Integrationen

Falls Zukunftsthemen spaeter umgesetzt werden, sollte die Architektur klar getrennt bleiben:

1. `Core Dashboard`
   - bestehende lokale Forschungs- und Visualisierungslogik
2. `User Profile Layer`
   - Einstellungen, Watchlists, UI-Praeferenzen
3. `External Integrations Layer`
   - reine Exporte oder klar getrennte Schnittstellen
4. `Compliance / Security Layer`
   - rechtliche Hinweise, Rechte, Logging, Secret-Verwaltung

Wichtig ist dabei:

- keine Vermischung von Forschungsprognosen mit echter Orderlogik
- keine stillschweigende Aufwertung des Dashboards zu einem Trading-System

## UI-Status im aktuellen Stand

In der App gibt es bewusst nur einen deaktivierten Hinweisbereich fuer spaetere Themen wie:

- `Profile: geplant`
- `TradingView-Export: geplant`
- `Broker-Anbindung: Zukunftsthema`

Diese Hinweise haben aktuell keine technische Wirkung und keine externen API-Verbindungen.
