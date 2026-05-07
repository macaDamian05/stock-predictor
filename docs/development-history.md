# Development History

Stand: 2026-05-05

## Zweck dieses Dokuments

Dieses Dokument haelt die Entwicklung des Projekts bewusst als Verlauf fest und nicht nur als aktuellen Endstand. Fuer die Bachelorarbeit ist das wichtig, weil nachvollziehbar bleiben soll:

- mit welchem Prototyp gestartet wurde
- welche Probleme oder Grenzen frueh sichtbar wurden
- welche technischen und methodischen Verbesserungen spaeter eingefuehrt wurden
- welche Zwischenstaende sich als weniger geeignet erwiesen

Ein frueherer Zwischenstand ist daher nicht "falsch", sondern Teil des Entwicklungswegs.

## Phase 1: Colab- und Notebook-Prototyp

Ausgangspunkt war ein Google-Colab-/Notebook-Ansatz mit:

- Jupyter-Notebooks als Arbeitsumgebung
- Fokus auf historischen Schlusskursen
- erstem LSTM-basierten Prognosepfad
- direkter Visualisierung und experimentellem Vorgehen

Staerken dieses Schritts:

- schneller fachlicher Einstieg
- erste lauffaehige Vorhersagen
- gute Explorationsumgebung fuer Ideen

Grenzen dieses Schritts:

- geringe Reproduzierbarkeit
- wenig klare Trennung zwischen Daten, Modelllogik und Visualisierung
- fuer eine Bachelorarbeit methodisch und organisatorisch noch zu lose

## Phase 2: Migration in das Hauptrepository

Anschliessend wurde `stock-predictor/` als einziges Hauptprojekt festgelegt. Die alten Notebooks wurden nach `StockPredictor.ML/notebooks/legacy/` uebernommen.

Ziel dieser Phase:

- klare Projektstruktur
- Trennung von Python-ML und spaeterer UI
- bessere Nachvollziehbarkeit in Git und Dokumentation

Wichtige Entscheidung:

- der alte lokale Arbeitsstand wird nicht mehr aktiv weiterentwickelt, sondern nur noch als Referenz betrachtet

## Phase 3: Erster klassischer Modellpfad

Nach der Migration wurde ein erster klassischer Zeitreihenpfad aufgebaut mit:

- `Persistence-Baseline`
- `RandomForestRegressor`
- chronologischem Holdout-Split
- Vorhersage der naechsten Tagesrendite
- Rueckrechnung in den naechsten Schlusskurs

Warum dieser Schritt wichtig war:

- wissenschaftlich leichter zu begruenden als ein frueher reiner Notebook-Prototyp
- einfacher zu testen, zu dokumentieren und mit Baselines zu vergleichen

Erste Beobachtung:

- der Random Forest lieferte oft bessere Richtungssignale
- die naive Baseline blieb bei der RMSE jedoch erstaunlich stark

Diese Beobachtung war fachlich wertvoll, weil sie gezeigt hat, dass ein "komplexeres" Modell nicht automatisch die bessere Punktprognose liefert.

## Phase 4: Walk-Forward-Backtesting

Danach wurde zusaetzlich zum Holdout-Test ein Walk-Forward-Backtesting eingefuehrt.

Verbesserung gegenueber dem frueheren Stand:

- realistischere Bewertung ueber mehrere Zeitfenster
- sauberere Aussage zu Generalisierung und Stabilitaet
- bessere Anschlussfaehigkeit an die methodischen Anforderungen der Bachelorarbeit

## Phase 5: Erweiterte Features und Forecast-Bereinigung

Im naechsten Schritt wurden die klassischen Eingabefeatures erweitert:

- Momentum
- gleitende Durchschnitte
- EMA-Gaps
- Volatilitaet
- Breakout-/Drawdown-Abstaende
- Preis-Z-Score
- RSI

Gleichzeitig wurde der rekursive Forecast technisch verbessert:

- Zukunftsfeatures werden jetzt konsistent aus der fortgeschriebenen `Close`-Historie neu aufgebaut
- fruehere vereinfachte Fortschreibungen von Features werden nicht mehr verwendet

Wichtige inhaltliche Erkenntnis:

- mehr technische Features fuehren nicht automatisch zu einer besseren Generalisierung

## Phase 6: Mehrmodell-Vergleich

Spaeter wurde der klassische Pfad zu einem echten Modellvergleich ausgebaut:

- `Persistence-Baseline`
- `Ridge Regression`
- `Decision Tree`
- `Random Forest`

Dadurch wurde sichtbar:

- unterschiedliche Aktien bevorzugen unterschiedliche Modelltypen
- `Ridge Regression` war in mehreren Faellen robuster als erwartet
- `Random Forest` war nicht durchgaengig das beste gelernte Modell

Diese Phase ist fuer die Bachelorarbeit besonders wichtig, weil sie den Schritt von einer einzelnen Modellidee zu einer systematischen Evaluation markiert.

## Phase 7: Benchmark-Koerbe und Experimentsuite

Aktuell existieren feste Ticker-Koerbe wie:

- `starter`
- `bachelor_core`
- `bachelor_diversified`

Zusaetzlich gibt es:

- wiederverwendbare Benchmark-Laeufe
- eine Experimentsuite ueber mehrere Feature-Profile
- Vergleiche ueber mehrere Lag-Werte
- aggregierte CSV-, JSON- und Markdown-Berichte

Dadurch entwickelt sich das Projekt von einem reinen Prototyp zu einer reproduzierbaren Evaluationsumgebung.

## Phase 8: Erste groessere Bachelor-Koerbe

Nach dem Starter-Korb wurden groessere Koerbe fuer belastbarere Aussagen genutzt, insbesondere `bachelor_core`.

Wichtige Beobachtung:

- im groesseren Korb blieb die naive Baseline weiter stark
- `technical_extended` war gegenueber `lag_only` im Mittel leicht besser, aber nur mit kleinem Abstand
- die besten Modelltypen wechselten weiter je nach Aktie

Das ist methodisch relevant, weil es zeigt:

- die Guete haengt nicht nur vom Modelltyp ab
- groessere Ticker-Koerbe koennen fruehere Einzelergebnisse relativieren
- ein kontrollierter Vergleich ueber Profile und Koerbe ist sinnvoller als eine einmalige Einzelbeobachtung

## Phase 9: Konsolidierte Ergebnisaufbereitung fuer die Bachelorarbeit

Nach den groesseren Vergleichslaeufen wurde zusaetzlich ein eigener Ergebnisexport eingefuehrt.

Ziel dieser Phase:

- vorhandene Experimente nicht nur auszufuehren, sondern gezielt fuer die schriftliche Arbeit aufzubereiten
- Tabellen, Grafiken und Kurzinterpretationen aus den bisherigen Laeufen automatisiert zusammenzufassen
- den jeweils aktuellen Auswertungsstand reproduzierbar als Ergebnispaket ablegen zu koennen

Wichtiger Unterschied zu frueher:

- zuvor lagen viele Erkenntnisse zwar als Einzel-CSV, JSON oder Plot vor
- jetzt gibt es zusaetzlich einen zusammenhaengenden Thesis-Export mit einer kompakten Ergebnisbasis

Methodischer Nutzen:

- staerkere Trennung zwischen Experimentdurchfuehrung und Ergebnisdarstellung
- leichtere Uebernahme von Tabellen und Grafiken in die Bachelorarbeit
- besser nachvollziehbare Verbindung zwischen Zwischenstand, Vergleichsergebnis und spaeterer Interpretation

## Phase 10: Automatisierter Profilvergleich und `bachelor_diversified`

Im naechsten Schritt wurde der Profilvergleich von einem einmaligen manuellen Zusammenfuehren auf ein eigenes Skript umgestellt.

Ziel dieser Phase:

- Benchmark-Runs ueber mehrere Teil-Laeufe sauber wieder zusammenfuehren
- denselben Vergleichsprozess fuer weitere Koerbe wiederverwenden
- groessere Koerbe wie `bachelor_diversified` ohne Ad-hoc-Auswertung auswerten

Wichtige Beobachtung:

- auch im `bachelor_diversified`-Korb blieb die Baseline bei der RMSE sehr stark
- `technical_extended` war im Mittel erneut leicht besser als `lag_only`
- dieser Vorteil war aber nicht ueber alle Einzelticker hinweg einheitlich verteilt

