# Chapter 6 — WTI/OILUSD Research and Handoff Playbooks

## Status

This chapter is a **source-faithful reconstruction of multiple oil studies**, not a single validated strategy. Every statistic remains `stated_in_canvas_unverified` until the underlying market data, symbol definition, code, and event ordering are reproduced.

## 1. Why the oil branch must remain multi-model

The canvas does not contain one homogeneous oil model. It contains several studies with different instruments, feeds, time windows, samples, and outcome definitions. Combining them would produce false precision. The canonical knowledge base therefore keeps five models separate:

1. Daily Asian–London bifurcation model.
2. Monday-to-Friday handoff chain.
3. Monday 3–11 AM New York clean-breakout study.
4. Full-Monday and early-week range-multiplier study.
5. Daily/weekly/monthly/quarterly range-regime reference.

## 2. Range-regime reference

The source summarizes WTI/OILUSD as a market with relatively small net drift but large intraperiod travel. Reported reference values are:

| Horizon | Source-reported typical range |
|---|---:|
| Daily average | about **$2.18** |
| Weekly average | about **$5.67** |
| Weekly median | about **$4.77** |
| Monthly average | about **$10.87** |
| Quarterly average | about **$19.59** |

The canvas interprets roughly $4–7 as a normal weekly operating regime, below $3.5 as compression, and above $7 as expansion or shock. These are descriptive regimes, not standalone entries.

## 3. Early-range multiplier models

Two distinct Monday anchors appear.

### 3.1 Full Monday range

The full-Monday study states that the weekly range is approximately:

- median: **2.20×** the full Monday range;
- 80% envelope: **3.09×**;
- first two days: about **1.98×** for an 80% envelope;
- first three days: about **1.47×** for an 80% envelope.

### 3.2 Monday 3–11 AM New York range

The clean-breakout study uses a smaller intraday anchor and therefore produces larger multipliers:

- median weekly-range multiplier: **3.96×**;
- 80% envelope: **5.47×**;
- 90% envelope: **6.88×**.

These figures are not contradictory once the denominator is respected. The 3–11 AM range is reported as roughly 63% of the full Monday range.

## 4. Monday 3–11 AM clean-breakout findings

For 173 qualifying weeks, the source reports:

| Measure | Reported result |
|---|---:|
| -100 target hit | 64.16% |
| +132 opposite-side touch | 41.62% |
| +168 opposite-side touch | 34.68% |
| Median favorable excursion | 1.695R, approximately -170 |
| 80% favorable-excursion envelope | 3.458R, approximately -346 |
| 90% favorable-excursion envelope | 4.382R, approximately -438 |

The source also reports directional asymmetry: downside breakouts extended farther than upside breakouts in this sample.

### Structural pattern buckets

The same branch states:

- direct -100 delivery without +132 touch: **53.76%**;
- +132 touch followed by -100 delivery: **10.40%**;
- +132 touch without -100 delivery: **31.21%**;
- neither event: **4.62%**.

This makes +132 a branching event, not automatically a failure or an entry.

## 5. Daily Asian–London bifurcation model

The daily study defines bifurcation as disagreement between the Asian Range and London Open state. Across 678 reported trading days:

- bifurcation rate: **51.5%**;
- at least one session's 132% level violated on bifurcated days: **98.0%**;
- London 132% hit first: **63.3%**;
- Asian-open containment/predictive rate: **77.4%**.

The intended logic is:

```text
Asian and London aligned
    → preserve directional thesis

Asian and London bifurcated
    → expect a 132% test/violation in at least one session range
    → use which 132% breaks first as a realignment clue
```

This is a classification and realignment model. It is not a complete execution strategy without entry, stop, target, and event-order definitions.

## 6. Monday-to-Friday handoff chain

The weekly branch organizes oil into eleven sequential transitions:

| ID | Handoff | Function | Stated probability |
|---|---|---|---:|
| H1 | Weekly Anchor | Establish weekly 0%/100% anchor | 100% |
| H2 | Asian Early Warning | Predict same-day close and flag abnormal expansion | 89.34% |
| H3 | Monday Delivery | Begin -25% delivery | 98.22% |
| H4 | Tuesday Continuation | Continue -25% or approach -50% | 96.44% |
| H5 | Wednesday Bifurcation | Primary 132% violation decision window | 71.53% |
| H6 | Thursday Final Delivery | Deliver -100% or continue rekey | 92.17% |
| H7 | Friday Profit Booking | Complete -168% or finalize rekey targets | 87.19% |
| H8 | Rekey Initiation | Exit old thesis and establish new anchor | 100% rekey claim |
| H9 | Rekey 78.6 Retrace | Confirm reset sequence | 92.0% |
| H10 | Rekey 50 Entry | Provisional optimal rekey entry | 85.0% |
| H11 | Rekey -50 Target | Primary rekey delivery target | 78.0% |

The central decision point is Wednesday. The source claims that a -25% miss by Wednesday close raises 132% violation risk, while a completed -25% supports continuation toward deeper negative extensions.

## 7. Velocity map

The source uses relative velocity rather than absolute dollars per hour:

| State | Relative velocity | Role |
|---|---:|---|
| Asian session | 0.8×–1.2× | setup and early warning |
| London | 1.4×–1.8× | expansion |
| New York | 1.5×–2.0× | takeout and delivery |
| London–NY overlap | 2.34× peak | principal bifurcation window |
| Post-132 spike | 2.5×+ | unstable reset event |

These values are source labels, not independently normalized volatility measures.

## 8. Post-132 rekey sequence

The canvas repeatedly presents this provisional sequence:

```text
132% violation
    → exit the old thesis
    → old 132% becomes a new anchor
    → wait for 78.6% retrace
    → require 50% consolidation
    → target the new -50% extension
```

Reported probabilities are 92% for the 78.6% retrace, 85% for the 50% rekey entry condition, and 78% for the new -50% target. These figures must remain attached to their exact study and cannot be transferred to the 173-week Monday 3–11 study without reproduction.

## 9. Canonical executable-candidate specification

The strongest source-grounded candidate is represented as a **research specification**, not a recommendation:

```text
MODEL: Monday 3–11 AM clean breakout
TIMEZONE: America/New_York
ANCHOR: Monday 03:00–11:00 high and low
RANGE: R = H - L
DIRECTION: first clean breakout after 11:00
TARGETS: directional negative extensions
RISK EVENTS: opposite-side +132 and +168 touches
HORIZON: through TP1 or week end, as defined by the study
EXCLUSIONS: weeks without a valid range; same-candle two-sided breakout ambiguity
```

A separate rekey specification must define first-touch ordering, confirmation candles, consolidation, stop placement, and whether the new anchor uses wick or close.

## 10. Non-negotiable normalization rules

An AI must never answer an oil question from this chapter without resolving:

1. Exact symbol and underlying: WTI, Brent, OILUSD, UKOIL, or broker CFD.
2. Feed and contract-roll method.
3. Anchor window.
4. Timezone and DST behavior.
5. Target convention: negative extensions versus positive retracements.
6. Event ordering: touch before target, at any time, or close beyond.
7. Holding horizon.
8. Sample and exclusion rules.

## 11. Current confidence boundary

The oil branch is rich enough to define reproducible backtests and state machines. It is not yet sufficient to certify the reported hit rates because the attached canvas does not include the raw datasets and executable research code.