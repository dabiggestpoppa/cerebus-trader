# CEREBUS CANONICAL TAXONOMY V1

Status: CANONICALIZATION DRAFT
Date: 2026-10-04
Purpose: define the object classes FORGE may store, retrieve, explain and expose without flattening research, models, evidence and execution into one category.

## Governing chain
OBSERVATION -> MEASUREMENT -> STATE -> TRANSITION -> MODEL -> OPERATOR -> EVIDENCE -> CLAIM.

A visualization, implementation or historical report may represent one or more objects, but is not itself proof.

## Canonical object classes

### 1 OBSERVATION
Raw market occurrence before interpretation.
Examples: candle, range high/low, event release, first close outside a band, target touch.
Required: market, clock, timestamp/session, source/granularity.

### 2 MEASUREMENT
Deterministic transformation of observations.
Examples: Asian range size, body pips, distance-to-node, MAE/MFE, range-left, regime ratio.
Required: formula, units, input frame, clock/session definition.

### 3 SCALE / COORDINATE
Normalized or asset-native coordinate system.
Examples: Tier, AU, 50-72,132/168/185, quarter zones.
Rule: coordinates do not create structure; valid structure/range must exist first.

### 4 EVENT
Discrete occurrence derived from observations/measurements.
Examples: P90, OCC, rekey touch, first delivery, failure, second acceptance, news event.
Required: exact event definition and generation/version.

### 5 STATE
Condition of a system at a time.
Examples: tier state, path state, health state, extension state, failure state.
Rule: state vocabulary is generation-specific; historical single-state ontology and later statistical states must not be silently merged.

### 6 TRANSITION / PATH
Change between states or ordered event sequence.
Examples: valid acceptance -> failure -> midpoint repair -> same-side reacquisition; Alpha->Beta->Gamma->Delta.
Required: conditioning population, order, clock/horizon.

### 7 CLOCK
Temporal coordinate or survival age.
Examples: 6AM/9AM/12PM checkpoints, 58-72h weekly timing, state age, Month1/2/3.
Clock is part of claim identity.

### 8 RANGE / ANCHOR
Earned structural measurement frame.
Examples: Asian range, Monday range, A-B Range Birth, D1-D3 seed.
Rule: anchor eligibility precedes coordinate projection.

### 9 MODEL
A reproducible mapping from inputs/state to distributions, classifications, levels or decisions.
Subtypes:
DISTRIBUTION
PATH
DESTINATION
STATE
REGIME
CROSS-ASSET
EXECUTION-SUPPORT.
A model is not automatically a trade setup.

### 10 SETUP / OPERATOR
Actionable rule set built from model/state/location.
Required: eligibility, entry, invalidation, target, clock, no-go, evidence status.
Subtypes MANUAL_OPERATOR, AUTOMATION_APPROVED, RESEARCH_ONLY.
ST is MANUAL_OPERATOR. Historical broken automation does not alter that classification.

### 11 INDICATOR
User interface/measurement implementation.
It can calculate/display models or states but does not independently validate them.

### 12 EVIDENCE
Empirical support or contradiction.
Types:
RAW_BACKTEST
SCIENTIFIC_RETEST
FORWARD_OOS
LIVE_OPERATOR
HISTORICAL_REPORT
SIMULATION
DERIVED_ALGEBRA
VISUAL_CONSTANT
NEGATIVE_EVIDENCE.
Evidence must identify source, sample, calculation and implementation where relevant.

### 13 CLAIM
A bounded proposition supported by evidence.
Required identity:
market, event_definition, conditioning_event, clock_origin, horizon, tolerance, numerator/denominator, eligibility, period, source generation, calculation type, status.

### 14 DOCTRINE
Cross-model reasoning rule.
Examples: distribution engine not oracle; L3 destination/L2 path/L1 execution; range-left over static target worship; negative evidence first-class.

### 15 LINEAGE
Relationship across generations.
Types:
ANCESTOR_OF
ABSORBED_INTO
RECALIBRATED_AS
SUPERSEDED_BY
FALSIFIED_BY
IMPLEMENTED_AS
VISUALIZED_BY.

### 16 ARTIFACT
Physical source: PDF, MD, Pine, CSV, workbook, infographic, notebook, conversation-derived memo.
Artifacts point to objects; artifacts are not the ontology itself.

## Evidence statuses
OBSERVED
VALIDATED
FORWARD_OOS
CANDIDATE
RESEARCH_FLAG
DESCRIPTIVE
HISTORICAL
PARKED
SUPERSEDED
FALSIFIED
NO_GO
REPRODUCTION_REQUIRED
INTERNAL_CONTRADICTION
IMPLEMENTATION_NOT_PARITY_SAFE.

## Product exposure
PUBLIC_TEACHING
SUBSCRIBER_MODEL
OPERATOR_ONLY
RESEARCH_LAB
INTERNAL_METHOD
INTERNAL_CODE.

## Layer convention
L3 DESTINATION: higher-order available destination/distribution.
L2 PATH: route, state transitions, timing, survival.
L1 EXECUTION: local entry/location/invalidation.
No layer may claim another layer's job merely because they correlate.

## Asset transfer rule
Transfer structural grammar, not calibration constants.
Every asset must earn native tiers, clocks, thresholds and tolerances.

## FORGE rule
Ask CEREBUS retrieves canonical objects first. Raw historical artifacts are supporting provenance and may only override a canonical object through an explicit later canonical decision.
