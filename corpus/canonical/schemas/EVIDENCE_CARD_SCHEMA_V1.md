# CEREBUS EVIDENCE CARD SCHEMA V1

evidence_id:
claim_id:
title:
status:
evidence_type:
source_artifact:
source_generation:
market:
data_period:
sample_n:

## Exact claim
Bounded proposition only.

## Event identity
event_definition:
conditioning_event:
clock_origin:
horizon:
tolerance:
eligibility_filter:

## Calculation
numerator:
denominator:
metric:
result:
calculation_type:

## Implementation identity
implementation_name:
version_or_hash:
execution_semantics:
data_granularity:
session_definition:
clock_mode:

## Validation
in_sample:
out_of_sample:
forward_oos:
reproduction_status:

## Contradictions / negative evidence
List identity-matched conflicts separately from merely different implementations.

## Interpretation
What the evidence supports.

## Does not support
Explicit overclaims prohibited by this evidence.

## Product exposure
PUBLIC_TEACHING / SUBSCRIBER_MODEL / OPERATOR_ONLY / RESEARCH_LAB / INTERNAL.
