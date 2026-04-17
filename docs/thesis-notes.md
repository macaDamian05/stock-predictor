# Thesis Notes

Stand: 2026-04-17

## Arbeitstitel

Arbeitstitel fuer die Bachelorarbeit:

"Konzeption und prototypische Implementierung eines Systems zur Vorhersage von Aktienkursen auf Basis historischer Marktdaten"

## Zielsetzung

Das Projekt soll untersuchen, inwieweit sich historische Boersendaten fuer die kurzfristige Prognose von Aktienkursen nutzen lassen. Der Fokus liegt auf einem prototypischen System, das Daten automatisiert bezieht, Modelle trainiert, Prognosen erzeugt und Ergebnisse nachvollziehbar speichert.

## Aktueller Prototyp

Der aktuelle technische Stand umfasst:

- eine erste klassische ML-Pipeline fuer den wissenschaftlich nachvollziehbaren Modellvergleich
- Persistence-Baseline als einfacher Referenzwert
- `Ridge Regression` als lineares Vergleichsmodell
- `DecisionTreeRegressor` als einfacher nichtlinearer Baumansatz
- `RandomForestRegressor` auf Lag-Features historischer Tagesrenditen
- mehrere Feature-Profile fuer systematische Vergleiche
- fuer den klassischen Baumansatz wird die naechste Tagesrendite modelliert und anschliessend in einen naechsten Schlusskurs zurueckgerechnet
- der klassische Feature-Satz umfasst inzwischen auch Momentum, gleitende Durchschnitte, EMA-Gaps, Volatilitaet, Breakout-/Drawdown-Abstaende, Preis-Z-Score und RSI
- CSV- oder `yfinance`-basierte Dateneingabe
- chronologischen Train/Test-Split ohne Shuffling
- Walk-Forward-Backtesting mit expandierendem Trainingsfenster
- grafische Ausgaben fuer Historie, Testperiode und mehrtaegigen Forecast
- zusaetzliche Artefakte fuer Walk-Forward-Vorhersagen und Fold-Metriken
- tickeruebergreifender Benchmark-Lauf mit gemeinsamer Vergleichstabelle
- Thesis-Export fuer konsolidierte Tabellen, Grafiken und Kurzberichte aus den bisherigen Experimenten
- konsistente rekursive Forecast-Berechnung auf Basis fortgeschriebener Close-Historie
- Experiment-Suite ueber mehrere Feature-Profile, Lag-Werte und feste Ticker-Koerbe
- Download historischer Kursdaten ueber `yfinance`
- Training eines LSTM-Modells pro Ticker
- persistente Speicherung von Modell, Scaler, Metadaten und Trainingslog
- inkrementelles Weitertraining bei neueren Kursdaten
- Visualisierung historischer Anpassung und kurzfristiger Prognosen
- Zusatzwerte wie RSI, durchschnittliche Prognose-Steigung, MAE, RMSE und Directional Accuracy

## Datengrundlage und Features

Aktuell verwendet das Modell nur den Schlusskurs (`Close`) als Eingangsfeature fuer das neuronale Netz. Weitere Groessen wie RSI werden derzeit nur zur Interpretation der Prognose genutzt.

Kurzfristig sinnvolle Erweiterungen:

- gleitende Durchschnitte
- Renditen und logarithmische Renditen
- Volatilitaet
- Momentum-Indikatoren
- Volumenbezogene Merkmale

## Methodische Hinweise fuer die Arbeit

Damit die Arbeit wissenschaftlich belastbar ist, sollte die Bewertung nicht nur auf Visualisierungen beruhen. Empfehlenswert sind mindestens:

- MSE
- MAE
- RMSE
- Directional Accuracy
- ein Vergleich gegen einfache Baselines wie "naechster Wert = letzter Wert"

Wichtig ist ausserdem eine zeitlich saubere Datenaufteilung, zum Beispiel:

- Trainingszeitraum
- Validierungszeitraum
- Testzeitraum

Ein Walk-Forward-Backtesting ist bereits fuer den klassischen Modellpfad umgesetzt und sollte in spaeteren Iterationen systematisch ueber mehrere Aktien hinweg ausgewertet werden.
Ein erster Mehrfachvergleich ueber mehrere Ticker ist jetzt ebenfalls vorgesehen, damit Metriken nicht nur fuer Einzelbeispiele, sondern auch tickeruebergreifend betrachtet werden koennen.

Erste Ergebnisbeobachtung:

- Im bisherigen Benchmark-Korb bleibt die naive Persistence-Baseline bei der RMSE sehr stark.
- Unter den gelernten Modellen ist `Ridge Regression` aktuell fuer `DOU.DE` und `TSLA` am besten, waehrend bei `AAPL` der `Random Forest` fuehrt.
- Diese Konstellation ist wissenschaftlich interessant, weil sie zeigt, dass Richtungsvorhersage, Punktprognose und Modellrang je nach Aktie unterschiedlich ausfallen koennen.
- In der ersten Starter-Suite war `lag_only` mit `10` Lags im Mittel besser als die technisch erweiterten Profile. Das spricht dafuer, dass mehr Features nicht automatisch zu besserer Generalisierung fuehren.
- Im groesseren `bachelor_core`-Vergleich zeigte `technical_extended` gegenueber `lag_only` zwar einen kleinen Vorteil bei den besten gelernten Modellen, dieser Vorteil blieb aber gering. Auch das spricht dafuer, dass Feature-Erweiterung nur kontrolliert und empirisch bewertet werden sollte.
- Die Ergebnisse koennen jetzt als konsolidiertes BA-Ergebnispaket exportiert werden. Dadurch lassen sich Tabellen und Grafiken spaeter leichter in die schriftliche Auswertung uebernehmen.

## Forschungsfragen

Moegliche Leitfragen:

1. Wie gut kann ein LSTM-Modell kurzfristige Kursbewegungen auf Basis historischer Schlusskurse vorhersagen?
2. Welche Auswirkungen haben technische Zusatzmerkmale auf die Prognoseguete?
3. Wie robust sind die Vorhersagen ueber verschiedene Aktien und Marktphasen hinweg?

## Bekannte Grenzen

- Einzelmodell pro Ticker statt gemeinsames Mehrfachmodell
- noch keine Nachrichten-, Sentiment- oder Fundamentaldaten
- noch keine unternehmensuebergreifende Ranking-Logik
- derzeit nur Tagesdaten, keine Intraday-Daten
- Abhaengigkeit von Datenqualitaet und Verfuegbarkeit in `yfinance`

## Moegliche Ausbaupfade

- Walk-Forward-Backtesting ueber mehrere Ticker und Marktphasen vergleichen
- Vergleich mehrerer Modelltypen, z. B. LSTM vs. GRU vs. klassische Baselines
- Erweiterung von Aktien auf ETFs
- Ranking mehrerer Werte anhand kombinierter Kennzahlen
- Einbindung in eine Weboberflaeche fuer Bedienung und Ergebnisdarstellung

## Offene Arbeitsauftraege

- Evaluationsdesign festziehen
- Feature Engineering sauber dokumentieren
- Anforderungen fuer Ranking und Mehrfachvergleich definieren
- groesseren Bachelor-Korb `bachelor_diversified` vollstaendig durchrechnen
- Uebergabestrategie zwischen Python-ML und Blazor-App festlegen
