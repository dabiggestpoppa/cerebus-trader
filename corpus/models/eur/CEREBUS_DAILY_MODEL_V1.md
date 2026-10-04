# CEREBUS DAILY MODEL V1

## Purpose
Predict the **feasible daily distribution**, not an exact candle path.

The engine answers five questions:

1. How much range is left today?
2. Which unresolved side is cheaper / more likely to resolve first?
3. Which structural state is active: 100 / 125 / 132 / 168 / 185?
4. Does scheduled news expand or compress the feasibility of the next state?
5. Is the event field still active, decaying, or exhausted?

---

## 1. Daily Range Layer
Use the existing live **Slot × Tier range-left quantiles** as the daily range backbone.

- Asian tier sets the structural regime.
- Current printed range is the primary live state.
- Use Q50 / Q75 / Q90 **range-left bands**, not a single exact daily target.
- Do not promote pace, regime labels, or ML residuals unless they beat the live range-left baseline.

**Output:** remaining-range band and daily completion confidence.

---

## 2. Direction Layer

Define:

`A = min(distance_up, distance_down) / max(distance_up, distance_down)`

Directional confidence:

- A < 0.25 → **VERY HIGH** nearest-side preference (~92.8%)
- 0.25–0.50 → **HIGH** (~82.3%)
- 0.50–0.75 → **MODERATE** (~63.4%)
- >= 0.75 → **SYMMETRIC / NO EDGE**

Asian bias is a secondary confirmation only.

- nearest side + Asian bias agree → promote confidence
- conflict → still prefer nearest side, but downgrade confidence

**Doctrine:** geometry supplies direction; news supplies kinetic energy.

---

## 3. Structural State Ladder

`100 -> 125 -> 132 -> 168 -> 185`

- 100 = Asian boundary interaction
- 125 = activation / pre-commitment
- 132 = first confirmed extension
- 168 = expansion
- 185 = deep continuation / acceptance

Daily any-side reach rates:
- 100: ~99.3%
- 125: ~92.0%
- 132: ~89.1%
- 168: ~70.9%
- 185: ~62.0%

### 125 activation rule
Once 125 is touched:
- ~49.8% traverse 132 on the same M5 bar
- ~45.1% reach 132 on a later bar
- ~5.0% fail to reach 132 by noon
- conditional on NOT same-bar, later 132 continuation ~90%
- median later 125→132 lag ~10 min

125 is therefore a **pre-commitment state**, not merely noise.

---

## 4. News Kinetic Layer

Each event uses a tolerance band:

`core band = Q25-Q75`
`center = Q50`
`outer tolerance = Q90`

Do **not** predict exact pips.

For unresolved state distance D:

- D <= remaining Q50 → high/normal feasibility
- Q50 < D <= Q75 → moderate feasibility
- Q75 < D <= Q90 → tail feasibility
- D > Q90 → structurally expensive / usually no-go

Matched news vs non-news:
- news 60m reach ~10.95%
- matched non-news ~4.84%
- incremental news effect ~+6.1pp overall

News is a **probability reweighting layer**, not a replacement for geometry.

---

## 5. Event Decay Layer

Use two clocks:

### Volatility Normalization Clock
When M5 bar size returns toward pre-event baseline.

### Structural Residue Clock
When the event stops printing new structural extremes.

These are not the same.

Operationally:
1. Freeze event band at release.
2. Measure realized event envelope.
3. Recalculate remaining Q50/Q75/Q90 budget.
4. Reclassify unresolved states at +15/+30/+60/+90/+120m.
5. If state moves beyond remaining Q90, sharply downgrade reach probability.

OOS validation:
- structural snapshot AUC ~0.824
- residual news field AUC ~0.840
- residual field improved ranking at every tested age checkpoint.

---

## 6. State Transition Logic

### 125 -> 132
Activation transition.

Promote when:
- 132 remains inside residual Q50/Q75
- early clock
- T1/T2
- nearest-side asymmetry is strong

Degrade when:
- late clock
- T3 / NO_GO
- 132 beyond remaining Q90

### 132 -> 168
Expansion transition.

Baseline event-snapshot continuation ~45%.
Inside remaining Q50: ~65%.

### 168 -> 185
Deep continuation / acceptance.

Baseline event-snapshot continuation ~51%.
Inside remaining Q50: ~76%.

---

## 7. Daily Decision Stack

At every live update:

1. **Classify Asian tier**
2. **Read current daily printed range**
3. **Read Slot×Tier range-left Q50/Q75/Q90**
4. **Calculate UP/DOWN state distances**
5. **Compute distance asymmetry A**
6. **Select directional confidence**
7. **Identify current structural state**
8. **If scheduled news is active:**
   - load family tolerance band
   - compute remaining kinetic budget
   - promote/downgrade next structural states
9. **Apply clock decay**
10. **Output branch probabilities / zones**

---

## 8. Core Live Output

A practical dashboard should surface:

- Tier
- Current printed daily range
- Remaining range Q50 / Q75 / Q90
- Direction confidence: VERY HIGH / HIGH / MODERATE / NONE
- Preferred branch: UP / DOWN / SYMMETRIC
- Current state: 100 / 125 / 132 / 168 / 185
- Next state
- Distance to next state
- News family
- Event core band
- Remaining event budget
- Reach zone: HIGH / NORMAL / LOW / TAIL / OUTSIDE
- Event age
- Event status: IMPULSE / ACTIVE / RESIDUE / EXHAUSTED
- Stand-down flag

---

## 9. What V1 Does NOT Claim

- exact daily high or low
- exact number of pips from a release
- news headline direction
- deterministic candle path
- 100% 132/168/185 completion
- family directional skew as a primary signal

V1 predicts **distribution feasibility, branch preference, structural reach, and event-conditioned state transitions**.
