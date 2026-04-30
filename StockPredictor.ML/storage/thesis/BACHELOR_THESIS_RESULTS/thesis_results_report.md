# Thesis Results Pack: BACHELOR_THESIS_RESULTS

Generiert am: 2026-04-30 22:23:59

## Quellen

- Starter-Suite: `storage/experiments/BACHELOR_SUITE_STARTER/experiment_summary.json`
- Bachelor-Core-Profilvergleich: `storage/experiments/BACHELOR_CORE_PROFILE_COMPARISON/profile_comparison_summary.json`
- Bachelor-Diversified-Profilvergleich: `storage/experiments/BACHELOR_DIVERSIFIED_PROFILE_COMPARISON/profile_comparison_summary.json`

## Kurzfazit

- Beste Starter-Konfiguration: `lag_only_lag5` mit mittlerem bestem gelernten Walk-Forward-RMSE von 4.3753.
- Im `bachelor_core`-Vergleich ist `technical_extended` bei den besten gelernten Modellen im Mittel vorne (4.8236 RMSE).
- Im `bachelor_diversified`-Vergleich ist `technical_extended` bei den besten gelernten Modellen im Mittel vorne (4.8236 RMSE).
- Im Starter-Korb schlagen die besten gelernten Modelle die Baseline aktuell bei 1 von 3 Tickern.

## Starter-Korb: beste Konfigurationen pro Ticker

| Ticker | Beste Konfiguration | Bestes Modell | Bestes RMSE | Baseline RMSE | Gap |
| --- | --- | --- | --- | --- | --- |
| DOU.DE | technical_basic_lag5 | Ridge Regression | 0.2692 | 0.2678 | +0.0014 |
| AAPL | lag_only_lag5 | Random Forest | 2.3866 | 2.3898 | -0.0031 |
| TSLA | lag_only_lag5 | Ridge Regression | 10.4685 | 10.4531 | +0.0153 |

## Starter-Suite: Profilranking

| Konfiguration | Profil | Bestes RMSE | Baseline RMSE | Gap | Dominantes Modell |
| --- | --- | --- | --- | --- | --- |
| lag_only_lag5 | lag_only | 4.3753 | 4.3703 | +0.0051 | Ridge Regression |
| technical_extended_lag5 | technical_extended | 4.3830 | 4.3759 | +0.0072 | Ridge Regression |
| technical_basic_lag5 | technical_basic | 4.3842 | 4.3759 | +0.0084 | Ridge Regression |
| lag_only_lag10 | lag_only | 4.3857 | 4.3719 | +0.0138 | Ridge Regression |
| technical_extended_lag10 | technical_extended | 4.3907 | 4.3759 | +0.0149 | Ridge Regression |
| technical_basic_lag10 | technical_basic | 4.3918 | 4.3759 | +0.0160 | Ridge Regression |

## Bachelor Core: Profilvergleich

| Profil | Bestes RMSE | Baseline RMSE | Gap | Richtung | Dominantes Modell |
| --- | --- | --- | --- | --- | --- |
| technical_extended | 4.8236 | 4.8218 | +0.0018 | 52.89% | Random Forest |
| lag_only | 4.8290 | 4.8178 | +0.0112 | 52.06% | Random Forest |

## Bachelor Core: Tickerweise Differenzen

| Ticker | Lag Only Modell | Lag Only RMSE | Technical Extended Modell | Technical Extended RMSE | Technical Extended minus Lag Only |
| --- | --- | --- | --- | --- | --- |
| MSFT | Random Forest | 4.2644 | Random Forest | 4.2387 | -0.0258 |
| NVDA | Random Forest | 2.1658 | Random Forest | 2.1555 | -0.0103 |
| AAPL | Random Forest | 2.3867 | Random Forest | 2.3934 | +0.0066 |
| TSLA | Ridge Regression | 10.4989 | Ridge Regression | 10.5070 | +0.0081 |

## Bachelor Core: Modellgewinne

| Profil | Ridge | Decision Tree | Random Forest |
| --- | --- | --- | --- |
| Lag Only | 1 | 0 | 3 |
| Technical Extended | 1 | 0 | 3 |

## Bachelor Diversified: Profilvergleich

| Profil | Bestes RMSE | Baseline RMSE | Gap | Richtung | Dominantes Modell |
| --- | --- | --- | --- | --- | --- |
| technical_extended | 4.8236 | 4.8218 | +0.0018 | 52.89% | Random Forest |
| lag_only | 4.8290 | 4.8178 | +0.0112 | 52.06% | Random Forest |

## Bachelor Diversified: Tickerweise Differenzen

| Ticker | Lag Only Modell | Lag Only RMSE | Technical Extended Modell | Technical Extended RMSE | Technical Extended minus Lag Only |
| --- | --- | --- | --- | --- | --- |
| MSFT | Random Forest | 4.2644 | Random Forest | 4.2387 | -0.0258 |
| NVDA | Random Forest | 2.1658 | Random Forest | 2.1555 | -0.0103 |
| AAPL | Random Forest | 2.3867 | Random Forest | 2.3934 | +0.0066 |
| TSLA | Ridge Regression | 10.4989 | Ridge Regression | 10.5070 | +0.0081 |

## Bachelor Diversified: Modellgewinne

| Profil | Ridge | Decision Tree | Random Forest |
| --- | --- | --- | --- |
| Lag Only | 1 | 0 | 3 |
| Technical Extended | 1 | 0 | 3 |

## Interpretation

- Die naive Persistence-Baseline bleibt ueber alle betrachteten Koerbe ein harter Referenzwert. Das ist methodisch wichtig, weil dadurch sichtbar bleibt, dass komplexere Modelle nicht automatisch bessere Punktprognosen liefern.
- `technical_extended` liegt im Mittel sowohl im `bachelor_core`- als auch im `bachelor_diversified`-Korb leicht vor `lag_only`, aber der Abstand ist jeweils klein.
- Die tickerweise Betrachtung zeigt gleichzeitig, dass dieser Mittelwertvorteil nicht gleichmaessig verteilt ist. Ein Teil der Werte profitiert, ein anderer Teil nicht.
- `bachelor_core`: Vorteil fuer `technical_extended` bei 2 Tickern (MSFT, NVDA), Vorteil fuer `lag_only` bei 2 Tickern (AAPL, TSLA).
- `bachelor_diversified`: Vorteil fuer `technical_extended` bei 2 Tickern (MSFT, NVDA), Vorteil fuer `lag_only` bei 2 Tickern (AAPL, TSLA).

