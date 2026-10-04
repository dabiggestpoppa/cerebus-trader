# CEREBUS Daily Range Tracker — Phase 1 Base Model Validation

## Frozen specification tested
- Data: EURUSD M5, 2022-11-01 through 2026-09-04.
- Working clock reconstruction: OX server time minus 7 hours = New York research clock.
- Asian constraint: 19:00–03:00 ET.
- Realized daily target: total high-low from 19:00 ET through the hard 12:00 ET cutoff.
- T1: Asian Range <20p, prediction = AR × 3.12.
- T2: 20–30p, prediction = AR × 2.68.
- T3: 30–45p, prediction = AR × 2.18.
- >45p: NO-GO, excluded from the normal model.
- Primary objective: realized range within ±5p of frozen prediction.

## Sample
- Complete research days: 995
- Normal T1–T3 days: 891
- NO-GO days: 104 (~10.5%)

## Overall result
- Mean realized range: 62.32p
- Median realized range: 56.90p
- Mean frozen prediction: 64.15p
- Median frozen prediction: 64.59p
- MAE: 19.69p
- Median absolute error: 16.14p
- Mean bias (realized - predicted): -1.83p

Tolerance accuracy:
- ±2.5p: 8.53%
- ±5p: 16.16%
- ±7.5p: 24.02%
- ±10p: 32.44%

## By tier
| Tier | n | Frozen factor | Median realized multiple | MAE | ±5p hit |
|---|---:|---:|---:|---:|---:|
| T1 | 278 | 3.12 | 2.992 | 16.95p | 18.71% |
| T2 | 362 | 2.68 | 2.304 | 19.57p | 13.81% |
| T3 | 251 | 2.18 | 1.939 | 22.88p | 16.73% |

## Stability notes
Frozen factors are directionally ordered correctly (T1 > T2 > T3), but the exact coordinates are not sufficiently accurate for a ±5p hard forecast.
- T1 median multiplier is close to frozen: 2.992 vs 3.12.
- T2 median is materially lower: 2.304 vs 2.68.
- T3 median is lower: 1.939 vs 2.18.
- 2026 shows material overprediction: mean bias about -10.22p.

## Decision
The old tier × multiplier model survives as a **structural prior**, not as the final precision forecast.
It is far too coarse to meet the requested ±5p target by itself.

Phase 2 should therefore preserve the tier ordering but replace the single static target with a 5-minute conditional distribution surface:
- slot × tier median completion,
- slot × tier MAD / robust sigma,
- range-left Q50/Q75/Q90,
- 06:00 and 09:00 heat-check relationships,
- London 03:00–09:00 vs NY-overlap 09:00–12:00 contribution ratios.

The key Phase 2 question is whether the error collapses materially once time/pace information is added.