Diese Phase ist fuer die Bachelorarbeit wichtig, weil sie zeigt, dass die Evaluation nicht nur groesser, sondern auch methodisch sauberer und reproduzierbarer geworden ist.

## Phase 11: UI-Handover ohne direkte UI-Implementierung

Bevor die eigentliche Blazor-Oberflaeche beginnt, wurde noch eine Zwischenphase eingefuehrt:

- konsolidierte Thesis-Ergebnisse fuer mehrere Koerbe
- kompakter Dashboard-Export fuer eine spaetere Anwendung
- klares Handover-Dokument fuer die Oberflaeche

Warum dieser Schritt wichtig ist:

- die UI muss nicht mehr direkt mit vielen einzelnen ML-Artefakten umgehen
- die Datenstruktur fuer Karten, Tickeruebersicht und Korbvergleiche ist bereits festgelegt
- damit wird der naechste Entwicklungsschritt klar: jetzt kann die Oberflaeche gebaut werden, statt weiter an der Datenaufbereitung zu arbeiten

## Phase 12: Erste echte Blazor-Dashboard-UI

Im naechsten Schritt wurde der Handover nicht nur dokumentiert, sondern direkt in der App umgesetzt.

Wichtige Merkmale dieser Phase:

- Ersetzung des Blazor-Standardtemplates durch ein echtes dunkles Dashboard
- Einfuehrung eines kleinen C#-Datendienstes fuer `dashboard_payload.json`
- Startseite mit Kennzahlenkarten, Featured-Tickern und Korbvergleichen
- bewusste Trennung zwischen ML-Export und App-Darstellung

Warum diese Phase wichtig ist:

- das Projekt ist damit nicht mehr nur eine ML- und Auswertungsumgebung, sondern besitzt erstmals eine zusammenhaengende Bedienoberflaeche
- die Visualisierung basiert nicht mehr auf Notebook-Plots allein, sondern auf einer reproduzierbaren UI-Schicht
- die Bachelorarbeit kann damit nicht nur Modelle und Metriken, sondern auch die Systemintegration eines Dashboards dokumentieren

Wichtige Abgrenzung:

- die App trainiert die Modelle noch nicht selbst live
- sie zeigt den aktuellen exportierten Forschungsstand an
- damit bleibt die Architektur sauber: ML erzeugt Ergebnisse, die UI praesentiert sie

## Phase 13: Unternehmensranking aus vorhandenen Multi-Ticker-Ergebnissen

Im naechsten Schritt wurde die bestehende Mehrticker-Auswertung um ein eigenes Unternehmensranking erweitert.

Wichtige Merkmale dieser Phase:

- kein neuer Modellpfad, sondern Wiederverwendung der vorhandenen Forecast- und Walk-Forward-Artefakte
- Ranking im Dashboard-Export auf Basis von 5-Tage-Ausblick, relativer Walk-Forward-Guete, Richtungstrefferquote und Abstand zur Baseline
- zusaetzlicher UI-Baustein in der Blazor-Startseite fuer die direkte Gegenueberstellung mehrerer Aktien

Warum diese Phase wichtig ist:

- ein Mehrticker-Vergleich endet damit nicht mehr nur bei Benchmark-CSV und RMSE-Berichten
- die App kann mehrere Unternehmen gleichzeitig sichtbar machen und priorisieren
- der Schritt bleibt methodisch anschlussfaehig, weil kein gemeinsames Mehrfachmodell behauptet wird, sondern ein Ranking aus vorhandenen Einzelprognosen entsteht

## Phase 14: Gemeinsamer Multi-Asset-Klassikpfad und erste ETF-Koerbe

Im naechsten Schritt wurde zusaetzlich zum bisherigen Einzel-Ticker-Training ein gemeinsamer klassischer Mehrfachpfad eingefuehrt.

Wichtige Merkmale dieser Phase:

- ein gemeinsamer Trainingslauf ueber mehrere Aktien oder ETFs statt nur nacheinander getrennte Einzelmodelle
- tickerkodierte Identitaetsmerkmale, damit das gemeinsame Modell die einzelnen Assets unterscheiden kann
- Holdout- und Walk-Forward-Auswertung ueber gemeinsame Datumsbloecke statt ueber isolierte Einzelticker-Reihen
- erste ETF- und Mischkoerbe wie `etf_core`, `etf_sectors` und `mixed_assets`

