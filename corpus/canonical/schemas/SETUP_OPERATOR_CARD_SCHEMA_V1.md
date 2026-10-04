# CEREBUS SETUP / OPERATOR CARD SCHEMA V1

setup_id:
name:
version:
status:
market_scope:
execution_class: MANUAL_OPERATOR | AUTOMATION_APPROVED | RESEARCH_ONLY
parent_model_ids:
product_exposure:

## Purpose
What operator decision does this setup support?

## Eligibility
Required state, range/anchor, tier, clock, event and higher-layer context.

## Entry
Exact trigger/location/confirmation. Distinguish touch, excursion, rejection, acceptance and close.

## Invalidation
Exact price/state/time invalidation.

## Targets
Ordered destinations with target identity and promotion conditions.

## No-go / stand-down
Conditions that suppress the setup.

## Layer handoff
L3 destination:
L2 path:
L1 execution:

## Evidence
claim_ids:
evidence_ids:
Do not quote unsupported model-level statistics as setup WR.

## Failure / repair
What failure means and whether repair/re-entry exists.

## Implementation parity
manual_rule_source:
indicator_source:
automation_status:
parity_status:

## Ask CEREBUS behavior
beginner_summary:
operator_instructions:
researcher_notes:
forbidden_overclaims:
