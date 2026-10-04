# FORGE RECOVERY PASS 14 — RAW-LAYER AUDIT OF HISTORICAL WORKBOOK

Date: 2026-10-04
Source: cerebus 3 market hoily grail (3).xlsx

## Purpose
Move below summary labels and identify where historical claims are measurements, derived summaries, simulations, or unresolved contradictions.

## 1. 132 claim separates into two different events
Phase 3 Comprehensive explicitly records:
- 132 violation rate: 71.53% versus original 95% claim -> requires revision.
- Rekey rate WHEN 132 was hit: 100% across the historical violation set.

These must never be collapsed.

Event A: probability of reaching/violating 132.
Event B: conditional behavior after a 132 event.

The workbook says all historical 132 events triggered what it called a rekey, but later research changed/retested rekey definitions. Therefore Event B remains HISTORICAL_DEFINITION_DEPENDENT, not a modern 100% law.

## 2. Sample-count inconsistency discovered
One workbook surface says 201/281 132 violations.
Other Phase-3/Phase-4 surfaces describe 195/281 and “195/195” post-132 rekeys.

This is a concrete internal sample-definition discrepancy.

Possible causes include filtering, missing-event eligibility, later revision, or copied summaries.

Status:
SAMPLE_DENOMINATOR_CONFLICT / REQUIRES EVENT-ROW RECONSTRUCTION.

## 3. Q4 claim partially decoded
Seasonal table splits quarter by bullish/bearish bias:
Q4 bullish N30: -25 = 100%, -50 = 96.67%, 132 violation = 66.67%.
Q4 bearish N35: -25 = 100%, -50 = 97.14%, 132 violation = 91.43%.

This gives 65 Q4 observations, matching the Phase-2 Q4 Reconstruction N65.

Therefore the 98.46% “Q4 Reconstruction” figure is likely a derived/combined Q4 metric rather than a standalone raw event rate.

Exact formula still needs cell/formula audit before canonical interpretation.

## 4. “Multi-Timeframe Alignment 100%” remains definition-risk
The summary claim has N281 but current search did not surface a sufficiently precise event definition to prove what constituted alignment, when it was observable, or whether selection was causal.

Status remains:
UNRESOLVED / DEFINITION_AND_CAUSALITY_AUDIT_REQUIRED.

## 5. Asian-session tolerance result recovered
Asian Session Failure Analysis contains 619 sessions:
- +/-0.15 tolerance: 512 correct / 107 failed = 82.71%.
- +/-0.25: 553 / 66 = 89.34%.
- +/-0.50: 600 / 19 = 96.93%.

Critical interpretation:
accuracy rises mechanically as tolerance widens.

Therefore “96.93% Asian accuracy” cannot be compared directly with the narrower-tolerance number without including the tolerance width.

FORGE rule:
Every accuracy metric based on spatial tolerance must store the tolerance in the claim identity.

## 6. Temporal scaling conflict discovered
Different workbook surfaces report different delivery times for the same weekly levels.

Phase 3B historical averages:
- -25 ~24h
- -50 ~39-40h
- -100 ~60h
- -168 ~84h

Phase 4 “15M atomic -> weekly” scaling states:
- -25 24-32 15m candles = 6-8h
- -50 48-64 candles = 12-16h
- 132 56-72 candles = 14-18h

These are not automatically contradictory if one is average time from weekly anchor and the other is an atomic-pattern delivery window, but the reference clock differs.

Status:
CLOCK_ORIGIN_MUST_BE_PART_OF_METRIC.

Never store “-25 delivery time” without start event.

## 7. Atomic-pattern predecessor surfaced
Phase 4 Temporal Delivery Mapping reports:
- 1,857 15M sessions from 2023-2025;
- “Alpha 3-leg” pattern ~72% success;
- objective: map 15M atomic patterns into weekly Fibonacci delivery and cross-session velocity handoffs.

This is a direct predecessor to later Atomic / state-transition research and should be recovered as its own historical branch.

Status:
HISTORICAL_ATOMIC_PREDECESSOR / RAW PATTERN DEFINITION NEEDED.

## 8. Cross-market copying risk strengthened
Cross_Market_Comparison explicitly displays:
EUR -25/-50/... and Oil with the same values.
It also labels Oil “Same framework as EUR/USD,” and repeats identical 132 violation 0.7153 and Wednesday share 0.35.

This makes independent coincidence less plausible and increases the chance of template/value inheritance.

Status upgraded:
LIKELY_SUMMARY_PROPAGATION_OR_SHARED_ASSUMPTION / NOT INDEPENDENT OIL VALIDATION.

Raw Oil sheets must decide.

## 9. ETH source lineage clarified but contradiction remains
ETH_Model_Compilation identifies:
- period 2021-01-04 to 2025-12-18;
- weekly anchor Friday Asian Range;
- Phase-4 PDF 5-Day Model;
- 215-week source;
- -25 100%;
- -50 95.7%;
- -100 86.2%;
- -168 76.3%;
- 132 violation 74.4%.

This establishes where the high figures came from, but does not resolve the lower recalculations found in ETH_Discrepancy_Analysis.

Status:
SOURCE_IDENTIFIED / RESULT_CONTRADICTION_UNRESOLVED.

## 10. Infographic lineage corroboration
Cerebus FX v4 system schematic reproduces workbook-era weekly matrix:
- -25 98.22%;
- -50 96.44%;
- -100 92.17%;
- -168 87.19%;
- 132 invalidation 71.53%;
and “195/195” rekey language.

This proves the visual was generated from this historical workbook generation.

Therefore it should be tagged:
VISUAL_LINEAGE = HISTORICAL_WORKBOOK_PHASE3/4
not current scientific doctrine.

## 11. FORGE schema implications
Claim identity needs more than name/value.

Required fields now include:
- event_definition
- conditioning_event
- clock_origin
- horizon
- tolerance_width
- numerator
- denominator
- eligibility_filter
- market
- data_period
- source_sheet
- source_generation
- calculation_type (raw / derived / simulated / manual)
- modern_disposition

Without these fields, old CEREBUS statistics can look contradictory when they are actually measuring different objects—or look independent when they were copied from the same summary.

## 12. Next pass
Priorities:
- recover the exact 195/201 132 event-row difference;
- inspect Oil raw/derived sheets to test copied-summary suspicion;
- inspect ETH Friday-Asian hit rows against Phase-4 summary;
- recover Alpha 3-leg pattern definition and failure modes;
- locate exact Multi-Timeframe Alignment construction;
- trace Q4 98.46 formula;
- build first machine-readable claim-lineage registry.