Warum diese Phase wichtig ist:

- damit wird ein zentraler Wunsch aus dem Notebook-Stand erstmals direkt im aktiven Projekt umgesetzt
- der Mehrfachvergleich ist nicht mehr nur ein Reporting ueber viele Einzelmodelle, sondern ein echtes gemeinsames Training
- ETFs werden damit technisch in denselben klassischen Evaluationspfad eingebunden, auch wenn sie in der Dashboard-UI noch nicht gesondert dargestellt werden

## Phase 15: Multi-Asset-Experimentsuite und Dashboard-Anbindung

Im naechsten Schritt wurde der neue gemeinsame Multi-Asset-Pfad nicht nur als Einzellauf, sondern auch als kleine reproduzierbare Suite verankert.

Wichtige Merkmale dieser Phase:

- eigenes Skript fuer kompakte Vergleiche ueber `mixed_assets`, `etf_core` und weitere feste Koerbe
- Vergleich mehrerer Feature-Profile und Lag-Werte fuer das gemeinsame Modell in einem Lauf
- Aggregation der besten Multi-Asset-Konfiguration pro Korb in einer kompakten Suite-Zusammenfassung
- direkte Uebernahme dieser Bestkonfigurationen in den Dashboard-Export und in die Blazor-Startseite

Warum diese Phase wichtig ist:

- der neue Mehrfachpfad ist damit nicht mehr nur technisch vorhanden, sondern systematisch auswertbar
- Aktien- und ETF-Koerbe koennen jetzt mit demselben gepoolten Verfahren reproduzierbar gegeneinander gestellt werden
- die Dashboard-UI zeigt damit nicht mehr nur Einzel-Ticker und klassische Korbvergleiche, sondern auch den besten gemeinsamen Multi-Asset-Stand

## Phase 16: Stabilisierung fuer fehlende lokale Dashboard-Artefakte

Im naechsten Schritt wurde die bestehende Blazor-App nicht fachlich erweitert, sondern fuer frische Clones und Rechnerwechsel robuster gemacht.

Wichtige Merkmale dieser Phase:

- klarer Leerzustand, wenn `storage/dashboard/LATEST/dashboard_payload.json` lokal fehlt
- expliziter Hinweis, dass die ML-Artefakte lokal erzeugt werden muessen
- direkte Anzeige des erwarteten Dateipfads und der typischen Export-Befehle
- zusaetzlicher UI-Hinweis `Datenstatus pruefen`, damit der Nutzer den lokalen Stand erneut laden kann

Warum diese Phase wichtig ist:

- die App wirkt nach einem frischen Clone nicht mehr still leer oder kaputt
- die Trennung zwischen versioniertem Code und lokal erzeugten Laufzeitdaten wird fuer Entwickler klarer
- die technische Einstiegshuerde fuer neue Rechner oder spaetere Bewertungsumgebungen sinkt deutlich

## Phase 17: Marktzentrierte Startseite statt theoriegetriebener Einfuehrung

Im naechsten Schritt wurde die Blazor-Startseite nicht fachlich neu erfunden, sondern in ihrer Informationshierarchie neu geordnet.

Wichtige Merkmale dieser Phase:

- kompakter Hero-Bereich statt langer Erklaerung am Seitenanfang
- Watchlist-/Ticker-Kacheln und letzte Schlusskurse direkt am Einstieg
- Umschaltung zwischen `Kurse` und `Prognosen` auf derselben Uebersichtsseite
- Prognosen bleiben optisch als Forschungs-/ML-Ergebnis markiert
- laengere Einordnung wandert auf die bestehende Hinweise-Seite

Warum diese Phase wichtig ist:

- die Seite wirkt naeher an einem modernen Finanzdashboard und weniger wie ein reiner Projektbericht
- relevante Tickerinformationen stehen vor Theorie und Methodik
- gleichzeitig bleibt die wissenschaftliche Trennung gewahrt, weil Prognosen nicht als Handlungssignal praesentiert werden

