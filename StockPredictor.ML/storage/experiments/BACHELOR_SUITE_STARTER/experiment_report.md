# Experiment Report: BACHELOR_SUITE_STARTER

Ticker basket: `starter`

Tickers: AAPL, TSLA, DOU.DE

## Kurzinterpretation

Die aktuell beste Konfiguration in dieser Suite ist `lag_only_lag5` mit einem mittleren besten gelernten Walk-Forward-RMSE von 4.3753.
Die zugehoerige mittlere Baseline-RMSE liegt bei 4.3703.
Damit bleibt die naive Persistence-Baseline im Mittel weiterhin leicht staerker, waehrend die gelernten Modelle vor allem ueber die Richtungsprognose und tickerabhaengige Staerken relevant werden.

## Ranking der Experiment-Konfigurationen

1. `lag_only_lag5`: bestes gelerntes Mittel-RMSE 4.3753, Baseline-Mittel-RMSE 4.3703, bester Modelltyp im Mittel `ridge_regression`
2. `technical_extended_lag5`: bestes gelerntes Mittel-RMSE 4.3830, Baseline-Mittel-RMSE 4.3759, bester Modelltyp im Mittel `ridge_regression`
3. `technical_basic_lag5`: bestes gelerntes Mittel-RMSE 4.3842, Baseline-Mittel-RMSE 4.3759, bester Modelltyp im Mittel `ridge_regression`
4. `lag_only_lag10`: bestes gelerntes Mittel-RMSE 4.3857, Baseline-Mittel-RMSE 4.3719, bester Modelltyp im Mittel `ridge_regression`
5. `technical_extended_lag10`: bestes gelerntes Mittel-RMSE 4.3907, Baseline-Mittel-RMSE 4.3759, bester Modelltyp im Mittel `ridge_regression`
6. `technical_basic_lag10`: bestes gelerntes Mittel-RMSE 4.3918, Baseline-Mittel-RMSE 4.3759, bester Modelltyp im Mittel `ridge_regression`

## Beste Konfiguration pro Ticker

- DOU.DE: `technical_basic_lag5` mit Ridge Regression (RMSE 0.2692, Richtung 45.75%)
- AAPL: `lag_only_lag5` mit Random Forest (RMSE 2.3866, Richtung 52.99%)
- TSLA: `lag_only_lag5` mit Ridge Regression (RMSE 10.4685, Richtung 51.72%)
