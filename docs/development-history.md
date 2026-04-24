# Development History

Stand: 2026-04-22

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

## Zwischenfazit fuer die Bachelorarbeit

Der Entwicklungsverlauf zeigt bewusst keine lineare Bewegung zu einer sofort "perfekten" Loesung. Stattdessen ist sichtbar:

- fruehe Prototypen waren explorativ und wenig strukturiert
- erste klassische Modelle waren methodisch sauberer, aber noch begrenzt
- spaetere Ausbaustufen verbesserten Reproduzierbarkeit und Vergleichbarkeit
- empirisch blieb die naive Baseline in der RMSE teilweise sehr stark
- die besten gelernten Modelle haengen vom jeweiligen Ticker und vom Feature-Setup ab

Genau dieser Verlauf ist fuer eine wissenschaftliche Arbeit plausibel und sogar wuenschenswert, weil er einen nachvollziehbaren Erkenntnisprozess dokumentiert.
