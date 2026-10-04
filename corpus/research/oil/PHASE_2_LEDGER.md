# CEREBUS OIL — PHASE 2 RESULTS
## Early-Week Anchor Search

## Question
Which simple early-week oil range best scales the final Sunday-evening→Friday weekly range **after normalizing the 2026 regime shift**?

## Frozen test design
- Provisional clock: server − 7h = ET.
- Week: Sunday 18:00 ET → Friday 17:00 ET.
- Complete weekly sample: **199 weeks**.
- Primary geometry: prior-ATR20 normalized.
- Raw dollars retained for live/operator output.
- Chronological OOS forecasting.
- Minimum history before first forecast: 52 prior weeks.
- Maximum rolling calibration memory: 104 weeks.
- No Thursday / Friday information.
- Oil RTH candidate in this phase: 09:00–14:30 ET.

## Important interpretation rule
This phase tests **seed ranges**, not the final checkpoint schedule.

A Tuesday-morning envelope is allowed to win statistical accuracy because it contains more information. It does **not** automatically become the operational baseline. Phase 4 will explicitly score **information gain versus time remaining**.

## Master ranking

| Anchor | Available after Sun18 | OOS n | MAE ATR | MAPE | Normalized Spearman | Median week/anchor | Pre→Post multiplier drift | Composite |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sun18_Tue09 | 39h | 142 | 0.741 | 29.6% | 0.551 | 1.83× | 9.2% | 3.00 |
| Sun18_Mon1430 | 20.5h | 138 | 0.811 | 33.6% | 0.429 | 2.27× | 3.3% | 3.75 |
| Mon03_Mon17 | 23h | 138 | 0.844 | 34.5% | 0.441 | 2.53× | 4.2% | 4.50 |
| Sun18_Mon17 | 23h | 138 | 0.863 | 33.8% | 0.446 | 2.25× | 5.5% | 4.50 |
| Mon09_Tue09 | 39h | 142 | 0.755 | 31.8% | 0.497 | 2.28× | 22.4% | 5.00 |
| Sun18_Mon09 | 15h | 138 | 0.852 | 35.4% | 0.371 | 3.15× | 1.7% | 5.50 |
| Mon00_Mon17 | 23h | 138 | 0.888 | 34.4% | 0.446 | 2.49× | 5.0% | 6.00 |
| Sun18_Mon08 | 14h | 138 | 0.858 | 35.9% | 0.349 | 3.40× | 8.2% | 8.75 |

# Result 1 — strongest overall candidate
## **Sun18_Tue09**
Available roughly **39 hours after Sunday 18:00 ET**, i.e. Tuesday 09:00 ET.

- OOS MAE: **0.741 ATR**
- OOS MAPE: **29.6%**
- normalized Spearman: **0.551**
- median final-week / anchor multiplier: **1.83×**
- pre→post multiplier drift: **9.2%**

### Regime stability
- **Post-shock elevated**: n=16, median 1.67×, IQR 1.40–1.92×
- **Pre-shock**: n=174, median 1.84×, IQR 1.48–2.39×
- **Shock-transition**: n=9, median 2.17×, IQR 1.11–2.60×

Interpretation: by Tuesday 09:00 ET, the Sunday-open→Tuesday-morning envelope contains the strongest overall weekly-size information in this Phase-2 candidate set. That is useful, but it is already a **checkpoint**, not a pure Monday seed.

# Result 2 — strongest Monday-only seed
## **Sun18_Mon1430**
Available around **Monday 14:30 ET**.

- OOS MAE: **0.811 ATR**
- OOS MAPE: **33.6%**
- normalized Spearman: **0.429**
- median final-week / anchor multiplier: **2.27×**
- pre→post multiplier drift: **3.3%**

### Regime stability
- **Post-shock elevated**: n=16, median 2.33×, IQR 1.89–2.70×
- **Pre-shock**: n=170, median 2.26×, IQR 1.70–2.83×
- **Shock-transition**: n=9, median 3.54×, IQR 1.56–3.65×

Interpretation: the **Sunday 18:00 → Monday 14:30 ET envelope** is the cleanest Monday-only seed in the current search. It performs better than Monday RTH by itself, Monday overnight by itself, and full Monday through 17:00 under the composite stability score.

# What the ranking says structurally

1. **Oil wants a broader early-week envelope**, not one isolated session.
2. Pure Monday RTH (`Mon09_Mon1430_RTH`) is useful but not the best anchor.
3. Adding the Sunday reopen / overnight structure materially improves the relationship.
4. Tuesday 09:00 improves the map further, but at the cost of waiting another ~18.5 hours beyond Monday RTH close.
5. Pre→post-shock multiplier drift is small for several Monday envelopes once ATR normalization is used, which supports the Phase-1 normalization decision.

# What is NOT frozen yet
- No oil tier thresholds yet.
- No final weekly Q50/Q75/Q90 factors yet.
- No claim that Tuesday 09:00 is the final operational lock.
- No claim that 09:00–14:30 is the final optimal RTH definition.
- No EIA / OPEC / weekend-gap features yet.
- No raw-dollar stationary tier system.

# Phase-2 handoff to Phase 3
Tier discovery should be run first on **`Sun18_Mon1430`** because it is the strongest Monday-only structural seed and gives enough week remaining to be operational.

`Sun18_Tue09` is retained as the first major checkpoint challenger for Phase 4.

## Phase 3
Run oil-native tier discovery on `Sun18_Mon1430`:
- k=3 baseline
- k=4 sensitivity
- quantile partition
- bootstrap centroids
- rolling annual centroids
- pre/shock/post stability
- ATR-normalized tier geometry
- raw-dollar translation by regime
- explicit T4 / shock / no-go class