## Phase 18: Asset-Suche, lokale Watchlist und robuste Detailansichten

Im naechsten Schritt wurde die bestehende Dashboard-UI nicht um neue ML-Logik erweitert, sondern um eine
nutzerfreundlichere Navigation ueber vorhandene und fehlende Assets.

Wichtige Merkmale dieser Phase:

- Asset-Suche direkt auf dem vorhandenen `dashboard_payload.json`
- lokale Watchlist im Browser mit Hinzufuegen und Entfernen ohne Serverzustand
- eigene Detailroute pro Asset statt nur einer Fokusflaeche auf der Startseite
- klare Platzhalter fuer Ticker ohne vorbereitete Prognosedaten
- deutsche UI-Texte mit regulaeren Sonderzeichen statt Umschreibungen

Warum diese Phase wichtig ist:

- die App ist damit naeher an einem echten Finanzdashboard und weniger nur eine einmalige Uebersichtsseite
- Nutzer koennen bekannte Assets schneller wiederfinden und lokal markieren
- fehlende oder noch nicht vorbereitete Ticker fuehren nicht zu Verwirrung oder einem leeren Bildschirm
- die Trennung bleibt sauber: die UI erklaert fehlende Daten, erzwingt aber kein spontanes ML-Training

## Phase 19: Prognosekontext, Aktualitaet und Modellvergleich sichtbar gemacht

Im naechsten Schritt wurde nicht die ML-Methodik selbst veraendert, sondern der vorhandene Dashboard-Handover
und die Blazor-UI so erweitert, dass Prognosen besser eingeordnet werden koennen.

Wichtige Merkmale dieser Phase:

- defensive Erweiterung des Dashboard-Payloads um `data_until`, `stale_after_days`, `selected_model`, `available_models`, `model_metrics` und `forecast_horizon_days`
- sichtbare Anzeige von Datenstand, Prognosezeitpunkt, Modell/Methode und Horizont auf Start- und Detailansicht
- Toggle nicht mehr nur fuer Kurse und Prognosen, sondern zusaetzlich fuer einen kompakten Modellvergleich
- direkte Gegenueberstellung von Persistence-Baseline, Ridge Regression, Decision Tree und Random Forest, sofern im Payload vorhanden
- Warnhinweis fuer aeltere Exporte statt einer stillschweigend veralteten Prognoseanzeige

Warum diese Phase wichtig ist:

- die UI wirkt damit weniger wie ein Trading-Signal und staerker wie eine nachvollziehbare Forschungsoberflaeche
- Nutzer erkennen schneller, ob ein Forecast aktuell ist, auf welchem Modell er basiert und wie Alternativen abgeschnitten haben
- die vorhandenen ML-Artefakte werden besser erklaert, ohne die Trainingslogik neu zu schreiben oder zu brechen

## Phase 20: Erklaersystem fuer Fachbegriffe, Kennzahlen und Dashboard-Karten

Im naechsten Schritt wurde die bestehende App nicht um neue ML-Berechnungen erweitert, sondern um eine
leichter zugängliche Erklaerschicht fuer Begriffe aus Prognose, Backtesting und Modellvergleich.

Wichtige Merkmale dieser Phase:

- zentraler Begriffskatalog in der App statt verteilter Einzeltexte
- wiederverwendbare Fragezeichen-Tooltip-Komponente fuer wichtige Kennzahlen und Modellbegriffe
- Integration dieser Erklaerungen in zentrale Start- und Detailkarten, ohne das Dashboard textlastig zu machen
- Ausbau der bestehenden Hinweise-Seite zu einer kombinierten FAQ- und Glossar-Seite in einfacher Sprache

Warum diese Phase wichtig ist:

- Nutzer werden bei Begriffen wie RMSE, Baseline, Directional Accuracy oder Feature-Profil nicht allein gelassen
- die App bleibt kompakt, weil Erklaerungen bei Bedarf an der Kennzahl geoeffnet werden koennen
- fuer die Bachelorarbeit verbessert sich die Nachvollziehbarkeit, ohne dass die ML-Logik selbst geaendert werden musste

## Phase 21: News-Bereich als reiner Kontextblock

