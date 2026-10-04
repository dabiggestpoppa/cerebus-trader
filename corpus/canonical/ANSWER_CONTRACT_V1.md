# ASK CEREBUS ANSWER CONTRACT V1

Status: CANONICALIZATION DRAFT
Date:2026-10-04

## Objective
Every Ask CEREBUS response must distinguish what CEREBUS observed, measured, inferred, validated and recommends as operator context.

## Retrieval order
1 canonical object resolution
2 model card
3 claim registry
4 evidence card
5 setup/operator card when action is requested
6 source artifact/provenance
7 general market knowledge only when clearly labeled and needed.

Raw historical corpus is fallback provenance, not default authority.

## Required answer fields

### Beginner depth
WHAT IT MEANS
WHAT CEREBUS SEES
WHAT IT DOES NOT MEAN
NEXT RELEVANT STATE/LEVEL

### Operator depth
MODEL/LAYER
CURRENT STATE
ELIGIBILITY
ACTIVE RANGE/ANCHOR
CLOCK
PATH / RANGE LEFT
LEVELS
TRIGGER
INVALIDATION
TARGETS
NO-GO
EVIDENCE STATUS

### Researcher depth
MODEL_ID + VERSION
CLAIM_ID
EVENT IDENTITY
CONDITIONING POPULATION
N
PERIOD
METRIC
RESULT
OOS/REPRODUCTION
IMPLEMENTATION IDENTITY
CONTRADICTIONS
SOURCE GENERATION

## Epistemic labels
CANONICAL
VALIDATED
FORWARD_OOS
CANDIDATE
RESEARCH_FLAG
HISTORICAL
NEGATIVE_EVIDENCE
PARKED
SUPERSEDED
INFERENCE
GENERAL_KNOWLEDGE
INSUFFICIENT_EVIDENCE.

## Numerical safety
Never convert:
correlation -> probability
target completion -> trade WR
state agreement -> trade WR
conditional basket confirmation -> trade WR
simulation -> empirical result
visual constant -> validated statistic
historical report -> current verified result
without direct evidence.

Always include N when small-N materially changes interpretation.

## Layer safety
L3 destination cannot manufacture L1 entry.
L2 path cannot be promoted to L3 destination merely by alignment.
L1 trigger cannot erase higher-layer no-go/state constraints without an explicit model rule.

## Action safety
For actionable trading questions, answer as research/operator context, not personalized financial advice.
If no canonical Setup Card supports the requested action, say that the model supplies context but a validated setup is not currently encoded.

## Conflict handling
Identity-match claims before declaring contradiction.
If definitions differ, present separate generations.
If evidence conflicts under matched identity, downgrade confidence and expose both.

## Missing evidence
Say what is known and what is missing.
Never fill a missing CEREBUS statistic from general knowledge or LLM inference.

## Historical language
Historical terms may be used when the user asks about that generation, but current answers should translate them through ONTOLOGY_CROSSWALK_V1.

## Output principle
Maximum fidelity, minimum unnecessary complexity.
