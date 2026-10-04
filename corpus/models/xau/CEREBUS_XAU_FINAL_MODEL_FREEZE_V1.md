# CEREBUS XAU — FINAL MODEL FREEZE V1

**Status:** Research freeze after five passes  
**Asset:** XAUUSD  
**Architecture:** L3 destination/scale → L2 weekly path → L1 execution  
**Core doctrine:** Transfer architecture, not assumptions. Strong state statistics are not automatically entry signals.

---

## 1. Layer contracts

### Layer 3 — Quarter / Month
Primary objects:
- Quarter directional prior
- Quarter scale
- M1/M2/M3 state
- Monthly rekey progression

Must not:
- Micromanage intraday execution
- Treat every strong state as a blind entry

### Layer 2 — Weekly
Primary objects:
- Weekly opportunity
- Weekly side
- Pace
- Range-left
- Delivery clock

Must not:
- Override Layer 3 destination
- Convert state probability directly into a market order

### Layer 1 — Daily
Primary objects:
- Entry timing
- Asian-range state
- Confirmation
- Invalidation

Must not:
- Infer quarter destination independently

---

# 2. Gold Layer 3 — frozen structure

## 2.1 Early M1 information has three separate jobs

### D1-D3 = Month-1 path seed
- D1-D3 → own Month-1 direction: ~75%
- Directional side breaks first after D3: ~72%
- Use for early Month-1 path, not quarter direction.

### D2-D11 = quarterly direction prior
Best stable tested early-M1 direction window:

`D2 open → D11 close`

- Full sample: **60 / 84 = 71.4%**
- Development pre-2019: ~70%
- 2019+ validation: ~74%

Interpretation:
- Gold quarter direction matures across roughly the first two trading weeks.
- D2-D11 is a prior, not a deterministic destination law.

### Full M1 range = quarterly scale anchor
86 complete quarters, 2004 Q3–2025 Q4.

M1 range vs final-quarter range:

`r = 0.842`

Quarter-range / M1-range distribution:
- Q25 = **1.42x**
- Q50 = **1.72x**
- Q75 = **2.23x**
- Q90 = **2.80x**

M2 breaks at least one M1 extreme:
- **74 / 86 = 86.0%**

Unfinished quarter side completing in M3:
- ~**81%**

---

# 3. M1 Seed setup library

## 3.1 M1 Seed Break — PROMOTED

Trigger:
- First H1 close beyond the D1-D3 directional edge.

Primary invalidation:
- D1-D3 **50%** rekey.

Primary target:
- **+0.25x D1-D3**

Research result:
- 61 / 76 = **80.3%** target-before-stop
- Pre-2019: 79.2%
- 2019+: 82.6%

95% Wilson interval approximately 70.0%–87.7%.

Runner:
- +0.50x = **61.8% overall**
- Pre-2019 = 67.9%
- 2019+ = **47.8%**

Freeze decision:
- +0.25x is the primary Seed Break target.
- +0.50x remains a runner, not a frozen default target.

---

## 3.2 M1 Seed Reload — PROMOTED

Sequence:
1. D1-D3 directional break occurs.
2. Price revisits the **25-50%** D1-D3 reload region.
3. H1 recovers through the 25% node in the original seed direction.

Invalidation:
- **68%**

Primary target:
- Return to the D1-D3 directional edge.

Result:
- 46 / 55 = **83.6%**
- Pre-2019 = 82.5%
- 2019+ = 86.7%

Secondary extension:
- +0.25x = 56.4% overall
- 2019+ = 46.7%

Freeze decision:
- Seed edge is the primary target.
- +0.25x is optional runner only.
- Do not blind-limit the 25-50 zone; require recovery.

---

# 4. Full-M1 geometry

Orientation:
- 0% = M1 directional extreme
- 100% = opposite M1 extreme
- Negative = continuation
- Positive = rekey / pullback

Observed M2/M3 reach:
- 25% = **95.3%**
- 50% = **80.2%**
- 68% = **65.1%**
- 80% = **54.7%**
- 100% = **43.0%**
- 110% = 39.5%
- 120% = 34.9%
- 132% = 30.2%
- 168% = 12.8%

Directional extensions:
- -25 = **60.5%**
- -50 = **48.8%**
- -85 = **31.4%**

Interpretation:
- 25-50% = normal macro rotation
- 50-68% = failure developing
- 68%+ = repair / deeper rekey regime

---

# 5. Monthly acceptance ladder

Acceptance = consecutive H1 closes beyond the node.

## 68 + 8h → 80 — PROMOTED
- 42 / 48 = **87.5%**
- Pre-2019 = 90.3%
- 2019+ = 82.4%
- Median MAE ≈ 0.040 M1

Invalidation reference:
- 50%

Target:
- 80%

## 80 + 8h → 100 — SECONDARY
- 27 / 40 = **67.5%**
- Pre-2019 = 62.5%
- 2019+ = 75.0%

