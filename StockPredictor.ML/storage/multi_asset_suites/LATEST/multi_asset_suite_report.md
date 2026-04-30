# Multi-Asset Experiment Suite: latest

Diese Suite vergleicht gemeinsame Multi-Asset-Trainingslaeufe ueber mehrere Koerbe.

## Beste Konfiguration pro Korb

- mixed_assets: `mixed_assets__technical_basic__lag5` mit Random Forest, shared RMSE 3.3656, Baseline 3.3774, mittlere 5-Tage-Aenderung +0.30%
- etf_core: `etf_core__technical_extended__lag5` mit Ridge Regression, shared RMSE 3.5019, Baseline 3.5095, mittlere 5-Tage-Aenderung -0.11%

## Gesamtranking

1. `mixed_assets__technical_basic__lag5`: shared RMSE 3.3656, Baseline 3.3774, Modell Random Forest
2. `mixed_assets__technical_extended__lag5`: shared RMSE 3.3664, Baseline 3.3774, Modell Random Forest
3. `mixed_assets__technical_basic__lag10`: shared RMSE 3.3674, Baseline 3.3774, Modell Random Forest
4. `mixed_assets__technical_extended__lag10`: shared RMSE 3.3677, Baseline 3.3774, Modell Random Forest
5. `etf_core__technical_extended__lag5`: shared RMSE 3.5019, Baseline 3.5095, Modell Ridge Regression
6. `etf_core__technical_basic__lag5`: shared RMSE 3.5026, Baseline 3.5095, Modell Ridge Regression
7. `etf_core__technical_extended__lag10`: shared RMSE 3.5070, Baseline 3.5095, Modell Ridge Regression
8. `etf_core__technical_basic__lag10`: shared RMSE 3.5093, Baseline 3.5095, Modell Ridge Regression
