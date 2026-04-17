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
- `RandomForestRegressor` auf Lag-Features historischer Tagesrenditen
- fuer den klassischen Baumansatz wird die naechste Tagesrendite modelliert und anschliessend in einen naechsten Schlusskurs zurueckgerechnet
- CSV- oder `yfinance`-basierte Dateneingabe
- chronologischen Train/Test-Split ohne Shuffling
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

Fuer spaetere Iterationen ist ein Walk-Forward-Backtesting sinnvoll, damit das System unter realistischeren Bedingungen bewertet werden kann.

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

- Walk-Forward-Backtesting fuer den klassischen Modellpfad
- Vergleich mehrerer Modelltypen, z. B. LSTM vs. GRU vs. klassische Baselines
- Erweiterung von Aktien auf ETFs
- Ranking mehrerer Werte anhand kombinierter Kennzahlen
- Einbindung in eine Weboberflaeche fuer Bedienung und Ergebnisdarstellung

## Offene Arbeitsauftraege

- Evaluationsdesign festziehen
- Feature Engineering sauber dokumentieren
- Anforderungen fuer Ranking und Mehrfachvergleich definieren
- Uebergabestrategie zwischen Python-ML und Blazor-App festlegen
