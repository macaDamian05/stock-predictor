# Development History

Stand: 2026-04-17

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

## Zwischenfazit fuer die Bachelorarbeit

Der Entwicklungsverlauf zeigt bewusst keine lineare Bewegung zu einer sofort "perfekten" Loesung. Stattdessen ist sichtbar:

- fruehe Prototypen waren explorativ und wenig strukturiert
- erste klassische Modelle waren methodisch sauberer, aber noch begrenzt
- spaetere Ausbaustufen verbesserten Reproduzierbarkeit und Vergleichbarkeit
- empirisch blieb die naive Baseline in der RMSE teilweise sehr stark
- die besten gelernten Modelle haengen vom jeweiligen Ticker und vom Feature-Setup ab

Genau dieser Verlauf ist fuer eine wissenschaftliche Arbeit plausibel und sogar wuenschenswert, weil er einen nachvollziehbaren Erkenntnisprozess dokumentiert.