Im naechsten Schritt wurde die Blazor-App um einen News-Bereich erweitert, ohne die bestehenden ML-Modelle oder
Prognosepfade fachlich zu veraendern.

Wichtige Merkmale dieser Phase:

- neue News-Architektur mit `NewsItem`, `INewsProvider`, `MockNewsProvider` und `NewsService`
- eigene News-Seite mit Filterung nach Kategorie und optional nach betroffenem Ticker
- kompakte News-Vorschau auf der Startseite
- klar markierte Demo-Daten aus serioesen Quellenmustern, damit die Funktion ohne API-Schluessel lauffaehig bleibt
- expliziter Hinweis in der UI, dass News aktuell nur als Kontext dienen und noch nicht im Modell verwendet werden

Warum diese Phase wichtig ist:

- das Dashboard bekommt mehr Marktumfeld, ohne daraus vorschnell ein Trading- oder Sentiment-System zu machen
- die technische Schnittstelle fuer eine spaetere echte News-API ist vorbereitet
- es werden keine Secrets oder kostenpflichtigen API-Zugaenge ins Repository gebracht

## Phase 22: Lokale Browser-Benachrichtigungen und In-App-Statusmeldungen

Im naechsten Schritt wurde die Blazor-App um optionale lokale Benachrichtigungen erweitert, ohne eine Server-Push-
Infrastruktur oder handelnde Signale aufzubauen.

Wichtige Merkmale dieser Phase:

- lokale Browser-Notification-Schicht mit Berechtigungsstatus, Aktivieren/Deaktivieren und Testbenachrichtigung
- neutrale Benachrichtigungstypen fuer neue Dashboard-Payloads, aktualisierte Prognosedaten und Watchlist-Assets mit neuem Datenstand
- Erkennung neuer lokaler Exporte ueber `generated_at` im Payload
- Fallback auf In-App-Toasts, wenn Browser-Benachrichtigungen nicht erlaubt oder nicht verfuegbar sind

Warum diese Phase wichtig ist:

- die App kann neue lokale Forschungsstaende aktiver sichtbar machen, ohne in Richtung Trading-App zu kippen
- das Feature bleibt optional, rein lokal und ohne Secrets, Push-Server oder externe Infrastruktur
- Nutzer erhalten Statusfeedback auch dann, wenn der Browser die Notification-API blockiert

## Phase 23: Lokaler FAQ-Chat mit optionaler Ollama-Anbindung

Im naechsten Schritt wurde die Blazor-App um einen lokal begrenzten FAQ- und Erklaer-Chat erweitert, ohne
die bestehende ML-Logik oder den Dashboard-Export fachlich umzubauen.

Wichtige Merkmale dieser Phase:

- klare Chat-Schnittstelle ueber `IChatAssistantService`
- lokaler `OllamaChatAssistantService` fuer die lokale Ollama-API sowie Modellpruefung ueber `api/tags`
- `MockChatAssistantService` als eingebauter FAQ-/Glossar-Fallback ohne Cloud-API
- eigene Chat-Seite unter `/chat` mit Provider-Status, Frageideen und Setup-Hinweisen
- thematische Begrenzung auf Dashboard, Kennzahlen, Modelle, Methoden und Bachelorarbeitskontext
- einfache Sicherheitsregeln gegen Kauf-, Verkaufs- oder Trading-Fragen
- Testbenachrichtigung zeigt jetzt immer zusaetzlich einen sichtbaren In-App-Hinweis, damit der manuelle Test nicht ins Leere laeuft

Warum diese Phase wichtig ist:

- die Erklaerschicht wird interaktiver, ohne von einem externen LLM-Dienst abzuhaengen
- die App bleibt auf jedem Rechner lauffaehig, auch wenn Ollama lokal fehlt oder nicht gestartet ist
- der Chat bleibt klar als Forschungs- und Erklaerfunktion eingegrenzt und greift nicht in Prognoseberechnung oder Anlageentscheidungen ein

## Phase 24: Robusterer Browser-Popup-Pfad und konzeptionelle Zukunftsintegrationen

Im naechsten Schritt wurde der lokale Benachrichtigungspfad auf Browser-Seite robuster gemacht und parallel nur
eine konzeptionelle Grundlage fuer spaetere Integrationen dokumentiert.

