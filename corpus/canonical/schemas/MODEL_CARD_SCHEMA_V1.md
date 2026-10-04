# CEREBUS MODEL CARD SCHEMA V1

model_id:
name:
version:
status:
market_scope:
layer: [L1, L2, L3, CROSS_LAYER]
model_type:
product_exposure:

## Purpose
What question does this model answer?

## Inputs
- observation/measurement IDs
- required ranges/anchors
- clocks
- external/event inputs

## State space
States and exact definitions.

## Outputs
Distribution, path, level, classification or operator context.

## Eligibility / no-go
When the model is valid and when it must stand down.

## Calibration
Asset-native tiers/thresholds/tolerances. Never inherit another market silently.

## Evidence links
evidence_card_ids:

## Known limitations
Failure modes, sample limits, implementation gaps, regime dependence.

## Lineage
ancestor_ids:
descendant_ids:
supersedes:
absorbs:

## Implementation
indicator/code artifacts and parity status.

## Operator interpretation
What a user may do with the output and what the output does NOT mean.

## Ask CEREBUS behavior
beginner_summary:
operator_summary:
researcher_summary:
forbidden_overclaims:
