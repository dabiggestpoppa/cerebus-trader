# CEREBUS EUR Higher-Order Quarter / Month Tracker V1 — Frozen Spec

**Status:** MODEL FROZEN FOR INDICATOR BUILD  
**Primary asset:** EURUSD  
**Purpose:** Higher-order quarter/month distribution tracking. This is not a full Game matrix and does not blend weekly/daily models into one score.

## 1. Architecture

The higher-order engine is intentionally sparse:

1. **Quarter seed** — first 3 trading days provide a directional prior.
2. **Month 1** — establishes the dominant quarterly range seed and fib geometry.
3. **Month 2** — shaping / pullback / rekey month.
4. **Month 3** — resolution / completion month.
5. **Weekly engine** — remains independent and describes local weekly path, not the same target as the monthly engine.
6. **Daily engine** — remains independent and is used later as N/T execution timing.

Do not merge layers unless a separate ablation demonstrates incremental value.

---

## 2. Long-history quarter findings

Long H1 research sample: 59 complete quarters, 2005 Q3–2020 Q1.

- First 3 trading days -> final quarter close direction: **41/59 = 69.5%**.
- Month 1 range vs final quarter range correlation: **r = 0.746**.
- Month 2 breaks at least one Month 1 extreme: **84.7%**.
- Quarter high formed by halfway: **44.1%**.
- Quarter low formed by halfway: **57.6%**.
- If a quarter side remained unfinished by halfway, the unfinished side formed in Month 3: **81.0%**.

Historical final-quarter-range multiple of Month 1 range:
- Q25: **1.42x**
- Q50: **1.64x**
- Q75: **2.26x**
- Q90: **2.83x**

Historical unconditional quarterly range:
- Q25: ~565 pips
- Q50: ~876 pips
- Q75: ~1,111 pips
- Q90: ~1,500 pips

---

## 3. Recent OOS validation

Forward validation slice: 2023 Q1–2026 Q2, 14 completed quarters.

- First 3 trading days -> final quarter direction: **10/14 = 71.4%**.
- First-3-days + Month-1 direction agreement: **6/6 = 100%** (small-N research flag; never display as certainty without N).
- Month 2 breaks at least one Month 1 extreme: **10/14 = 71.4%**.
- Quarter high formed by halfway: **7/14 = 50.0%**.
- Quarter low formed by halfway: **9/14 = 64.3%**.
- Unfinished quarter sides that completed in Month 3: **10/12 = 83.3%**.

Recent OOS final-quarter-range multiple of Month 1 range:
- Q25: ~1.30x
- Q50: ~1.45x
- Q75: ~2.03x
- Q90: ~2.16x

Historical range multipliers therefore remain the structural benchmark, while the indicator must also calculate rolling realized multipliers so the operator sees both long-history and current-regime behavior.

---

## 4. Month 1 geometry

Orient the M1 range by Month 1 direction:

- `0%` = M1 directional extreme.
- `100%` = opposite M1 extreme.
- Negative values = continuation beyond the directional M1 extreme.
- Positive values = pullback / rekey through M1.

### Pullback / rekey ladder

`25 -> 50 -> 68 -> 80 -> 100 -> 110 -> 120 -> 132 -> 168`

Working interpretation:

- **25–50%** = normal higher-order pullback / reload zone.
- **50–68%** = failure developing.
- **68–80%** = deep failure / thesis under pressure.
- **80–100%** = opposite M1 boundary increasingly likely.
- **100–110%** = monthly snap / rekey AOI.
- **110–120%** = last recovery band.
- **120–132%** = deep rekey promoted.
- **132–168%** = deep rekey confirmed.
- **168%+** = outer excursion.

Directional extensions:

`-25 -> -50 -> -85`

Use `-25` as the common first extension, `-50` as secondary, `-85` as outer campaign delivery. Do not treat -85 as a default target.

---

## 5. Temporal acceptance

Monthly rekey state is not defined by a wick alone. Track continuous H1 acceptance / elapsed acceptance time at:

`68, 80, 100, 120, 132`

Reference windows:

`4h -> 8h -> 12h -> 24h`

Observed structural interpretation:

- Sustained acceptance beyond **80%** increasingly promotes delivery to **100%**.
- **100%** is the polarity-flip decision boundary.
- The **100–110%** zone is the strongest early monthly snap/rekey AOI found so far.
- Sustained acceptance beyond **120%** strongly promotes **132%**.
- Sustained acceptance beyond **132%** promotes **168%**.

Exact branch probabilities are not frozen. They remain rolling statistics because many subcells are small.

---

## 6. Month 2 role

Month 2 is primarily a shaping month.

Core observations:

- M1 25% pullback is common.
- M1 50% pullback is still normal higher-order rotation.
- M2 Weeks 1–2 are the main pullback / reload window.
- If M2 is already 50%+ rekeyed early, quarter resolution is more likely to defer to Month 3.

Track M2 live rather than labeling it only after completion.

Required M2 checkpoints:

`D1, D3, D5, D7, D10, D15, D20`

Track at each checkpoint:

- M1-relative normalized close.
- fib/rekey state.
- current M2 range.
- quarter-to-date range.
- distance to M1 directional edge.
- distance to 100% opposite M1 boundary.
- continuation vs repair candidate branch.

---

## 7. Month 3 role

Month 3 is the dominant resolution month.

Long-history endpoint ownership:

- M1 owns final directional quarter extreme: ~16.9%.
- M2 owns it: ~28.8%.
- M3 owns it: ~54.2%.

M3 live branch logic:

- Early M3 acceptance beyond the M1 directional edge = continuation / completion candidate.
- Early M3 close 50%+ into the M1 range = failure / repair candidate.
- 68–80%+ during M3 strongly promotes the opposite M1 boundary as first delivery.
- Recovery back through failed rekey levels can reactivate the continuation branch.

Required M3 checkpoints:

`D1, D3, D5, D7, D10, D15, D20`

The strongest early classification window discovered is **D3–D5**, but exact subcell rates must remain adaptive.

---

## 8. Validation panel doctrine

The indicator must show two statistical angles side-by-side:

1. **Historical/OOS benchmark** — frozen recent OOS rate + sample N for the relevant checkpoint/state cell when available.
2. **Rolling chart rate** — rate computed from the last N completed quarters visible to the indicator.

The panel must never hide small sample size. Always display `rate + N`.

For the first version, fixed OOS checkpoint subcells are available for M3 D3 and D5 state bins. All other checkpoint/state cells are rolling-only until a larger independent OOS table is frozen.

### OOS M3 D3 cell benchmark (M3 owns final directional extreme)

| M1-relative state | Success / N | Rate |
|---|---:|---:|
| <0 | 3/4 | 75.0% |
| 0–25 | 0/1 | 0.0% |
| 25–50 | 1/1 | 100.0% |
| 50–68 | 1/3 | 33.3% |
| 68–80 | 1/1 | 100.0% |
| 80–100 | 1/2 | 50.0% |
| 100–110 | 0/0 | — |
| 110–120 | 1/1 | 100.0% |
| 120–132 | 0/1 | 0.0% |
| 132–168 | 0/0 | — |
| 168+ | 0/0 | — |

### OOS M3 D5 cell benchmark

| M1-relative state | Success / N | Rate |
|---|---:|---:|
| <0 | 3/4 | 75.0% |
| 0–25 | 1/1 | 100.0% |
| 25–50 | 1/2 | 50.0% |
| 50–68 | 0/1 | 0.0% |
| 68–80 | 0/1 | 0.0% |
| 80–100 | 2/2 | 100.0% |
| 100–110 | 0/1 | 0.0% |
| 110–120 | 0/0 | — |
| 120–132 | 1/2 | 50.0% |
| 132–168 | 0/0 | — |
| 168+ | 0/0 | — |

These tiny cells are context, not hard-coded predictions.

---

## 9. Weekly / Daily coupling decision

Ablation result: the frozen weekly engine remains strong on its own weekly target, but did not materially improve monthly destination prediction in the tested overlap sample.

Decision:

- **Do not blend Monthly + Weekly into one score.**
- Monthly/Quarterly owns higher-order destination/regime.
- Weekly owns local weekly path / next weekly extreme.
- Daily owns execution timing / range-left / next structural state.
- Weekly opposition can be used as a patience/veto context, not as proof that the monthly destination is wrong.

This separation is a frozen design doctrine unless future OOS evidence shows incremental lift.

---

## 10. Indicator outputs

Main dashboard:

- Quarter / month position.
- First-3-day direction.
- Month 1 direction and agreement state.
- M1 range.
- Historical Q50/Q75/Q90 quarter projection.
- Rolling Q50/Q75/Q90 quarter projection.
- Current M1-relative normalized state.
- Current fib/rekey zone.
- M2/M3 trading-day checkpoint.
- Active branch candidate.
- First delivery candidate.
- Acceptance duration at 68/80/100/120/132.

Validation dashboard:

- OOS D3 direction rate vs rolling.
- OOS M2 break rate vs rolling.
- Active M3 D3/D5 subcell OOS rate+N vs rolling rate+N.
- Explicit small-N warning where relevant.

Plots:

- M1 directional edge and opposite edge.
- 25/50/68/80/100/110/120/132/168 pullback/rekey levels.
- -25/-50/-85 directional extension levels.
- Independent toggles for levels, dashboard and validation panel.

---

## 11. Freeze decision

**Freeze V1 geometry and state machine.**

Do not freeze exact probabilities for small M2/M3 state cells. Preserve historical/OOS subcells as benchmark evidence and calculate rolling rates live.

The next layer after this indicator is not another higher-order model. It is the existing weekly engine followed by the existing daily engine as separate lower-order context/execution layers.