Wichtige Merkmale dieser Phase:

- Browser-Benachrichtigungen nutzen jetzt bevorzugt einen lokalen Service-Worker-Pfad statt nur den direkten `Notification`-Konstruktor
- Statuskarte zeigt zusaetzlich, ob der Popup-Kanal technisch vorbereitet ist oder nur der In-App-Fallback verfuegbar bleibt
- neue Doku `docs/future-integrations.md` fuer Nutzerprofile, gespeicherte Watchlists, persoenliche Dashboard-Einstellungen und moegliche Exportpfade
- sichtbarer, aber deaktivierter UI-Platzhalter fuer `Profile: geplant`, `TradingView-Export: geplant` und `Broker-Anbindung: Zukunftsthema`
- ausdrueckliche Klarstellung: keine Anlageberatung, kein automatisches Trading, keine Broker-Orders

Warum diese Phase wichtig ist:

- das Notification-Feature wird technisch nachvollziehbarer und weniger browserabhaengig
- der Ausbaupfad fuer spaetere Integrationen ist dokumentiert, ohne die Bachelorarbeit in Richtung Trading-System zu verschieben
- die App bleibt forschungsorientiert und seroes, obwohl kuenftige Optionen konzeptionell sichtbar gemacht werden

## Phase 25: Markt-Datenebene, echte Kurscharts und lokale Forecast-Jobs

Im naechsten Schritt wurde das zentrale Produktproblem der Web-App angegangen: Die App zeigt nicht mehr nur
vorbereitete Payload-Ticker, sondern trennt jetzt eine echte Markt-Datenebene von der Forecast-/Research-Ebene.

Wichtige Merkmale dieser Phase:

- neue lokale Markt-Datenlogik ueber `StockPredictor.ML/export_market_data.py` mit historischen OHLCV-Snapshots unter `storage/market_data/`
- erweiterbare Asset-Suche ueber bekannte Ticker- und Alias-Namen wie `apple`, `tesla`, `siemens` oder `siemens energy`
- Startseite mit echten Kurskarten, Zeitraumveraenderungen und Watchlist-Fokus statt reinem Payload-Dashboard
- Asset-Detailseite mit historischem Kurschart fuer `1T`, `1W`, `1M`, `6M`, `1J` und `MAX`, auch wenn noch kein Forecast existiert
- klare Trennung zwischen `Kursdaten geladen bis ...` und `Forecast basiert auf lokalem Export vom ...`
- lokale Forecast-Job-Struktur in der App fuer `Prognose fuer dieses Asset erzeugen` und `Forecast aktualisieren`
- automatische Hintergrund-Aktualisierung fuer veraltete Forecasts, ohne blockierenden Ladescreen
- robustere Fehlerpfade fuer fehlende Payloads, fehlende `.venv`, yfinance-/Netzprobleme und unbekannte Assets

Warum diese Phase wichtig ist:

- die App fuehlt sich erstmals wie ein nutzbares Finanzdashboard an und nicht nur wie ein Viewer fuer vorbereitete JSON-Ticker
- Nutzer koennen neue Assets suchen und direkt als Marktansicht verwenden, auch bevor ein lokaler Forecast erzeugt wurde
- Forecasts bleiben sichtbar als getrennte Forschungsartefakte und wirken dadurch weniger wie unveraenderliche Live-Signale

## Zwischenfazit fuer die Bachelorarbeit

Der Entwicklungsverlauf zeigt bewusst keine lineare Bewegung zu einer sofort "perfekten" Loesung. Stattdessen ist sichtbar:

- fruehe Prototypen waren explorativ und wenig strukturiert
- erste klassische Modelle waren methodisch sauberer, aber noch begrenzt
- spaetere Ausbaustufen verbesserten Reproduzierbarkeit und Vergleichbarkeit
- empirisch blieb die naive Baseline in der RMSE teilweise sehr stark
- die besten gelernten Modelle haengen vom jeweiligen Ticker und vom Feature-Setup ab

Genau dieser Verlauf ist fuer eine wissenschaftliche Arbeit plausibel und sogar wuenschenswert, weil er einen nachvollziehbaren Erkenntnisprozess dokumentiert.
