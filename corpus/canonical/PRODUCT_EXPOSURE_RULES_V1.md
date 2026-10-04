# GLX FORGE PRODUCT EXPOSURE RULES V1

Status: CANONICALIZATION DRAFT

## Exposure classes
PUBLIC_TEACHING
SUBSCRIBER_MODEL
OPERATOR_ONLY
RESEARCH_LAB
INTERNAL_METHOD
INTERNAL_CODE

## Public teaching
May expose concepts, model purpose, high-level lineage, bounded published/recovered evidence and beginner explanations.
Never expose proprietary raw transformation code or unreleased parameters.

## Subscriber model
May expose canonical model state, levels, calibrated public/operator parameters, evidence-backed statistics, confidence/status and historical lineage appropriate to the product.

## Operator only
May expose setup eligibility, triggers, invalidations, targets, no-go logic and operator workflows licensed for that tier.
Manual operator models must be labeled MANUAL_OPERATOR.

## Research lab
May expose candidates, small-N findings, negative evidence and experiments with explicit status.
Research Lab content must not be phrased as production signal logic.

## Internal method
Feature engineering, unreleased transformations, model-construction details, hidden calibration workflow, anti-leakage logic and research machinery remain internal unless explicitly promoted.

## Internal code
Source code, private implementation internals, keys, infrastructure secrets and non-licensed code are never retrieved into normal Ask CEREBUS responses.

## IP doctrine
Access is licensed; underlying CEREBUS research, models, methods, code, names and derivatives remain owner IP subject to final legal review.
Entitlement does not transfer ownership.

## Entitlement rule
Retrieval must filter by exposure class before context reaches the LLM.
Do not retrieve forbidden content and ask the LLM not to quote it; prevent retrieval upstream.

## Evidence rule
A lower subscription tier may receive a summarized evidence statement while higher/research access may inspect claim identity, N, period and provenance.
No tier may receive fabricated certainty.

## Corpus leakage
Rate-limit bulk extraction patterns; cap contiguous artifact reproduction; prefer canonical synthesized objects; log suspicious systematic enumeration; never expose internal code through semantic search.