Pass-2 duration result:
- 80 + 24h → 100 ≈ **82.9%**

Freeze decision:
- 8h = progression warning
- 24h = stronger 100 promotion
- Do not label 80+8h as an elite setup.

## 100 acceptance — progression state
- 100-110 is a rejection / snap AOI only if price fails acceptance.
- Sustained acceptance beyond 100 shifts interpretation toward deeper rekey progression.

## 120 + 8h → 132 — PRIMARY
- 24 / 25 = **96.0%**
- Pre-2019 = 92.3%
- 2019+ = 100%
- Median MAE ≈ 0.035 M1

Invalidation:
- 100%

Target:
- 132%

## 132 → 168 — PARKED
- 132 + 8h → 168 before recovery was only ~35%.
- 24h acceptance improved to only ~53%.

Freeze decision:
- 132 = deep decision state.
- 168 is not automatically promoted.
- 168 requires additional evidence/context.

---

# 6. M2 role

M2 remains primarily a shaping month.

### M2 Normal Reload
25-50% M1 rekey is a valid **AOI / state**, but the standalone higher-order entry failed promotion.

Test:
- 25-50 visit + recovery through 25
- Stop at 68
- Return to M1 directional edge ≈ **58.8%**
- M1 -25 ≈ **38.2%**

Freeze:
- Keep as L3 context / AOI.
- Require L1 execution.
- Do not display it as an automatic trade trigger.

### M2 Deep Shaping / Deferred Resolution
- 50%+ rekey increases failure / repair relevance.
- 68%+ materially shifts the state toward deeper M3 repair / resolution logic.

---

# 7. M3 setup library

## 7.1 M3 Resolution Continuation — PROMOTED WITH CAUTION

Trigger:
- First H1 acceptance beyond the full M1 directional edge during M3.

Target:
- M1 -25

Aligned with D2-D11 quarter prior:
- 31 / 38 = **81.6%** with 25% stop
- 32 / 38 = **84.2%** with 50% stop

Chronological caution:
- Pre-2019 aligned, 25 stop: 88%
- 2019+ aligned: **69.2%**, N=13

Opposed small-N state:
- 10 / 13 = 76.9% with 25 stop
- 11 / 13 = 84.6% with 50 stop

Freeze decision:
- M3 edge acceptance is a legitimate primary continuation state.
- Do **not** freeze the 84% headline as a permanent probability.
- Display rolling hit rate and N.
- Later confirmed M3 state can override the weaker early-quarter prior.

## 7.2 M3 Unfinished-Side Alignment — RESEARCH-GRADE PRIMARY CONTEXT

When exactly one quarter side is unfinished at halfway and M3 D1-D3 points toward it:
- 38 / 41 = **92.7%** historical completion

When M3 D1-D3 points away:
- 17 / 24 = 70.8%

Freeze:
- Promote as strong context / branch priority.
- Keep explicit N.
- Use L1 to execute; do not blind-enter D3.

---

# 8. Gold Layer 2 — frozen weekly architecture

Core sequence:

`Monday Range Tier → Relative Consumption → Tuesday Pace → Week Location → Range Left → Delivery Clock`

Absolute Monday Range tiers remain useful:
- W-T1 ≤ $18.13
- W-T2 = $18.13–$51.70
- W-T3 > $51.70

State-level continuation after OCC:

### W-T1
- +0.25 MR = 98.1%
- +0.50 MR = 92.6%
- +1.00 MR = 81.5%
- Median favorable excursion = 1.86 MR

### W-T2
- +0.25 MR = 86.4%
- +0.50 MR = 77.3%
- +1.00 MR = 52.7%

### W-T3
- +0.25 MR = 73.2%
- +0.50 MR = 63.4%
- +1.00 MR = 36.6%

---

# 9. Surviving legacy Gold weekly states

## Coiled Spring — KEEP AS STATE
N=34
- +0.50 MR = **94.1%**
- +1.00 MR = **82.4%**

Caution:
- 2025+ contained only one W-T1 Coiled Spring observation in this sample.
- Excellent full-sample state result, insufficient recent independent N.

## Deep Reset — KEEP AS STATE / SMALL-N
N=20
- +0.50 MR = **90.0%**
- +1.00 MR = **80.0%**

Caution:
- Sample is modest and concentrated in development history.

## Standard Breath — KEEP
N=57
- +0.25 MR = **86.0%**
- +0.50 MR = **82.5%**
- +1.00 MR = 54.4%

2025+:
- +0.25 = 91.7%, N=12
- +0.50 = 91.7%, N=12

This is the cleanest recently validated W-T2 legacy state.

## Standard Rekey — SECONDARY / REGIME-SENSITIVE
N=55
- +0.25 MR = 83.6%
- +0.50 MR = 69.1%
- +1.00 MR = 49.1%

2025+ improved sharply:
- +0.50 MR = 90.9%, N=11
- +1.00 MR = 72.7%, N=11

Freeze:
- Retain, but show as secondary / rolling-stat state.
- Do not replace long-history rate with recent small-N rate.

## Exhausted Snap — PARK
Failed to demonstrate a sufficiently strong primary midpoint reversal edge.

W-T3 remains:
- high-consumption
- no-chase
- reversal requires L1 confirmation

---

# 10. Modern Tuesday path state — PROMOTED

Primary Gold weekly decision window:

**Tuesday 12:00–18:00 New York**

Best tested checkpoint near 15:00 NY:

State:
- price in Upper or Lower Third
- pace = UNDER or NORMAL

Result:
- N = 109
- another same-side weekly extreme = **95.4%**
- median remaining directional range ≈ **0.283x** normal week

Chronological:
- 2022-2024 = **93.6%**, N=78
- 2025+ = **100%**, N=31

Subcells:
- Upper + UNDER: 100%, N=12
- Upper + NORMAL: 89.1%, N=46
- Lower + UNDER: 100%, N=15
- Lower + NORMAL: 100%, N=36

Freeze:
- This is a primary L2 path state.
- It is **not** a blind Tuesday entry.
- L1 must supply execution.

Gold-specific pace doctrine:
- Tuesday UNDER frequently catches up.
- UNDER is not equivalent to “slow week.”
- Tuesday OVER is persistent expansion, but remaining opportunity depends strongly on location/regime.

---

# 11. Delivery clock

Final favorable weekly extreme clusters through the second half of the week.

Approximate distribution:
- Tuesday ~17%
- Wednesday ~29%
- Thursday ~18%
- Friday ~32%

UNDER weeks showed especially strong late-week delivery tendency.

Freeze:
- Dashboard should display expected delivery-day context.
- Do not treat a Tuesday state as requiring Tuesday completion.

---

# 12. Entry architecture — final rule

## L3 may contain direct H1 trigger setups
Promoted:
- M1 Seed Break
- M1 Seed Reload
- M3 Resolution Continuation
- 68+8h → 80
- 120+8h → 132

Secondary:
- 80+8h / 24h → 100

Context only:
- M2 Normal Reload
- M3 unfinished-side alignment

Parked:
- automatic 132 → 168

## L2 is primarily an opportunity/path engine
Promoted states:
- Coiled Spring
- Deep Reset
- Standard Breath
- Standard Rekey secondary
- Tuesday directional-third + UNDER/NORMAL continuation

But first OCC close is **not** frozen as the optimal entry.

Blind OCC entry materially reduced target-before-stop rates.

Therefore:

`L2 state → L1 execution`

is a frozen design contract.

---

# 13. Final Gold hierarchy

## L3
`D1-D3 path seed → D2-D11 quarter direction → Full M1 scale → M2 shaping → M3 resolution`

## L2
`MR Tier → Relative State → Tuesday Pace → Location → Range Left → Delivery Clock`

## L1
`Absolute Asian tier × Relative Asian consumption → execution state → confirmed trigger`

---

# 14. Indicator requirements

The final Gold indicator should show independent, toggleable panels.

### L3 panel
- Quarter / M1-M2-M3 position
- D1-D3 path direction
- D2-D11 quarter direction prior
- Full M1 range
- Projected quarter Q25/Q50/Q75/Q90
- Current M1-relative node
- Acceptance duration
- Active L3 setup
- Entry / AOI
- Invalidation reference
- Target
- Research flag / N

### L2 panel
- Monday Range
- W-Tier
- Relative MR state
- Tuesday pace
- Week location
- Range-left
- Active weekly setup/state
- Direction
- Delivery-day context
- Target
- Entry status: "WAIT FOR L1" when execution is not direct

### L1 panel
- Absolute Asian tier
- Relative Asian state
- Active execution setup
- Entry / trigger
- Invalidation
- Target
- No-Go / exhaustion state

### Display contract
- Every major plot family toggleable
- Every level color customizable
- Panels movable independently
- Historical structural maps remain visible
- Active setup geometry must not connect unrelated states
- Rolling rates displayed beside frozen benchmark and N

---

# 15. Scientific freeze status

### Frozen topology
- D1-D3 = M1 path
- D2-D11 = quarter direction
- Full M1 = quarter scale
- M2 = shaping
- M3 = resolution
- Tuesday afternoon = primary Gold L2 path window
- L2 state ≠ direct entry
- 68+8h → 80
- 120+8h → 132
- 132 → 168 not automatic

### Rolling / adaptive
- Exact M3 continuation success rate
- Standard Rekey recent performance
- Upper-vs-lower OVER asymmetry
- Small unfinished-side and deep-rekey subcells

### Parked
- Exhausted Snap as primary L2 setup
- M2 Normal Reload as standalone entry
- Automatic 132→168
- Any monolithic L1/L2/L3 confluence score

**Final doctrine:**  
**L3 defines destination and scale. L2 defines opportunity and path. L1 defines execution.**